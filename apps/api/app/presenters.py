from .db import Audit


def audit(db, member, action, detail=""):
    db.add(
        Audit(
            org_id=member.org_id, user_id=member.user_id, action=action, detail=detail
        )
    )


def user_json(user):
    return {
        "id": user.id,
        "name": user.name,
        "email": user.email,
        "verified": bool(user.verified),
    }


def doc_json(d):
    return {
        "id": d.id,
        "name": d.name,
        "status": d.status,
        "size": d.size,
        "created_at": d.created_at,
        "chunks": d.chunks,
        "visibility": d.visibility,
        "workspace_id": d.workspace_id,
        "error": d.error,
        "attempts": d.attempts,
    }
