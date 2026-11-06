import asyncio, io, math
from sqlalchemy import select, delete
import tiktoken, httpx
from .db import SessionLocal, Document, Chunk
from . import storage
from .config import settings

ENC = tiktoken.get_encoding("cl100k_base")


def chunk_text(text: str, size=480, overlap=64):
    if not 0 <= overlap < size:
        raise ValueError("Invalid overlap")
    tokens = ENC.encode(text, disallowed_special=())
    for start in range(0, len(tokens), size - overlap):
        yield ENC.decode(tokens[start : start + size])
        if start + size >= len(tokens):
            break


def extract(data, name):
    suffix = name.lower().rsplit(".", 1)[-1]
    if suffix == "pdf":
        from pypdf import PdfReader

        reader = PdfReader(io.BytesIO(data))
        if len(reader.pages) > 500:
            raise ValueError("Maximum 500 pages")
        return [(i + 1, p.extract_text() or "") for i, p in enumerate(reader.pages)]
    if suffix == "docx":
        from docx import Document as Docx

        doc = Docx(io.BytesIO(data))
        return [
            (
                None,
                "\n".join(
                    [p.text for p in doc.paragraphs]
                    + [
                        " | ".join(c.text for c in row.cells)
                        for table in doc.tables
                        for row in table.rows
                    ]
                ),
            )
        ]
    return [(None, data.decode("utf-8"))]


async def embed(texts, *, transport=None):
    if not settings.openai_api_key:
        return [None] * len(texts)
    async with httpx.AsyncClient(timeout=60, transport=transport) as client:
        resp = await client.post(
            settings.openai_base_url + "/embeddings",
            headers={"Authorization": "Bearer " + settings.openai_api_key},
            json={
                "model": settings.embedding_model,
                "input": texts,
                "dimensions": 1536,
            },
        )
        resp.raise_for_status()
        vectors = [
            item["embedding"]
            for item in sorted(resp.json()["data"], key=lambda x: x["index"])
        ]
        if len(vectors) != len(texts) or any(
            len(v) != 1536
            or any(not isinstance(n, (int, float)) or not math.isfinite(n) for n in v)
            for v in vectors
        ):
            raise ValueError("Embedding dimension mismatch")
        return vectors


async def ingest(document_id, org_id):
    async with SessionLocal() as db:
        doc = await db.scalar(
            select(Document)
            .where(Document.id == document_id, Document.org_id == org_id)
            .with_for_update()
        )
        if not doc or doc.status == "ready":
            return
        doc.status = "processing"
        doc.attempts += 1
        await db.commit()
        try:
            pages = await asyncio.to_thread(
                lambda: extract(storage.get(doc.storage_key), doc.name)
            )
            if sum(len(text) for _, text in pages) > 5_000_000:
                raise ValueError("Maximum extracted text length exceeded")
            pieces = [
                (page, part)
                for page, text in pages
                for part in chunk_text(text)
                if part.strip()
            ]
            if not pieces:
                raise ValueError(
                    "No extractable text. Scanned PDFs need OCR, which is not enabled."
                )
            if len(pieces) > 2000:
                raise ValueError("Maximum 2,000 chunks per document")
            vectors = []
            for start in range(0, len(pieces), 64):
                vectors.extend(await embed([p[1] for p in pieces[start : start + 64]]))
            # Lock and re-check after external work; duplicate deliveries cannot duplicate chunks.
            await db.refresh(doc, with_for_update=True)
            if doc.status == "ready":
                return
            await db.execute(
                delete(Chunk).where(Chunk.document_id == doc.id, Chunk.org_id == org_id)
            )
            for i, ((page, text), vector) in enumerate(zip(pieces, vectors)):
                db.add(
                    Chunk(
                        org_id=org_id,
                        document_id=doc.id,
                        ordinal=i,
                        text=text,
                        page=page,
                        embedding=vector,
                    )
                )
            doc.status = "ready"
            doc.chunks = len(pieces)
            doc.error = None
            await db.commit()
        except Exception:
            await db.rollback()
            doc = await db.scalar(
                select(Document)
                .where(Document.id == document_id, Document.org_id == org_id)
                .with_for_update()
            )
            if doc and doc.status != "ready":
                doc.status = "failed"
                doc.error = "Text extraction or provider processing failed. Check worker logs and retry."
                await db.commit()
            import structlog

            structlog.get_logger().error(
                "ingestion_failed", document_id=document_id, org_id=org_id
            )
            raise


async def safe_ingest(document_id, org_id):
    try:
        await ingest(document_id, org_id)
    except Exception:
        pass
