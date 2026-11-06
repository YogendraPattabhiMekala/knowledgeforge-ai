import hashlib, secrets
from datetime import datetime, timezone, timedelta
from fastapi import Depends, HTTPException, Request
from sqlalchemy import select, or_
from argon2 import PasswordHasher
from argon2.exceptions import VerificationError, InvalidHashError
from .db import get_db, Session, User, Membership, Document

hasher = PasswordHasher()
DUMMY_PASSWORD_HASH = hasher.hash("timing-safe-dummy-password")


def digest(value: str):
    return hashlib.sha256(value.encode()).hexdigest()


def verify(password, encoded):
    try:
        return hasher.verify(encoded, password)
    except (VerificationError, InvalidHashError):
        return False


def utc(value):
    return value.replace(tzinfo=timezone.utc) if value.tzinfo is None else value


async def current_user(request: Request, db=Depends(get_db)):
    raw = request.cookies.get("kf_session", "")
    session = await db.get(Session, digest(raw))
    if not session or utc(session.expires) < datetime.now(timezone.utc):
        raise HTTPException(401, "Sign in to continue")
    if request.method not in {"GET", "HEAD", "OPTIONS"}:
        if not secrets.compare_digest(
            request.headers.get("x-csrf-token", ""), session.csrf
        ):
            raise HTTPException(403, "CSRF validation failed")
    request.state.session = session
    user = await db.get(User, session.user_id)
    if not user:
        raise HTTPException(401, "Sign in to continue")
    return user


async def tenant(org_id: str, user=Depends(current_user), db=Depends(get_db)):
    member = await db.scalar(
        select(Membership).where(
            Membership.org_id == org_id, Membership.user_id == user.id
        )
    )
    if not member:
        raise HTTPException(404, "Organization not found")
    return member


def require_write(member):
    if member.role not in {"owner", "admin"}:
        raise HTTPException(403, "Administrator permission required")


def visible_docs(org_id, member):
    clauses = [Document.org_id == org_id]
    if member.role not in {"owner", "admin"}:
        clauses.append(
            or_(
                Document.visibility == "organization",
                Document.owner_id == member.user_id,
            )
        )
    return clauses


async def new_session(db, user_id, response):
    from .config import settings

    raw, csrf = secrets.token_urlsafe(48), secrets.token_urlsafe(32)
    db.add(
        Session(
            token=digest(raw),
            user_id=user_id,
            csrf=csrf,
            expires=datetime.now(timezone.utc) + timedelta(hours=8),
        )
    )
    response.set_cookie(
        "kf_session",
        raw,
        httponly=True,
        secure=settings.secure_cookies,
        samesite="lax",
        max_age=28800,
        path="/",
    )
    return csrf
