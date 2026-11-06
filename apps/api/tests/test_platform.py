import pytest
from sqlalchemy import select
from app.db import SessionLocal, Membership, User, Chunk
from app.ingestion import chunk_text, ingest, ENC
from app.security import digest


async def register(client, email="owner@example.test", organization="First org"):
    response = await client.post(
        "/api/auth/register",
        json={
            "email": email,
            "password": "StrongPassword!2026",
            "name": "Test Person",
            "organization": organization,
        },
    )
    assert response.status_code == 201, response.text
    client.headers["x-csrf-token"] = response.json()["csrf"]
    me = (await client.get("/api/auth/me")).json()
    return me["organizations"][0]["id"], me["user"]["id"]


@pytest.mark.asyncio
async def test_registration_cookie_and_password_hash(client):
    org, user = await register(client)
    assert (
        "HttpOnly"
        in (
            await client.post(
                "/api/auth/login",
                json={"email": "owner@example.test", "password": "StrongPassword!2026"},
            )
        ).headers["set-cookie"]
    )
    async with SessionLocal() as db:
        u = await db.get(User, user)
        assert u.password.startswith("$argon2id$")
    assert (
        await client.get("/api/organizations/" + org + "/documents")
    ).status_code == 200


@pytest.mark.asyncio
async def test_unauthenticated_and_csrf(client):
    assert (await client.get("/api/auth/me")).status_code == 401
    org, _ = await register(client)
    client.headers.pop("x-csrf-token")
    assert (
        await client.post(
            "/api/organizations/" + org + "/workspaces", json={"name": "Forbidden"}
        )
    ).status_code == 403


@pytest.mark.asyncio
async def test_session_rotation_and_logout(client):
    await register(client)
    old = client.cookies.get("kf_session")
    refresh = await client.post("/api/auth/refresh")
    assert refresh.status_code == 200
    new = client.cookies.get("kf_session")
    assert old != new
    async with SessionLocal() as db:
        from app.db import Session

        assert await db.get(Session, digest(old)) is None
    client.headers["x-csrf-token"] = refresh.json()["csrf"]
    assert (await client.post("/api/auth/logout")).status_code == 200
    assert (await client.get("/api/auth/me")).status_code == 401


@pytest.mark.asyncio
async def test_cross_tenant_isolation(client):
    org, _ = await register(client)
    doc = await client.post(
        f"/api/organizations/{org}/documents",
        files={
            "file": (
                "secret.md",
                b"Payroll salary private confidential",
                "text/markdown",
            )
        },
    )
    assert doc.status_code == 201
    docid = doc.json()["id"]
    other, _ = await register(client, "other@example.test", "Other org")
    for endpoint in [
        "documents",
        "search?q=salary",
        "conversations",
        "members",
        "analytics",
        "audit",
        "workspaces",
        f"documents/{docid}",
        f"documents/{docid}/download",
    ]:
        assert (
            await client.get(f"/api/organizations/{org}/" + endpoint)
        ).status_code == 404, endpoint
    assert (
        await client.get(f"/api/organizations/{other}/search?q=salary")
    ).json() == []
    assert (
        await client.delete(f"/api/organizations/{other}/documents/{docid}")
    ).status_code == 404


@pytest.mark.asyncio
async def test_upload_ingest_search_chat_and_delete(client):
    org, _ = await register(client)
    root = f"/api/organizations/{org}"
    uploaded = await client.post(
        root + "/documents",
        files={
            "file": (
                "policy.md",
                b"Remote employees may work from home three days per week.",
                "text/markdown",
            )
        },
    )
    assert uploaded.status_code == 201, uploaded.text
    did = uploaded.json()["id"]
    detail = (await client.get(root + "/documents/" + did)).json()
    assert detail["status"] == "ready" and detail["chunks"] > 0
    hits = (await client.get(root + "/search?q=remote")).json()
    assert hits and hits[0]["document_id"] == did
    chat = await client.post(root + "/chat", json={"question": "remote work policy"})
    assert chat.status_code == 200, chat.text
    result = chat.json()
    assert "Extractive mode" in result["content"]
    assert result["citations"][0]["document_id"] == did
    follow = await client.post(
        root + "/chat",
        json={
            "question": "How many days?",
            "conversation_id": result["conversation_id"],
        },
    )
    assert follow.status_code == 200
    history = (
        await client.get(root + "/conversations/" + result["conversation_id"])
    ).json()
    assert len(history) == 4
    assert (
        await client.get(root + "/documents/" + did + "/download")
    ).content.startswith(b"Remote")
    assert (await client.delete(root + "/documents/" + did)).status_code == 200
    assert (await client.get(root + "/search?q=remote")).json() == []
    history = (
        await client.get(root + "/conversations/" + result["conversation_id"])
    ).json()
    assert "hidden" in history[1]["content"]


@pytest.mark.asyncio
async def test_insufficient_evidence(client):
    org, _ = await register(client)
    response = await client.post(
        f"/api/organizations/{org}/chat", json={"question": "What is the revenue?"}
    )
    assert response.status_code == 200
    assert "enough evidence" in response.json()["content"]
    assert response.json()["citations"] == []


