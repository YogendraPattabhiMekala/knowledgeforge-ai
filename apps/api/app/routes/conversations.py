from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select, delete
import structlog
from ..db import get_db, Document, Conversation, Message
from ..security import tenant, visible_docs
from ..rag import retrieve, answer
from ..schemas import ChatInput
from ..presenters import audit

router = APIRouter()
log = structlog.get_logger()


async def owned_conversation(db, org_id, member, cid):
    c = await db.scalar(
        select(Conversation).where(
            Conversation.id == cid,
            Conversation.org_id == org_id,
            Conversation.user_id == member.user_id,
        )
    )
    if not c:
        raise HTTPException(404, "Conversation not found")
    return c


@router.get("/api/organizations/{org_id}/search")
async def search(org_id: str, q: str, member=Depends(tenant), db=Depends(get_db)):
    if not 2 <= len(q) <= 4000:
        raise HTTPException(422, "Query length must be 2–4000 characters")
    results = await retrieve(db, org_id, member, q)
    audit(db, member, "search.performed")
    await db.commit()
    return results


@router.get("/api/organizations/{org_id}/conversations")
async def conversations(org_id: str, member=Depends(tenant), db=Depends(get_db)):
    rows = (
        await db.scalars(
            select(Conversation)
            .where(
                Conversation.org_id == org_id, Conversation.user_id == member.user_id
            )
            .order_by(Conversation.created_at.desc())
        )
    ).all()
    return [{"id": c.id, "title": c.title, "created_at": c.created_at} for c in rows]


@router.get("/api/organizations/{org_id}/conversations/{conversation_id}")
async def messages(
    org_id: str, conversation_id: str, member=Depends(tenant), db=Depends(get_db)
):
    await owned_conversation(db, org_id, member, conversation_id)
    rows = (
        await db.scalars(
            select(Message)
            .where(Message.conversation_id == conversation_id)
            .order_by(Message.created_at)
        )
    ).all()
    # Revalidate source access rather than leaking historic excerpts after permission changes.
    allowed = set(
        (
            await db.scalars(select(Document.id).where(*visible_docs(org_id, member)))
        ).all()
    )
    output = []
    for m in rows:
        accessible = all(c["document_id"] in allowed for c in m.citations)
        output.append(
            {
                "id": m.id,
                "role": m.role,
                "content": m.content
                if accessible
                else "This answer is hidden because access to a cited source has changed.",
                "citations": m.citations if accessible else [],
                "created_at": m.created_at,
            }
        )
    return output


@router.delete("/api/organizations/{org_id}/conversations/{conversation_id}")
async def delete_conversation(
    org_id: str, conversation_id: str, member=Depends(tenant), db=Depends(get_db)
):
    c = await owned_conversation(db, org_id, member, conversation_id)
    await db.execute(delete(Message).where(Message.conversation_id == c.id))
    await db.delete(c)
    await db.commit()
    return {"ok": True}


@router.post("/api/organizations/{org_id}/chat")
async def chat(
    org_id: str, data: ChatInput, member=Depends(tenant), db=Depends(get_db)
):
    if member.role == "viewer":
        raise HTTPException(403, "Viewers can search but cannot create conversations")
    if data.conversation_id:
        c = await owned_conversation(db, org_id, member, data.conversation_id)
    else:
        c = Conversation(
            org_id=org_id, user_id=member.user_id, title=data.question[:100]
        )
        db.add(c)
        await db.flush()
    previous = await messages(org_id, c.id, member, db)
    history = [{"role": m["role"], "content": m["content"]} for m in previous[-8:]]
    try:
        result = await answer(db, org_id, member, data.question, history)
    except Exception:
        log.error("generation_failed", org_id=org_id)
        raise HTTPException(
            502, "AI provider or retrieval failed. No answer was saved. Please retry."
        )
    cited_ids = {item["document_id"] for item in result["citations"]}
    if cited_ids:
        accessible = set(
            (
                await db.scalars(
                    select(Document.id).where(
                        *visible_docs(org_id, member), Document.id.in_(cited_ids)
                    )
                )
            ).all()
        )
        if accessible != cited_ids:
            raise HTTPException(
                409, "Source access changed while answering. Please retry."
            )
    db.add(
        Message(conversation_id=c.id, role="user", content=data.question, citations=[])
    )
    response = Message(
        conversation_id=c.id,
        role="assistant",
        content=result["answer"],
        citations=result["citations"],
    )
    db.add(response)
    audit(db, member, "answer.created", c.id)
    await db.commit()
    return {
        "conversation_id": c.id,
        "content": response.content,
        "citations": response.citations,
    }
