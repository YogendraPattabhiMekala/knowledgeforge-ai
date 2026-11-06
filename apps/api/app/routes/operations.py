from fastapi import APIRouter, Depends
from sqlalchemy import select, func, text
import structlog
from ..config import settings
from ..db import engine, get_db, Document, Conversation, Audit
from ..security import tenant, require_write, visible_docs

router = APIRouter()
log = structlog.get_logger()


@router.get("/api/health")
async def health(db=Depends(get_db)):
    await db.execute(text("SELECT 1"))
    return {
        "status": "ok",
        "environment": settings.environment,
        "retrieval": (
            "postgres-hybrid" if settings.openai_api_key else "postgres-full-text"
        )
        if engine.dialect.name == "postgresql"
        else "development-keyword",
        "generation": "llm" if settings.openai_api_key else "extractive",
        "email_enabled": bool(settings.smtp_host),
    }


@router.get("/api/organizations/{org_id}/analytics")
async def analytics(org_id: str, member=Depends(tenant), db=Depends(get_db)):
    docs = (
        await db.scalars(select(Document).where(*visible_docs(org_id, member)))
    ).all()
    conv = await db.scalar(
        select(func.count())
        .select_from(Conversation)
        .where(Conversation.org_id == org_id, Conversation.user_id == member.user_id)
    )
    return {
        "documents": len(docs),
        "ready": sum(d.status == "ready" for d in docs),
        "failed": sum(d.status == "failed" for d in docs),
        "processing": sum(d.status in {"queued", "processing"} for d in docs),
        "chunks": sum(d.chunks for d in docs),
        "storage_bytes": sum(d.size for d in docs),
        "conversations": conv,
        "provider_configured": bool(settings.openai_api_key),
        "retrieval": ("hybrid" if settings.openai_api_key else "full-text")
        if engine.dialect.name == "postgresql"
        else "keyword",
    }


@router.get("/api/organizations/{org_id}/audit")
async def activity(org_id: str, member=Depends(tenant), db=Depends(get_db)):
    require_write(member)
    rows = (
        await db.scalars(
            select(Audit)
            .where(Audit.org_id == org_id)
            .order_by(Audit.created_at.desc())
            .limit(100)
        )
    ).all()
    return [
        {
            "id": a.id,
            "action": a.action,
            "detail": a.detail,
            "user_id": a.user_id,
            "created_at": a.created_at,
        }
        for a in rows
    ]
