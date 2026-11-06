"""Explicit synthetic development fixture; forbidden in production."""

import asyncio, hashlib
from sqlalchemy import select, text
from .db import *
from .security import hasher
from . import storage
from .ingestion import ingest
from .config import settings

SOURCES = [
    (
        "Company handbook.md",
        "People & Culture",
        "Our guide to doing good work, together.",
        """# Company handbook — SYNTHETIC DEMO
## Remote work policy
Employees may work remotely up to three days per week. Teams coordinate two shared collaboration days with their manager. Fully remote arrangements require written approval from a department lead. Employees should keep calendars current and be reachable from 10 am to 3 pm in their local time zone.
## Time off
Full-time employees receive 25 days of paid time off annually in addition to public holidays. Submit requests at least two weeks before planned leave. Managers approve coverage. Unused days carry over up to a maximum of five days.
## Learning
Employees have an annual learning budget of $1,500. Discuss goals with your manager before booking a course. Reimbursement requires a receipt and a learning summary.
This is synthetic data, not real company policy.""",
    ),
    (
        "Engineering playbook.md",
        "Engineering",
        "Technical practices, systems, and the way we build.",
        """# Engineering playbook — SYNTHETIC DEMO
## Deploying a new release
Create a pull request with a description and test evidence. One engineer outside the author must approve it. CI runs unit, integration, and dependency checks. Merging to main deploys to staging. A release captain checks staging smoke tests then approves production promotion. Deployments use a rolling strategy. Monitor error rates and latency for 30 minutes. If errors increase, roll back to the previous release image.
## Incident response
Open an incident channel and assign an incident commander. Share a customer-impact statement within 15 minutes. Prioritize mitigation. A blameless review is due within three business days.
## Code review
Prefer small focused changes. Include migration rollback steps for database changes. Never commit secrets or customer data. Every endpoint needs an authorization test.""",
    ),
    (
        "Product strategy — Q4.md",
        "Product & Strategy",
        "Research, direction, and decisions that shape our product.",
        """# Q4 product strategy — SYNTHETIC DEMO
Our first priority is reliable source-grounded answers. Our second priority is reducing ingestion failures. Our third priority is improving team onboarding so new members find their first useful answer quickly.
Evaluate answer quality with a curated question set and inspect citations manually. We have no published accuracy benchmark. Avoid introducing new providers until retrieval evaluation is stable.
Customer interviews suggest users value knowing where an answer came from more than receiving a longer answer. Citation clarity and permission correctness are release gates.""",
    ),
    (
        "Information security policy.txt",
        "Engineering",
        "",
        """Information security policy — SYNTHETIC DEMO
Report suspected security incidents immediately to security@example.test and notify the on-call lead through the incident channel. Include time, affected systems, and a short description. Do not copy sensitive data into the report. Preserve logs and avoid deleting evidence. The security lead coordinates containment and notifications.
Use least privilege and multi-factor authentication for production services. Review access quarterly. Revoke access when a member leaves. Store credentials in a managed secrets system.
Classify internal documents before sharing. Never upload regulated or customer-confidential data into demonstration environments.""",
    ),
    (
        "New starter checklist.md",
        "People & Culture",
        "",
        """# New starter checklist — SYNTHETIC DEMO
Before day one: confirm your start date, shipping address, and equipment needs with People Operations.
Day one: activate your account, configure multi-factor authentication, and meet your onboarding buddy. Read the company handbook and information security policy.
Week one: attend introductions, set up your development environment, and agree your first project with your manager.
First month: schedule feedback with your manager and suggest one onboarding improvement.""",
    ),
]


async def main():
    if settings.environment == "production":
        raise RuntimeError("Demo seed forbidden in production")
    async with engine.begin() as c:
        if engine.dialect.name == "postgresql":
            await c.execute(text("CREATE EXTENSION IF NOT EXISTS vector"))
        await c.run_sync(Base.metadata.create_all)
    async with SessionLocal() as db:
        if await db.scalar(
            select(User).where(User.email == "alex@demo.knowledgeforge.local")
        ):
            return
        user = User(
            name="Alex Morgan",
            email="alex@demo.knowledgeforge.local",
            password=hasher.hash("DemoWorkspace!2026"),
        )
        db.add(user)
        await db.flush()
        org = Organization(name="Acme Demo")
        db.add(org)
        await db.flush()
        db.add(Membership(org_id=org.id, user_id=user.id, role="owner"))
        spaces = {}
        ids = []
        for name, space, description, content in SOURCES:
            if space not in spaces:
                w = Workspace(org_id=org.id, name=space, description=description)
                db.add(w)
                await db.flush()
                spaces[space] = w.id
            data = content.encode()
            doc = Document(
                id=uid(),
                org_id=org.id,
                workspace_id=spaces[space],
                owner_id=user.id,
                name=name,
                media_type="text/plain",
                size=len(data),
                storage_key="",
                checksum=hashlib.sha256(data).hexdigest(),
            )
            doc.storage_key = org.id + "/" + doc.id
            storage.put(doc.storage_key, data)
            db.add(doc)
            ids.append(doc.id)
            db.add(
                Audit(
                    org_id=org.id,
                    user_id=user.id,
                    action="document.seeded",
                    detail=name + " (synthetic)",
                )
            )
        await db.commit()
    for doc_id in ids:
        await ingest(doc_id, org.id)
    print("Seeded synthetic demo. alex@demo.knowledgeforge.local / DemoWorkspace!2026")


if __name__ == "__main__":
    asyncio.run(main())
