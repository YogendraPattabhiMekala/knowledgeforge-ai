import io
import zipfile
from datetime import datetime, timezone, timedelta
import pytest
from fastapi import HTTPException
from app.file_validation import validate_upload
from app.middleware import RateLimiter
from app.db import SessionLocal, ActionToken, Session
from app.security import digest
from test_platform import register


@pytest.mark.asyncio
async def test_origin_and_body_bounds(client):
    assert (
        await client.post(
            "/api/auth/login",
            headers={"Origin": "https://evil.example"},
            json={"email": "a@example.test", "password": "not-a-real-password"},
        )
    ).status_code == 403
    response = await client.post(
        "/api/auth/login",
        headers={"Content-Length": str(22 * 1024 * 1024)},
        content=b"{}",
    )
    assert response.status_code == 413
    assert response.headers["x-content-type-options"] == "nosniff"


@pytest.mark.asyncio
async def test_expired_session_rejected(client):
    _, user = await register(client)
    async with SessionLocal() as db:
        session = await db.get(Session, digest(client.cookies.get("kf_session")))
        session.expires = datetime.now(timezone.utc) - timedelta(seconds=1)
        await db.commit()
    assert (await client.get("/api/auth/me")).status_code == 401


@pytest.mark.asyncio
async def test_reset_single_use_revokes_sessions(client):
    _, user = await register(client)
    async with SessionLocal() as db:
        db.add(
            ActionToken(
                token=digest("test-reset"),
                user_id=user,
                kind="reset",
                expires=datetime.now(timezone.utc) + timedelta(minutes=5),
            )
        )
        await db.commit()
    data = {"token": "test-reset", "password": "ReplacementPassword!2026"}
    assert (await client.post("/api/auth/reset-password", json=data)).status_code == 200
    assert (await client.post("/api/auth/reset-password", json=data)).status_code == 400
    assert (await client.get("/api/auth/me")).status_code == 401
    assert (
        await client.post(
            "/api/auth/login",
            json={"email": "owner@example.test", "password": data["password"]},
        )
    ).status_code == 200


@pytest.mark.asyncio
async def test_verification_token_single_use(client):
    _, user = await register(client)
    async with SessionLocal() as db:
        db.add(
            ActionToken(
                token=digest("verify-test"),
                user_id=user,
                kind="verify",
                expires=datetime.now(timezone.utc) + timedelta(minutes=5),
            )
        )
        await db.commit()
    assert (
        await client.post("/api/auth/verify", json={"token": "verify-test"})
    ).status_code == 200
    assert (
        await client.post("/api/auth/verify", json={"token": "verify-test"})
    ).status_code == 400
    assert (await client.get("/api/auth/me")).json()["user"]["verified"] is True


@pytest.mark.asyncio
async def test_limiter_is_bounded_and_expires():
    limiter = RateLimiter()
    assert await limiter.allow("one", maximum=1, now=0)
    assert not await limiter.allow("one", maximum=1, now=1)
    assert await limiter.allow("one", maximum=1, now=61)
    for i in range(4100):
        await limiter.allow(str(i), now=61)
    assert len(limiter.windows) == 4096


@pytest.mark.parametrize(
    "name,data",
    [
        ("fake.pdf", b"not pdf"),
        ("bad.md", b"\x00payload"),
        ("bad.txt", b"\xff\xfe"),
        ("invalid.docx", b"PK00"),
        ("bad\nname.txt", b"hello"),
        ("x" * 256 + ".md", b"hi"),
        ("bad.html", b"<html/>"),
    ],
)
def test_file_mismatch_rejected(name, data):
    with pytest.raises(HTTPException):
        validate_upload(name, data)


def test_docx_bomb_and_traversal_rejected():
    for entry, data in [("word/document.xml", b"0" * 100000), ("../outside", b"evil")]:
        output = io.BytesIO()
        with zipfile.ZipFile(output, "w", compression=zipfile.ZIP_DEFLATED) as z:
            z.writestr("[Content_Types].xml", "<Types/>")
            if entry != "word/document.xml":
                z.writestr("word/document.xml", "<document/>")
            z.writestr(entry, data)
        with pytest.raises(HTTPException):
            validate_upload("unsafe.docx", output.getvalue())


def test_real_docx_accepted():
    from docx import Document

    output = io.BytesIO()
    doc = Document()
    doc.add_paragraph("Valid document")
    doc.save(output)
    assert validate_upload("valid.docx", output.getvalue()) == "valid.docx"


@pytest.mark.parametrize(
    "values",
    [
        {"environment": "prod"},
        {"storage_backend": "s33"},
        {"task_mode": "celeryy"},
        {"s3_server_side_encryption": "unencrypted"},
        {"embedding_dimensions": 1024},
    ],
)
def test_unsafe_or_unsupported_configuration_rejected(values):
    from pydantic import ValidationError
    from app.config import Settings

    with pytest.raises(ValidationError):
        Settings(_env_file=None, **values)


@pytest.mark.asyncio
async def test_streamed_body_limit_without_content_length(client):
    async def body():
        yield b'{"email":"'
        for _ in range(22):
            yield b"x" * (1024 * 1024)
        yield b'"}'

    response = await client.post(
        "/api/auth/login", content=body(), headers={"Content-Type": "application/json"}
    )
    assert response.status_code == 413
    assert response.headers["x-content-type-options"] == "nosniff"


@pytest.mark.asyncio
async def test_smtp_failure_logs_event_only(client, monkeypatch):
    from types import SimpleNamespace
    from app.routes import auth

    events = []

    async def fail_mail(*args):
        raise RuntimeError("sensitive-smtp-response-must-not-be-logged")

    monkeypatch.setattr(auth, "send_action", fail_mail)
    monkeypatch.setattr(auth, "log", SimpleNamespace(error=events.append))
    monkeypatch.setattr(auth.settings, "smtp_host", "synthetic.example.test")
    await register(client)
    response = await client.post(
        "/api/auth/forgot-password", json={"email": "owner@example.test"}
    )
    assert response.status_code == 200
    assert events == ["verification_mail_failed", "reset_mail_failed"]


def test_fixed_dimension_accepts_environment_integer(monkeypatch):
    from app.config import Settings

    monkeypatch.setenv("EMBEDDING_DIMENSIONS", "1536")
    assert Settings(_env_file=None).embedding_dimensions == 1536
