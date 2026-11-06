import asyncio, secrets, smtplib
from datetime import datetime, timezone, timedelta
from email.message import EmailMessage
from fastapi import APIRouter, Depends, HTTPException, Request, Response
from sqlalchemy import select, delete
from sqlalchemy.exc import IntegrityError
import structlog
from ..config import settings
from ..db import get_db, User, Organization, Membership, Session, ActionToken, Workspace
from ..security import (
    current_user,
    new_session,
    hasher,
    verify,
    digest,
    DUMMY_PASSWORD_HASH,
)
from ..schemas import (
    Credentials,
    Registration,
    Named,
    EmailInput,
    ResetInput,
    TokenInput,
)
from ..presenters import user_json

router = APIRouter()
log = structlog.get_logger()


async def send_action(db, user, kind):
    if not settings.smtp_host:
        return
    raw = secrets.token_urlsafe(40)
    db.add(
        ActionToken(
            token=digest(raw),
            user_id=user.id,
            kind=kind,
            expires=datetime.now(timezone.utc) + timedelta(minutes=30),
        )
    )
    await db.commit()
    message = EmailMessage()
    message["Subject"] = "KnowledgeForge: " + kind
    message["From"] = settings.smtp_from
    message["To"] = user.email
    message.set_content(
        f"Open {settings.public_url}/{'reset-password' if kind == 'reset' else 'verify-email'}?token={raw} within 30 minutes."
    )

    def send():
        with smtplib.SMTP(settings.smtp_host, settings.smtp_port, timeout=15) as smtp:
            smtp.starttls()
            if settings.smtp_user:
                smtp.login(settings.smtp_user, settings.smtp_password)
            smtp.send_message(message)

    await asyncio.to_thread(send)


@router.post("/api/auth/register", status_code=201)
async def register(data: Registration, response: Response, db=Depends(get_db)):
    user = User(
        email=data.email.lower().strip(),
        name=data.name.strip(),
        password=await asyncio.to_thread(hasher.hash, data.password),
    )
    db.add(user)
    try:
        await db.flush()
    except IntegrityError:
        await db.rollback()
        raise HTTPException(409, "This email cannot be registered")
    org = Organization(name=data.organization.strip())
    db.add(org)
    await db.flush()
    db.add(Membership(org_id=org.id, user_id=user.id, role="owner"))
    db.add(
        Workspace(
            org_id=org.id, name="General", description="Your team's shared knowledge"
        )
    )
    csrf = await new_session(db, user.id, response)
    await db.commit()
    try:
        await send_action(db, user, "verify")
    except Exception:
        log.error("verification_mail_failed")
    return {"user": user_json(user), "csrf": csrf}


@router.post("/api/auth/login")
async def login(data: Credentials, response: Response, db=Depends(get_db)):
    user = await db.scalar(select(User).where(User.email == data.email.lower().strip()))
    encoded = user.password if user else DUMMY_PASSWORD_HASH
    valid = await asyncio.to_thread(verify, data.password, encoded)
    if not user or not valid:
        raise HTTPException(401, "Invalid email or password")
    csrf = await new_session(db, user.id, response)
    await db.commit()
    return {"user": user_json(user), "csrf": csrf}


@router.get("/api/auth/me")
async def me(request: Request, user=Depends(current_user), db=Depends(get_db)):
    rows = (
        await db.execute(
            select(Organization, Membership.role)
            .join(Membership, Membership.org_id == Organization.id)
            .where(Membership.user_id == user.id)
        )
    ).all()
    return {
        "user": user_json(user),
        "csrf": request.state.session.csrf,
        "organizations": [
            {"id": o.id, "name": o.name, "role": role} for o, role in rows
        ],
    }


@router.post("/api/auth/refresh")
async def refresh(
    request: Request, response: Response, user=Depends(current_user), db=Depends(get_db)
):
    consumed = await db.scalar(
        delete(Session)
        .where(Session.token == request.state.session.token)
        .returning(Session.token)
    )
    if not consumed:
        raise HTTPException(401, "Session already rotated")
    csrf = await new_session(db, user.id, response)
    await db.commit()
    return {"csrf": csrf}


@router.post("/api/auth/logout")
async def logout(
    request: Request, response: Response, user=Depends(current_user), db=Depends(get_db)
):
    await db.delete(request.state.session)
    await db.commit()
    response.delete_cookie("kf_session")
    return {"ok": True}


@router.post("/api/auth/forgot-password")
async def forgot(data: EmailInput, db=Depends(get_db)):
    if not settings.smtp_host:
        raise HTTPException(
            503,
            "Password reset requires a configured mail provider. Contact your administrator.",
        )
    user = await db.scalar(select(User).where(User.email == data.email.lower().strip()))
    if user:
        try:
            await send_action(db, user, "reset")
        except Exception:
            log.error("reset_mail_failed")
    return {"message": "If the account exists, a reset link will be emailed."}


@router.post("/api/auth/reset-password")
async def reset(data: ResetInput, db=Depends(get_db)):
    user_id = await db.scalar(
        delete(ActionToken)
        .where(
            ActionToken.token == digest(data.token),
            ActionToken.kind == "reset",
            ActionToken.expires > datetime.now(timezone.utc),
        )
        .returning(ActionToken.user_id)
    )
    if not user_id:
        raise HTTPException(400, "Invalid or expired link")
    user = await db.get(User, user_id)
    user.password = await asyncio.to_thread(hasher.hash, data.password)
    await db.execute(delete(Session).where(Session.user_id == user.id))
    await db.execute(
        delete(ActionToken).where(
            ActionToken.user_id == user.id, ActionToken.kind == "reset"
        )
    )
    await db.commit()
    return {"ok": True}


@router.post("/api/auth/verify")
async def verify_email(data: TokenInput, db=Depends(get_db)):
    user_id = await db.scalar(
        delete(ActionToken)
        .where(
            ActionToken.token == digest(data.token),
            ActionToken.kind == "verify",
            ActionToken.expires > datetime.now(timezone.utc),
        )
        .returning(ActionToken.user_id)
    )
    if not user_id:
        raise HTTPException(400, "Invalid or expired link")
    user = await db.get(User, user_id)
    user.verified = 1
    await db.commit()
    return {"ok": True}


@router.patch("/api/profile")
async def profile(data: Named, user=Depends(current_user), db=Depends(get_db)):
    user.name = data.name
    await db.commit()
    return user_json(user)
