# Final validation and portfolio release review

> Historical portfolio baseline. The later answer-relevance fix and its separate executed results are recorded in [RELEVANCE.md](testing/RELEVANCE.md). Do not interpret the full Compose results below as a fresh run of that patch.

**Review date:** 2026-11-05
**Decision:** **GO for a public GitHub portfolio/source release, with the documented limitations. NO-GO for public production hosting.**
**Scope:** existing architecture and working features preserved; targeted security/correctness fixes, refactoring, cleanup, and real local verification. No push, deployment, cloud resource creation, paid LLM invocation, or certification claim.

## Fresh recheck scope

This report includes the initial implementation audit and a new verification of the current release. The fresh run used local Python **3.13.16** / Node **20.20.2** and container Python **3.12.13** / Node **22.22.1**, installed from the existing locks. Its logs were retained outside the repository under `validation/recheck`. Docker resources were recreated, not inferred from the earlier report. No approved provider credentials were present, so paid generation remained disabled.

Additional defects found and fixed in this recheck:

- Configuration typos silently fell back to unintended behavior. Mode fields now validate enumerated values; embedding dimensions are constrained to 1536 while accepting ordinary integer environment variables.
- Auth mail handlers used exception logging, which could include SMTP response details. They now log event names only; a regression injects a sensitive synthetic exception and checks that it is not logged.
- An over-limit streamed body without Content-Length was stopped but converted by body parsing to HTTP 400. The middleware now preserves **413**, verified with an actual 22 MB asynchronous request body.
- Old chat/document/search/member/audit responses could repopulate state after an organization switch. Current-scope checks prevent stale application; pending confirmations and upload workspace selections are cleared. Three new RTL regressions exercise deferred responses and state cleanup. This is additional UI protection, not a substitute for the server tenant checks.
- `.dockerignore` omitted host `.venv` directories. Comprehensive dependency/runtime/credential/artifact exclusions were added, and the actual API image was inspected to assert `/srv/.venv` is absent.
- `make demo` now invokes Bash explicitly, so archive extractors losing executable mode do not break the quick start. ZIP Unix executable metadata is also retained.

The local Git metadata needed reinitialization after workspace restoration; only a local candidate index was prepared. No commit, remote, or push was created. Ruff also removed unused test imports. The final results below supersede the earlier 33/35 backend and 7 frontend counts.

## 1. Actual final results

| Command / check executed | Environment | Final observed result |
|---|---|---|
| `python -m pytest -q` | Isolated clean Python environment, SQLite/local files | **41 passed, 2 skipped**. Skips explicitly require PostgreSQL/external services. |
| `docker compose ... run --no-deps --rm test` after starting dependencies | Patched Python 3.12 images, PostgreSQL/pgvector, Redis, MinIO, Celery | **43 passed**, no skips. |
| `npm ci` | Clean checkout, committed npm lock | **passed**; dependencies installed without pre-existing node_modules. |
| `npm run typecheck` | Clean checkout, strict TS | **passed**. |
| `npm test` | Clean checkout, Vitest 4.1.12 + RTL | **10 passed** in 3 files. |
| `npm run build` | Clean checkout | **passed**, Next 16.4.5 production build. |
| Web Dockerfile build | Node 22 container | **passed**. Fresh final-source web image built successfully; the isolated checkout also production-built the same frontend. |
| `WEB_URL=http://localhost:3001 npx playwright test` | Full Compose stack, Chromium | **3 passed**. |
| `npm run test:e2e` | Fresh `make demo` clean checkout | **3 passed** against the development demo. |
| `npm run test:e2e` | Final clean-checkout production server | **3 passed**. |
| `python scripts/verify_stack.py http://localhost:3001` | Real web/API/DB/S3/broker/worker, AI disabled | **passed** complete live flow described below. |
| `docker compose config -q` with base and test overrides | Compose v2.39.4 | **passed**. |
| API, worker, web, migration, storage initializer and MinIO Docker builds | Docker Engine 26.1.5, sandbox VFS | **passed** after fixes and resource recovery. |
| `pg_extension` / `pg_indexes` inspection | Application PostgreSQL | **vector 0.8.2**, `ix_chunks_fts` and `ix_chunks_vector` present. |
| `redis-cli ping` / `celery ... inspect ping` | Compose services | **PONG / one worker online**. |
| Alembic upgrade in full Compose | Fresh app DB | **exit 0**, API subsequently healthy. |
| `python -m alembic upgrade head`, downgrade, upgrade | Fresh SQLite migration-check DB, outside source | **passed**. |
| `actionlint .github/workflows/ci.yml` | Actionlint 1.7.7 | **passed**. Hosted GitHub Actions runs are **not claimed**. |
| `npm audit --json` | Final full npm tree, including dev dependencies | **0 known findings**. |
| `pip-audit --no-deps --disable-pip -r apps/api/requirements.lock` | Complete 96-package Python 3.12 resolution | **No known vulnerabilities found**. No hash-lock or container/Go dependency audit claimed. |
| `git diff --cached --check` and candidate secret/artifact check | Local candidate index | **passed**; no real credentials/private-key patterns found in candidate files. |
| Source ZIP / external manifest inspection | Final allowlisted release | No DB/uploads/.env/build output/node_modules/raw logs/nested archives; per-file SHA256 manifest and ZIP checksum supplied outside the archive. |

