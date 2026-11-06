from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select, func
import structlog
from ..db import get_db, User, Organization, Membership, Workspace, Document
from ..security import current_user, tenant, require_write
from ..schemas import Named, MemberInput, RoleInput
from ..presenters import audit

router = APIRouter()
log = structlog.get_logger()


@router.post("/api/organizations", status_code=201)
async def create_org(data: Named, user=Depends(current_user), db=Depends(get_db)):
    org = Organization(name=data.name)
    db.add(org)
    await db.flush()
    db.add(Membership(org_id=org.id, user_id=user.id, role="owner"))
    await db.commit()
    return {"id": org.id, "name": org.name}


@router.patch("/api/organizations/{org_id}")
async def update_org(
    org_id: str, data: Named, member=Depends(tenant), db=Depends(get_db)
):
    if member.role != "owner":
        raise HTTPException(403, "Owner permission required")
    org = await db.get(Organization, org_id)
    org.name = data.name
    audit(db, member, "organization.updated", data.name)
    await db.commit()
    return {"ok": True}


@router.get("/api/organizations/{org_id}/workspaces")
async def workspaces(org_id: str, member=Depends(tenant), db=Depends(get_db)):
    rows = (await db.scalars(select(Workspace).where(Workspace.org_id == org_id))).all()
    return [{"id": w.id, "name": w.name, "description": w.description} for w in rows]


@router.post("/api/organizations/{org_id}/workspaces", status_code=201)
async def create_workspace(
    org_id: str, data: Named, member=Depends(tenant), db=Depends(get_db)
):
    require_write(member)
    w = Workspace(org_id=org_id, name=data.name, description=data.description)
    db.add(w)
    audit(db, member, "workspace.created", data.name)
    await db.commit()
    return {"id": w.id, "name": w.name, "description": w.description}


@router.delete("/api/organizations/{org_id}/workspaces/{workspace_id}")
async def delete_workspace(
    org_id: str, workspace_id: str, member=Depends(tenant), db=Depends(get_db)
):
    require_write(member)
    w = await db.scalar(
        select(Workspace).where(
            Workspace.id == workspace_id, Workspace.org_id == org_id
        )
    )
    if not w:
        raise HTTPException(404, "Workspace not found")
    count = await db.scalar(
        select(func.count())
        .select_from(Document)
        .where(Document.workspace_id == w.id, Document.org_id == org_id)
    )
    if count:
        raise HTTPException(409, "Remove documents from this workspace first")
    await db.delete(w)
    audit(db, member, "workspace.deleted", w.name)
    await db.commit()
    return {"ok": True}


@router.get("/api/organizations/{org_id}/members")
async def members(org_id: str, member=Depends(tenant), db=Depends(get_db)):
    require_write(member)
    rows = (
        await db.execute(
            select(Membership, User)
            .join(User, User.id == Membership.user_id)
            .where(Membership.org_id == org_id)
        )
    ).all()
    return [
        {"id": m.id, "role": m.role, "name": u.name, "email": u.email} for m, u in rows
    ]


@router.post("/api/organizations/{org_id}/members", status_code=201)
async def add_member(
    org_id: str, data: MemberInput, member=Depends(tenant), db=Depends(get_db)
):
    if member.role != "owner":
        raise HTTPException(403, "Owner permission required")
    user = await db.scalar(select(User).where(User.email == data.email.lower().strip()))
    if not user:
        raise HTTPException(
            404,
            "User must register before joining. Email invitations are not yet available.",
        )
    exists = await db.scalar(
        select(Membership).where(
            Membership.org_id == org_id, Membership.user_id == user.id
        )
    )
    if exists:
        raise HTTPException(409, "Already a member")
    db.add(Membership(org_id=org_id, user_id=user.id, role=data.role))
    audit(db, member, "member.added", user.email)
    await db.commit()
    return {"ok": True}


@router.patch("/api/organizations/{org_id}/members/{membership_id}")
async def change_role(
    org_id: str,
    membership_id: str,
    data: RoleInput,
    member=Depends(tenant),
    db=Depends(get_db),
):
    if member.role != "owner":
        raise HTTPException(403, "Owner permission required")
    target = await db.scalar(
        select(Membership).where(
            Membership.id == membership_id, Membership.org_id == org_id
        )
    )
    if not target:
        raise HTTPException(404, "Member not found")
    if target.role == "owner":
        raise HTTPException(409, "Owner transfer is not supported")
    target.role = data.role
    audit(db, member, "member.role_changed", membership_id)
    await db.commit()
    return {"ok": True}


@router.delete("/api/organizations/{org_id}/members/{membership_id}")
async def remove_member(
    org_id: str, membership_id: str, member=Depends(tenant), db=Depends(get_db)
):
    if member.role != "owner":
        raise HTTPException(403, "Owner permission required")
    target = await db.scalar(
        select(Membership).where(
            Membership.id == membership_id, Membership.org_id == org_id
        )
    )
    if not target:
        raise HTTPException(404, "Member not found")
    if target.role == "owner":
        raise HTTPException(409, "Cannot remove owner")
    await db.delete(target)
    audit(db, member, "member.removed", membership_id)
    await db.commit()
    return {"ok": True}
