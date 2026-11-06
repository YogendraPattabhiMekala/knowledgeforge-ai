import asyncio, hashlib
from ..file_validation import validate_upload
from fastapi import (
    APIRouter,
    Depends,
    HTTPException,
    UploadFile,
    File,
    Form,
    BackgroundTasks,
)
from fastapi.responses import StreamingResponse
from sqlalchemy import select, delete
import structlog
from ..config import settings
from ..db import get_db, uid, Workspace, Document, Chunk
from ..security import tenant, require_write, visible_docs
from .. import storage
from ..ingestion import safe_ingest
from ..schemas import DocumentUpdate
from ..presenters import audit, doc_json

router = APIRouter()
log = structlog.get_logger()


async def get_document(db, org_id, member, document_id):
    doc = await db.scalar(
        select(Document).where(
            Document.id == document_id, *visible_docs(org_id, member)
        )
    )
    if not doc:
        raise HTTPException(404, "Document not found")
    return doc


@router.get("/api/organizations/{org_id}/documents")
async def documents(org_id: str, member=Depends(tenant), db=Depends(get_db)):
    return [
        doc_json(d)
        for d in (
            await db.scalars(
                select(Document)
                .where(*visible_docs(org_id, member))
                .order_by(Document.created_at.desc())
            )
        ).all()
    ]


@router.post("/api/organizations/{org_id}/documents", status_code=201)
async def upload(
    org_id: str,
    background: BackgroundTasks,
    file: UploadFile = File(...),
    workspace_id: str | None = Form(None),
    visibility: str = Form("organization"),
    member=Depends(tenant),
    db=Depends(get_db),
):
    require_write(member)
    if visibility not in {"private", "organization"}:
        raise HTTPException(422, "Invalid visibility")
    data = await file.read(20 * 1024 * 1024 + 1)
    await file.close()
    name = validate_upload(file.filename or "", data)
    if workspace_id:
        w = await db.scalar(
            select(Workspace).where(
                Workspace.org_id == org_id, Workspace.id == workspace_id
            )
        )
        if not w:
            raise HTTPException(404, "Workspace not found")
    doc = Document(
        id=uid(),
        org_id=org_id,
        owner_id=member.user_id,
        workspace_id=workspace_id,
        name=name,
        media_type=file.content_type or "application/octet-stream",
        size=len(data),
        storage_key="",
        checksum=hashlib.sha256(data).hexdigest(),
        visibility=visibility,
    )
    doc.storage_key = org_id + "/" + doc.id
    await asyncio.to_thread(storage.put, doc.storage_key, data)
    db.add(doc)
    audit(db, member, "document.uploaded", name)
    try:
        await db.commit()
    except Exception:
        await db.rollback()
        await asyncio.to_thread(storage.remove, doc.storage_key)
        raise
    if settings.task_mode == "celery":
        from ..tasks import ingestion_task

        try:
            await asyncio.to_thread(ingestion_task.delay, doc.id, org_id)
        except Exception:
            doc.status = "failed"
            doc.error = "Queue unavailable. Retry when worker service is available."
            await db.commit()
    else:
        background.add_task(safe_ingest, doc.id, org_id)
    return doc_json(doc)


@router.get("/api/organizations/{org_id}/documents/{document_id}")
async def document_detail(
    org_id: str, document_id: str, member=Depends(tenant), db=Depends(get_db)
):
    doc = await get_document(db, org_id, member, document_id)
    chunks = (
        await db.scalars(
            select(Chunk)
            .where(Chunk.document_id == doc.id, Chunk.org_id == org_id)
            .order_by(Chunk.ordinal)
            .limit(100)
        )
    ).all()
    return {
        **doc_json(doc),
        "passages": [
            {"id": c.id, "text": c.text, "page": c.page, "ordinal": c.ordinal}
            for c in chunks
        ],
    }


@router.patch("/api/organizations/{org_id}/documents/{document_id}")
async def update_document(
    org_id: str,
    document_id: str,
    data: DocumentUpdate,
    member=Depends(tenant),
    db=Depends(get_db),
):
    require_write(member)
    doc = await get_document(db, org_id, member, document_id)
    if data.workspace_id:
        w = await db.scalar(
            select(Workspace).where(
                Workspace.id == data.workspace_id, Workspace.org_id == org_id
            )
        )
        if not w:
            raise HTTPException(404, "Workspace not found")
    doc.visibility = data.visibility
    doc.workspace_id = data.workspace_id
    audit(db, member, "document.permissions_updated", doc.name)
    await db.commit()
    return doc_json(doc)


@router.get("/api/organizations/{org_id}/documents/{document_id}/download")
async def download(
    org_id: str, document_id: str, member=Depends(tenant), db=Depends(get_db)
):
    import io
    from urllib.parse import quote

    doc = await get_document(db, org_id, member, document_id)
    data = await asyncio.to_thread(storage.get, doc.storage_key)
    return StreamingResponse(
        io.BytesIO(data),
        media_type="application/octet-stream",
        headers={
            "Content-Disposition": "attachment; filename*=UTF-8''" + quote(doc.name)
        },
    )


@router.delete("/api/organizations/{org_id}/documents/{document_id}")
async def delete_document(
    org_id: str, document_id: str, member=Depends(tenant), db=Depends(get_db)
):
    require_write(member)
    doc = await get_document(db, org_id, member, document_id)
    if doc.status in {"queued", "processing"}:
        raise HTTPException(409, "Wait until processing finishes before deleting")
    await asyncio.to_thread(storage.remove, doc.storage_key)
    await db.execute(
        delete(Chunk).where(Chunk.document_id == doc.id, Chunk.org_id == org_id)
    )
    await db.delete(doc)
    audit(db, member, "document.deleted", doc.name)
    await db.commit()
    return {"ok": True}


@router.post("/api/organizations/{org_id}/documents/{document_id}/retry")
async def retry(
    org_id: str,
    document_id: str,
    background: BackgroundTasks,
    member=Depends(tenant),
    db=Depends(get_db),
):
    require_write(member)
    doc = await get_document(db, org_id, member, document_id)
    if doc.status != "failed":
        raise HTTPException(409, "Only failed documents can be retried")
    doc.status = "queued"
    doc.error = None
    await db.commit()
    if settings.task_mode == "celery":
        from ..tasks import ingestion_task

        try:
            await asyncio.to_thread(ingestion_task.delay, doc.id, org_id)
        except Exception:
            doc.status = "failed"
            doc.error = "Queue unavailable. Retry when worker service is available."
            await db.commit()
            raise HTTPException(503, "Queue unavailable") from None
    else:
        background.add_task(safe_ingest, doc.id, org_id)
    return {"ok": True}