### Commands used for the Compose review

The sandbox initially lacked Docker; a local daemon was installed solely for validation. `WEB_PORT=3001` avoided the existing preview port.

```sh
cp .env.example .env
docker compose -p forge-final build minio
docker compose -p forge-final -f docker-compose.yml -f docker-compose.test.yml build api worker storage-init migrate test
# Web was built separately as well.
docker compose -p forge-final build web
WEB_PORT=3001 docker compose -p forge-final up -d --no-build
python scripts/wait_ready.py http://localhost:3001/api/health
python scripts/verify_stack.py http://localhost:3001
docker compose -p forge-final exec -T api python -m app.seed
```

The dedicated `postgres-test` service was started before the final test-container run. Its database is `knowledgeforge_test`, separate from the real application DB. In the constrained VFS sandbox, completed one-shot migration/initializer containers were removed to recover disk, then:

```sh
WEB_PORT=3001 docker compose -p forge-final -f docker-compose.yml -f docker-compose.test.yml run --no-deps --rm test
cd apps/web
WEB_URL=http://localhost:3001 npx playwright test
```

Dependencies really were running; `--no-deps` avoided re-creating completed one-shot containers, not external-service testing. The ordinary documented integration command remains `run --build --rm test` in its own disposable Compose project.

After the successful runs, `docker compose ... down -v` removed this review project's synthetic database/object-store/broker volumes, and its temporary daemon data was deleted. The lightweight no-key demo was then left running separately.

## 2. Live feature acceptance

`scripts/verify_stack.py` used separate real cookie sessions and synthetic users, not route mocks. It asserted:

1. PostgreSQL full-text and extractive health mode (refuses to run against a paid-provider-enabled stack).
2. Registration and organization ownership; real workspace creation.
3. Multipart document upload to MinIO; initial **queued** response.
4. Real Celery task processing to **ready**, nonzero chunks, at least one worker attempt.
5. Exact original-byte download and full-text retrieval.
6. Persisted LangGraph extractive chat and document-linked citations.
7. Cross-tenant download denial and empty outsider retrieval.
8. Adding a viewer; viewer can read shared content but cannot create chat.
9. Changing to private removes the document from viewer listing/retrieval.
10. Deletion removes downloads and retrieval; historic cited answer becomes hidden.
11. Conversation/workspace cleanup.

Playwright independently exercised seeded real retrieval/citation inspection, mobile navigation/theme, and new-account workspace/upload/permission/search UI flows. Screenshots contain synthetic data only. No fake AI responses were used to make the demo appear generated.

## 3. LangGraph/provider verification

Deterministic `httpx.MockTransport` tests execute the actual graph's retrieve → generate orchestration and the provider HTTP payload path. Cases: valid cited output, invalid reference number, missing references, no-evidence abstention without a provider call, HTTP upstream failure, valid embeddings and wrong embedding dimension. A PostgreSQL test writes deterministic 1536-dimensional vectors, retrieves a semantically ranked passage with no lexical overlap, and proves it does not cross tenants.

**Real provider: NOT RUN.** No approved credentials/budget were supplied; no paid API charge was incurred. Real SMTP delivery, TLS mail interoperability and model semantic correctness remain unverified. Numeric reference validation does not prove entailment.

## 4. Problems found and resolution

| Finding | Impact | Resolution / evidence |
|---|---|---|
| Unavailable MinIO and client registry images | Full documented stack could not start | Build pinned upstream MinIO source; boto3 bucket initializer replaces client-image dependency. Source build and real S3 flow passed. AGPL notice added. |
| Alembic console command could not import `app` in container | Migration blocked startup | Use `python -m alembic` and add `prepend_sys_path` to Alembic config. Real migration exited 0. |
| Exact all-term FTS missed otherwise useful remote-work evidence | SQLite tests passed while PostgreSQL chat abstained | Preserve precise full-text first, add safe normalized OR fallback when empty. PostgreSQL and live-flow regressions pass. |
| Health/UI called no-key PostgreSQL mode “hybrid” | Misleading portfolio claim | Explicit full-text / hybrid / SQLite-keyword modes. No-key passages stay extractive. |
| Extension-only upload validation / unbounded archive expansion | Parser abuse / resource risk | UTF-8/PDF checks, filename limits, DOCX entry/expanded-byte/ratio/path/macro/XML checks; upload/request/text-size limits. Unsafe fixtures rejected; real DOCX accepted. Sandbox/scanner still absent. |
| Non-atomic action token and session consumption | Concurrent replay race | Atomic DELETE RETURNING for action tokens/rotation, reset revokes sessions. Single-use and expiry tests on SQLite/PostgreSQL. |
| Per-process unbounded rate-limit map; read polling counted toward auth limit | Memory growth and incorrect throttling behavior | Bounded local windows; atomic Redis windows in Compose; mutation-only auth limits and aggregated chat category. Proxy/edge policy remains deployment work. |
| Missing origin validation and generic error boundary | CSRF defense gap and leakage risk | Explicit configured origin checks plus CSRF; body bounds; generic errors and content-free failure logs. Negative tests pass. |
| Large compressed HTTP/UI modules | Difficult review/maintenance | Domain routers/schemas/presenters, typed screen modules, shared UI/dialogs, controller hook; formatting/import cleanup. Behavior checks pass. Further controller decomposition remains optional. |
| Dialog focus effect reran on each changing callback; nested Escape reached both dialogs | Typing/focus and confirmation usability defects | Stable callback ref and topmost modal stack; two RTL regressions pass. |
| Initial Python lock audit: 88 advisory entries in 6 packages (entries may duplicate IDs) | Known dependency exposure | Upgrade affected dependencies and resolve 96-package lock; no known findings after update; patched Docker suite 43 passed. |
| Full npm audit found critical development-tool advisories | Unsafe developer/test dependency tree | Vitest 4.1.12, fresh npm lock; full-tree audit now zero; 7 tests and clean build pass. |
| Runtime DBs/uploads/raw logs/screenshots/output archive clutter | Unsafe/poor Git release | Delete/exclude runtime data and raw test outputs; only curated synthetic screenshots retained in docs/images. Release allowlist, secret-pattern scan, manifest/checksum. |
| Tests could drop the same DB as the application | Data-loss risk if pointed at app DB | Separate disposable PostgreSQL test service; test fixture refuses names not ending `_test`. |

