"""Deterministic HTTP transports; no external endpoints, no API charges."""

import json
import httpx
import pytest
from app import rag
from app.config import settings
from app.ingestion import embed

EVIDENCE = [
    {
        "id": "chunk-1",
        "document_id": "doc-1",
        "name": "policy.md",
        "text": "Remote work is allowed three days per week.",
        "page": None,
        "ordinal": 0,
    }
]


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "text,valid",
    [
        ("Remote work is allowed three days per week [1].", True),
        ("A claim [999].", False),
        ("No citation at all.", False),
    ],
)
async def test_langgraph_generate_and_citation_validation(monkeypatch, text, valid):
    called = []

    async def retrieve(*args, **kwargs):
        called.append("retrieve")
        return EVIDENCE

    def handle(request):
        called.append("generate")
        body = json.loads(request.content)
        assert "untrusted" in body["messages"][0]["content"]
        assert "three days" in body["messages"][-1]["content"]
        return httpx.Response(200, json={"choices": [{"message": {"content": text}}]})

    monkeypatch.setattr(rag, "retrieve", retrieve)
    monkeypatch.setattr(settings, "openai_api_key", "test-only-not-a-real-key")
    result = await rag.answer(
        None,
        "org",
        None,
        "Remote work policy?",
        [],
        transport=httpx.MockTransport(handle),
    )
    assert called == ["retrieve", "generate"]
    assert (result["answer"] == text) == valid
    assert result["citations"][0]["document_id"] == "doc-1"


@pytest.mark.asyncio
async def test_langgraph_abstains_without_calling_provider(monkeypatch):
    async def empty(*a, **k):
        return []

    def forbidden(request):
        raise AssertionError("Provider must not be called without evidence")

    monkeypatch.setattr(rag, "retrieve", empty)
    monkeypatch.setattr(settings, "openai_api_key", "test-only")
    result = await rag.answer(
        None, "org", None, "Unanswerable?", [], transport=httpx.MockTransport(forbidden)
    )
    assert result["citations"] == [] and "enough evidence" in result["answer"]


@pytest.mark.asyncio
async def test_langgraph_provider_failure_propagates(monkeypatch):
    async def retrieve(*a, **k):
        return EVIDENCE

    monkeypatch.setattr(rag, "retrieve", retrieve)
    monkeypatch.setattr(settings, "openai_api_key", "test-only")
    with pytest.raises(httpx.HTTPStatusError):
        await rag.answer(
            None,
            "org",
            None,
            "Remote work?",
            [],
            transport=httpx.MockTransport(lambda r: httpx.Response(503)),
        )


@pytest.mark.asyncio
async def test_embeddings_mock_and_dimension_guard(monkeypatch):
    monkeypatch.setattr(settings, "openai_api_key", "test-only")
    vector = [1.0] + [0.0] * 1535
    transport = httpx.MockTransport(
        lambda r: httpx.Response(
            200, json={"data": [{"index": 0, "embedding": vector}]}
        )
    )
    assert (await embed(["policy"], transport=transport))[0] == vector
    invalid = httpx.MockTransport(
        lambda r: httpx.Response(200, json={"data": [{"index": 0, "embedding": [1.0]}]})
    )
    with pytest.raises(ValueError):
        await embed(["policy"], transport=invalid)


@pytest.mark.asyncio
async def test_postgres_semantic_tenant_filter(client, monkeypatch):
    from test_platform import register
    from app.db import SessionLocal, Chunk, Membership, engine
    from sqlalchemy import select

    if engine.dialect.name != "postgresql":
        pytest.skip("Requires PostgreSQL vector extension")
    org, _ = await register(client)
    upload = await client.post(
        f"/api/organizations/{org}/documents",
        files={"file": ("vector.md", b"This passage discusses the sunshine.")},
    )
    other, _ = await register(client, "other-vector@example.test")
    vector = [1.0] + [0.0] * 1535
    async with SessionLocal() as db:
        chunks = (await db.scalars(select(Chunk).where(Chunk.org_id == org))).all()
        for c in chunks:
            c.embedding = vector
        await db.commit()
        member = await db.scalar(select(Membership).where(Membership.org_id == org))
        other_member = await db.scalar(
            select(Membership).where(Membership.org_id == other)
        )
        monkeypatch.setattr(settings, "openai_api_key", "test-only")
        transport = httpx.MockTransport(
            lambda r: httpx.Response(
                200, json={"data": [{"index": 0, "embedding": vector}]}
            )
        )
        assert (
            await rag.retrieve(db, org, member, "unrelatedterm", transport=transport)
        )[0]["document_id"] == upload.json()["id"]
        assert (
            await rag.retrieve(
                db, other, other_member, "unrelatedterm", transport=transport
            )
            == []
        )
        # Even a perfect mock vector score is candidate relevance, not evidence.
        # No /chat/completions response is provided: the gate must abstain first.
        result = await rag.answer(
            db, org, member, "unrelatedterm", [], transport=transport
        )
        assert result["citations"] == []
        assert "No sufficiently relevant information" in result["answer"]
