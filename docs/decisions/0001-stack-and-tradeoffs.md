# ADR 0001 — Preserve a modular monolith and an honest local demo
Accepted; updated in the final review.

Keep FastAPI/SQLAlchemy, PostgreSQL+pgvector, Redis/Celery, S3/MinIO and Next App Router. Avoid Kubernetes or a second vector database. LangGraph explicitly sequences retrieval and generation; no autonomous tool loop is needed.

Python 3.12 is the container/lock resolution target; Python 3.13 is also locally tested. Node 22 is the container/CI target; Node 20.20.2 was the sandbox host. Exact npm versions and resolved Python dependencies are committed. Python lock is a complete version resolution, not a hash-locked supply-chain attestation.

Next 16.4.5/React 19.3.1 retain the existing app. The final review upgraded pydantic-settings, python-multipart, pypdf, pytest, LangGraph (1.2.20) and OTel instrumentation to address scanner-reported advisories, then reran tests against the patched lock. Vitest was upgraded to 4.1.12 after a separate development-dependency audit. No known audit findings is a point-in-time result, not proof of security.

MinIO's old registry images were unavailable. Preserve the architecture by building the version-pinned upstream source and initialize the bucket with boto3, instead of silently substituting mock storage. Build flags bound Go compilation on memory-constrained hosts. MinIO remains AGPL; see THIRD_PARTY.md.

Use opaque revocable server sessions, not JWT access/refresh token pairs. Atomic DELETE RETURNING handles rotation and one-time action-token consumption. Keep CSRF and origin checks server-side. Redis throttling is shared in the Compose stack; the local demo uses a bounded in-memory limiter. Trusted proxy/edge policy remains deployment work.

Keep the no-key mode explicitly extractive. SQLite uses keyword matching; PostgreSQL uses full-text (precise terms, then a safe relaxed fallback if no match). A configured embedding provider adds vector candidates and RRF. Embeddings remain 1536-dimensional and model changes need deliberate re-ingestion. Citation numbers are checked, not semantic entailment.

Refactor by domain routers, screen components, shared dialogs and a typed controller hook without changing workflows. TanStack Query, generated TypeScript clients and further controller decomposition remain optional improvements, not completed features.