@pytest.mark.asyncio
async def test_member_private_filter_and_viewer_read_only(client):
    org, owner = await register(client)
    root = f"/api/organizations/{org}"
    private = await client.post(
        root + "/documents",
        data={"visibility": "private"},
        files={"file": ("private.md", b"secret saffron payroll", "text/markdown")},
    )
    public = await client.post(
        root + "/documents",
        files={"file": ("public.md", b"public onboarding checklist", "text/markdown")},
    )
    other_org, viewer = await register(client, "viewer@example.test")
    async with SessionLocal() as db:
        db.add(Membership(org_id=org, user_id=viewer, role="viewer"))
        await db.commit()
    docs = (await client.get(root + "/documents")).json()
    assert len(docs) == 1 and docs[0]["id"] == public.json()["id"]
    assert (await client.get(root + "/search?q=saffron")).json() == []
    assert (
        await client.get(root + "/documents/" + private.json()["id"] + "/download")
    ).status_code == 404
    assert (
        await client.post(root + "/chat", json={"question": "onboarding"})
    ).status_code == 403
    assert (
        await client.post(root + "/documents", files={"file": ("bad.txt", b"no")})
    ).status_code == 403
    assert (
        await client.post(root + "/workspaces", json={"name": "Nope"})
    ).status_code == 403
    assert (await client.get(root + "/audit")).status_code == 403
    assert (await client.get(root + "/members")).status_code == 403


@pytest.mark.asyncio
async def test_conversation_ownership(client):
    org, _ = await register(client)
    root = f"/api/organizations/{org}"
    chat = (
        await client.post(root + "/chat", json={"question": "unknown topic"})
    ).json()
    _, member = await register(client, "member@example.test")
    async with SessionLocal() as db:
        db.add(Membership(org_id=org, user_id=member, role="admin"))
        await db.commit()
    cid = chat["conversation_id"]
    assert (await client.get(root + "/conversations/" + cid)).status_code == 404
    assert (await client.delete(root + "/conversations/" + cid)).status_code == 404
    assert (
        await client.post(
            root + "/chat", json={"question": "steal it", "conversation_id": cid}
        )
    ).status_code == 404


@pytest.mark.asyncio
async def test_upload_validation(client):
    org, _ = await register(client)
    root = f"/api/organizations/{org}"
    assert (
        await client.post(
            root + "/documents", files={"file": ("evil.html", b"<script/>")}
        )
    ).status_code == 415
    assert (
        await client.post(root + "/documents", files={"file": ("empty.md", b"")})
    ).status_code == 413
    assert (
        await client.post(
            root + "/documents",
            data={"workspace_id": "not-my-workspace"},
            files={"file": ("ok.md", b"hello")},
        )
    ).status_code == 404


@pytest.mark.asyncio
async def test_ingestion_idempotency(client):
    org, _ = await register(client)
    response = await client.post(
        f"/api/organizations/{org}/documents",
        files={"file": ("hello.md", b"hello world knowledge")},
    )
    did = response.json()["id"]
    await ingest(did, org)
    await ingest(did, org)
    async with SessionLocal() as db:
        rows = (await db.scalars(select(Chunk).where(Chunk.document_id == did))).all()
        assert len(rows) == 1


@pytest.mark.asyncio
async def test_password_reset_not_faked(client):
    response = await client.post(
        "/api/auth/forgot-password", json={"email": "unknown@example.test"}
    )
    assert response.status_code == 503


def test_token_chunking():
    content = "alpha beta gamma delta " * 1000
    chunks = list(chunk_text(content, size=128, overlap=16))
    assert len(chunks) > 1
    assert all(len(ENC.encode(c)) <= 128 for c in chunks)
    with pytest.raises(ValueError):
        list(chunk_text("a", size=10, overlap=10))


@pytest.mark.asyncio
async def test_document_permissions_update_revalidates_citations(client):
    org, _ = await register(client)
    root = f"/api/organizations/{org}"
    upload = await client.post(
        root + "/documents",
        files={"file": ("policy.md", b"All employees have a remote work policy.")},
    )
    did = upload.json()["id"]
    owner_cookies = dict(client.cookies)
    owner_csrf = client.headers["x-csrf-token"]
    _, member = await register(client, "coworker@example.test")
    async with SessionLocal() as db:
        db.add(Membership(org_id=org, user_id=member, role="member"))
        await db.commit()
    chat = (
        await client.post(root + "/chat", json={"question": "remote work policy"})
    ).json()
    assert chat["citations"]
    member_cookies = dict(client.cookies)
    member_csrf = client.headers["x-csrf-token"]
    client.cookies.clear()
    client.cookies.update(owner_cookies)
    client.headers["x-csrf-token"] = owner_csrf
    changed = await client.patch(
        root + "/documents/" + did, json={"visibility": "private", "workspace_id": None}
    )
    assert changed.status_code == 200
    client.cookies.clear()
    client.cookies.update(member_cookies)
    client.headers["x-csrf-token"] = member_csrf
    assert (await client.get(root + "/search?q=remote")).json() == []
    history = (
        await client.get(root + "/conversations/" + chat["conversation_id"])
    ).json()
    assert history[1]["citations"] == [] and "hidden" in history[1]["content"]
    assert (
        await client.patch(
            root + "/documents/" + did, json={"visibility": "organization"}
        )
    ).status_code == 403
