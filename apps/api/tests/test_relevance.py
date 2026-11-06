"""Evidence sufficiency regressions: no special-case topics or paid providers."""

import httpx
import pytest
from app import rag
from app.config import settings
from app.db import Membership, SessionLocal
from app.relevance import assess
from app.seed import SOURCES
from test_platform import register


@pytest.mark.parametrize(
    "question,passage,accepted",
    [
        (
            "What is our remote work policy?",
            "Employees may work remotely. Remote work is permitted three days per week.",
            True,
        ),
        (
            "How should I report security incidents?",
            "Report suspected security incidents immediately to the security lead.",
            True,
        ),
        (
            "What is the relocation allowance in 2035?",
            "The relocation allowance in 2035 is $500.",
            True,
        ),
        (
            "What is the company's official policy for employees relocating to Mars in 2035?",
            SOURCES[0][3],
            False,
        ),
        ("What is our lunar relocation policy in 2041?", SOURCES[0][3], False),
        ("What remote work policy applies to Neptune residents?", SOURCES[0][3], False),
        ("What remote work policy applies in 2035?", SOURCES[0][3], False),
        (
            "What is the relocation allowance in 2035?",
            "The relocation allowance in 20350 is $500.",
            False,
        ),
        ("Explain quantum crop insurance", SOURCES[3][3], False),
        ("What is the official company policy?", SOURCES[0][3], False),
        (
            'What is the "interplanetary relocation" policy?',
            "Relocation requests are reviewed by managers.",
            False,
        ),
        ('Explain "remote work"', "Remote work is allowed three days per week.", True),
    ],
)
def test_explainable_gate(question, passage, accepted):
    result = assess(question, passage)
    assert result["accepted"] is accepted
    assert 0 <= result["coverage"] <= 1


def test_threshold_is_configurable(monkeypatch):
    query = "Explain remote work approval"
    text = "Remote work is permitted."
    assert not assess(query, text)["accepted"]
    monkeypatch.setattr(settings, "relevance_min_coverage", 0.6)
    assert assess(query, text)["accepted"]
    monkeypatch.setattr(settings, "relevance_min_matches", 3)
    assert not assess(query, text)["accepted"]


@pytest.mark.asyncio
@pytest.mark.parametrize("provider", [False, True])
async def test_graph_abstains_before_generation_on_weak_evidence(monkeypatch, provider):
    async def candidates(*args, **kwargs):
        return [
            {
                "text": text,
                "id": str(i),
                "document_id": str(i),
                "name": name,
                "page": None,
                "ordinal": 0,
            }
            for i, (name, _, _, text) in enumerate(SOURCES)
        ]

    def forbidden(request):
        raise AssertionError("Weak evidence must not trigger generation")

    monkeypatch.setattr(rag, "retrieve", candidates)
    monkeypatch.setattr(settings, "openai_api_key", "test-only" if provider else "")
    # Previous history must not make an unrelated current question answerable.
    result = await rag.answer(
        None,
        "org",
        None,
        "What about lunar crop insurance?",
        [{"role": "user", "content": "What is our remote work policy?"}],
        transport=httpx.MockTransport(forbidden),
    )
    assert "No sufficiently relevant information" in result["answer"]
    assert result["citations"] == []


@pytest.mark.asyncio
async def test_each_passage_must_be_relevant_and_citations_exact(monkeypatch):
    async def candidates(*args, **kwargs):
        assert kwargs["limit"] == 30
        return [
            {
                "id": str(i),
                "document_id": f"doc-{i}",
                "name": f"source-{i}.md",
                "text": ("Unrelated employee policy. " * 60 if i == 0 else "")
                + "Remote work requires approval.",
                "page": i + 1,
                "ordinal": i,
            }
            for i in range(6)
        ]

    monkeypatch.setattr(rag, "retrieve", candidates)
    result = await rag.answer(
        None, "org", None, "What approval is required for remote work?", []
    )
    assert len(result["citations"]) == 3
    for i, citation in enumerate(result["citations"], 1):
        assert citation["number"] == i
        assert citation["text"] in result["answer"]
        assert citation["document_id"] == f"doc-{i - 1}"
        assert citation["page"] == i
    assert "[4]" not in result["answer"]


@pytest.mark.asyncio
async def test_partial_matches_are_not_pooled(monkeypatch):
    async def candidates(*args, **kwargs):
        return [{"text": "Remote work."}, {"text": "Relocation to Neptune in 2035."}]

    monkeypatch.setattr(rag, "retrieve", candidates)
    result = await rag.answer(
        None, "org", None, "Remote work relocation to Neptune in 2035", []
    )
    assert result["citations"] == []


