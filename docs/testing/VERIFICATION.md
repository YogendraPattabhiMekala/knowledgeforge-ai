# Test methodology
The final execution record and readiness decision are in [docs/VALIDATION.md](../VALIDATION.md). Raw logs, coverage artifacts, traces, browser reports and generated databases are deliberately not tracked or placed in the Git-ready ZIP. Curated synthetic screenshots are in `docs/images`.

- SQLite suite: fast auth, role, access, ingestion and workflow regressions. Two skips explicitly require external services/PostgreSQL.
- PostgreSQL suite: the same contracts, plus actual vector ranking/tenant filtering using deterministic embedding vectors.
- Compose suite: isolated `_test` database, Redis round-trip, S3 object round-trip, and broker→worker→result backend task smoke check.
- `scripts/verify_stack.py`: live user/API acceptance against the real application database, object storage and async worker. Does not drop schema; creates synthetic accounts and cleans up its documents/conversations/workspace.
- LangGraph MockTransport tests: no network credentials or paid generation. Validate success, abstention, citation rejection, upstream failure and embeddings.
- Vitest/RTL: API client contract and modal focus/topmost-Escape behavior, delayed responses across organization switches, and workspace-state cleanup.
- Playwright: seeded demo with actual retrieval and citations, mobile navigation/theme, plus new organization/workspace/upload/access/search flow.

Test fixtures set AI credentials to empty, use a separate database, and refuse destructive external test runs unless the database name ends in `_test`. Browser acceptance uses synthetic content. A passing suite is not a security proof, semantic answer-quality metric, or production load benchmark.
