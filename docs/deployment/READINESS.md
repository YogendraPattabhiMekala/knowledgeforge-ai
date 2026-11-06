# Deployment readiness
**Decision: suitable for a clearly labeled public portfolio/source release after review checks; NOT ready for public production service.** See `docs/VALIDATION.md` for evidence and exact scope.

## Verified in final review
- [x] Docker image builds and full local PostgreSQL/pgvector, Redis, MinIO, FastAPI, Celery and Next stack startup.
- [x] PostgreSQL migrations, extension and FTS/HNSW indexes; disposable test DB isolated from app DB.
- [x] Real queue/object-storage/user acceptance and full-stack browser tests.
- [x] Deterministic LangGraph/provider mocks and vector isolation tests; no paid provider call.
- [x] Candidate-file secret/artifact scan, dependency audits, workflow static validation.
- [x] Removal of SQLite data/uploads/test outputs from release; source ZIP allowlist and checksums.

## Still required before hosting for untrusted users
- [ ] Independent security review, accessibility audit, load tests and recovery exercises.
- [ ] Real provider and SMTP delivery verification (with explicit budget/privacy approval).
- [ ] TLS, deployment-specific trusted origin/proxy policy, edge quotas/rate limiting and private networking.
- [ ] File parser isolation, malware scanning, broader parser resource limits and encrypted/scanned PDF policy.
- [ ] Durable ingestion outbox/stale-job recovery, deletion reconciliation and terminal-job operations.
- [ ] Database RLS or further repository-layer defense in depth; immutable external audit sink.
- [ ] Secrets/IAM/bucket lifecycle policies, backup/restore, retention and data purge.
- [ ] Nonce-based CSP (current compatibility CSP permits inline scripts/styles).
- [ ] OTel exporter/collector, full worker/DB tracing, alerts and tested operational runbooks.
- [ ] Human/provider citation-entailment evaluations and prompt-injection threat testing.

Optional product work (not a release claim): nested collections/workspace ACLs, document versioning/OCR, SSO/MFA, invitations/owner transfer, streaming, historical/token-cost analytics, generated TS API client, and an actual AWS Terraform deployment.