@pytest.mark.asyncio
async def test_actual_seeded_sources_relevance_and_citations(client):
    org, _ = await register(client)
    root = f"/api/organizations/{org}"
    ids = {}
    for name, _, _, text in SOURCES:
        response = await client.post(
            root + "/documents", files={"file": (name, text.encode())}
        )
        assert response.status_code == 201
        ids[name] = response.json()["id"]
    for query, name in [
        ("What is our remote work policy?", "Company handbook.md"),
        ("How should we report security incidents?", "Information security policy.txt"),
        ("How do we deploy a new release?", "Engineering playbook.md"),
        ("What is our incident response process?", "Engineering playbook.md"),
        ("What is our annual learning budget?", "Company handbook.md"),
        ("How many paid time off days do I get?", "Company handbook.md"),
    ]:
        response = await client.post(root + "/chat", json={"question": query})
        assert response.status_code == 200
        data = response.json()
        assert "Extractive mode" in data["content"]
        assert {c["document_id"] for c in data["citations"]} == {ids[name]}
        for citation in data["citations"]:
            detail = (
                await client.get(root + "/documents/" + citation["document_id"])
            ).json()
            assert any(
                p["text"] == citation["text"] and p["id"] == citation["id"]
                for p in detail["passages"]
            )
    for query in [
        "What is the company's official policy for employees relocating to Mars in 2035?",
        "What remote work policy applies to Neptune residents?",
        "How are quantum crop insurance claims settled?",
    ]:
        response = await client.post(root + "/chat", json={"question": query})
        assert response.status_code == 200
        assert response.json()["citations"] == []
        assert "No sufficiently relevant information" in response.json()["content"]


@pytest.mark.asyncio
async def test_gate_respects_authorized_sources(client):
    org, _ = await register(client)
    root = f"/api/organizations/{org}"
    private = await client.post(
        root + "/documents",
        data={"visibility": "private"},
        files={
            "file": (
                "restricted.md",
                b"Mercury launch approval is restricted to executives.",
            )
        },
    )
    assert private.status_code == 201
    public = await client.post(
        root + "/documents",
        files={"file": ("shared.md", b"Remote work is permitted three days per week.")},
    )
    assert public.status_code == 201
    response = await client.post(
        root + "/chat", json={"question": "What is Mercury launch approval?"}
    )
    assert response.json()["citations"][0]["document_id"] == private.json()["id"]
    other, uid = await register(client, "relevance-outsider@example.test")
    assert (
        await client.post(root + "/chat", json={"question": "Mercury launch approval?"})
    ).status_code == 404
    own = await client.post(
        f"/api/organizations/{other}/chat",
        json={"question": "Mercury launch approval?"},
    )
    assert own.json()["citations"] == []
    async with SessionLocal() as db:
        db.add(Membership(org_id=org, user_id=uid, role="member"))
        await db.commit()
    denied = await client.post(
        root + "/chat", json={"question": "Mercury launch approval?"}
    )
    assert denied.json()["citations"] == []
    allowed = await client.post(
        root + "/chat", json={"question": "What is our remote work policy?"}
    )
    assert {c["document_id"] for c in allowed.json()["citations"]} == {
        public.json()["id"]
    }


@pytest.mark.asyncio
async def test_llm_only_receives_admitted_evidence(monkeypatch):
    async def candidates(*args, **kwargs):
        return [
            {"text": "Unrelated handbook noiseBeta", "document_id": "noise"},
            {
                "id": "chunk-good",
                "document_id": "good",
                "name": "work.md",
                "page": 2,
                "ordinal": 0,
                "text": "Remote work needs approval.",
            },
        ]

    def provider(request):
        import json

        body = json.loads(request.content)
        assert "noiseBeta" not in body["messages"][-1]["content"]
        assert "[1] Remote work needs approval." in body["messages"][-1]["content"]
        return httpx.Response(
            200,
            json={
                "choices": [{"message": {"content": "Remote work needs approval [1]."}}]
            },
        )

    monkeypatch.setattr(rag, "retrieve", candidates)
    monkeypatch.setattr(settings, "openai_api_key", "test-only")
    result = await rag.answer(
        None,
        "org",
        None,
        "What approval is required for remote work?",
        [],
        transport=httpx.MockTransport(provider),
    )
    assert result["answer"] == "Remote work needs approval [1]."
    assert [(c["document_id"], c["number"]) for c in result["citations"]] == [
        ("good", 1)
    ]


def test_numeric_only_query_has_no_topic():
    assert not assess("What about 2035?", "Security review in 2035.")["accepted"]
    # Numeric overlap cannot dominate coverage without any matched topic.
    years = "2031 2032 2033 2034 2035 2036 2037 2038 2039"
    assert not assess("Explain relocation in " + years, "Calendar: " + years)[
        "accepted"
    ]


@pytest.mark.asyncio
async def test_brief_followup_retains_topic_not_unrelated_day_matches(monkeypatch):
    async def candidates(*args, **kwargs):
        return [
            {
                "id": "work",
                "document_id": "work",
                "name": "work.md",
                "page": None,
                "ordinal": 0,
                "text": "Remote work is allowed three days per week.",
            },
            {
                "id": "starter",
                "document_id": "starter",
                "name": "starter.md",
                "page": None,
                "ordinal": 0,
                "text": "Day one: activate your account.",
            },
        ]

    monkeypatch.setattr(rag, "retrieve", candidates)
    result = await rag.answer(
        None,
        "org",
        None,
        "How many days?",
        [{"role": "user", "content": "What is our remote work policy?"}],
    )
    assert {c["document_id"] for c in result["citations"]} == {"work"}