### Failed attempts were not relabeled as passes

In the initial audit, the first registry pulls failed, the initial MinIO compile was killed for memory, and early VFS container runs ran out of disk. The source build was bounded with Go memory/parallelism flags; intermediates and completed one-shot containers were removed; successful builds and suites were rerun. A non-supported Compose `run --no-build` flag was corrected to a prebuilt-image run. The first PostgreSQL suite exposed the FTS regression described above. Vitest's first patch upgrade still had advisories, so it was upgraded further and re-audited. In this fresh recheck, the new streamed-body regression first failed (400 instead of 413), then passed after the middleware correction. The first new hook-test compile failed on the deferred promise's generic type; it was corrected before the successful TS/test runs. Running the MinIO source build concurrently with frontend/container verification exceeded the 2 GB sandbox memory limit and killed the Go compiler. The demo and other builds were stopped; the identical pinned MinIO source/Dockerfile then built successfully on a sequential retry. No successful result is inferred from a failed attempt. Only final successful runs appear as passes in section 1.

## 5. Clean-checkout and packaging verification

A new `release-check` directory was populated with `git checkout-index` from the candidate files, with no existing `.env`, SQLite DB, uploads, venv, or node_modules. `make demo` created its own isolated Python environment, installed the Python lock, ran `npm ci`, seeded external demo state and started successfully. That checkout passed 41 SQLite tests, 10 frontend tests, TS checking and three browser flows. The clean checkout independently passed npm installation, TS/frontend tests and the production build. Its no-key demo passed all three browser flows, was then stopped, and its production server passed all three flows with the final API. Afterward, only unused test imports and documentation/evidence were cleaned up; the final-source container suite was also run. The raw result counts are 41 passed / 2 skipped for SQLite, 43 passed for Compose, 10 frontend tests and 3 flows per browser run.

The final package contains source/configuration/docs/tests and two curated synthetic screenshots. It omits `.git`, private `.env` files, virtual environments, node_modules, compiled assets, databases/WAL files, uploaded documents, traces, raw logs and other ZIPs. A local Git index was prepared for review, **not committed or pushed**. There was no pre-existing Git history/remote to inspect; a historical secrets audit is not claimed. The example local passwords and deliberately public demo identity are explicitly documented, not real secrets.

Raw command logs were kept outside the source tree during review. The human-readable results are here; raw outputs are not release-package contents.

## 6. CI and remaining limits

Actionlint passed and the constituent local/Compose commands were exercised. CI uses the same locked dependencies, no paid provider, an isolated test DB, and bounded readiness. **No hosted GitHub Actions run, branch-protection rule or repository permission configuration was verified.** Do not display an invented green CI badge.

Remaining production blockers: parser process isolation/malware checks; provider/SMTP live verification; TLS and trusted-proxy/edge rate policy; durable ingestion outbox/stale-job recovery; object/DB deletion reconciliation; database RLS/defense in depth; retention/purge and backup restore; secrets/IAM/bucket lifecycle; immutable audit sink; nonce CSP; observability export/alerts; accessibility/load/independent security testing. Current compatibility CSP permits inline/eval; no safety certification is implied. MinIO source/Go dependencies and container OS packages were not comprehensively vulnerability-audited.

Product omissions are listed in README, not hidden behind nonfunctional controls: OCR/versioning, nested collections/workspace ACLs, invitations/owner transfer, SSO/MFA, streaming, historical analytics/cost accounting and AWS Terraform are not implemented.

**Final decision: GitHub/recruiter portfolio ready with honest scope and local-demo instructions. Not a claim of full enterprise-spec completion, cloud deployment, model accuracy, or production readiness.**
