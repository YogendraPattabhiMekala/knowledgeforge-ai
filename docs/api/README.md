# API contract
Generated specification: `packages/shared-contracts/openapi.json`; regenerate with `make contracts`.
FastAPI exposes `/openapi.json` and `/docs` on the internal API server. Browser calls use `/api/*` through Next rewrites. No cross-origin cookie API is needed.

- `/api/auth/register`, `/login`, `/logout`, `/refresh`, `/me`, `/forgot-password`, `/reset-password`, `/verify`
- `/api/profile` PATCH
- `/api/organizations` POST, `/api/organizations/{org_id}` PATCH
- `.../workspaces` GET/POST, `.../workspaces/{id}` DELETE
- `.../documents` GET/POST (multipart: file, optional workspace_id, visibility)
- `.../documents/{id}` GET/PATCH/DELETE, `/download` GET, `/retry` POST
- `.../search?q=...` GET; passage IDs, document IDs, page and text
- `.../chat` POST `{question, conversation_id?}`; persisted answer and source objects
- `.../conversations` GET; `.../conversations/{id}` GET/DELETE
- `.../members` GET/POST; `.../members/{id}` PATCH/DELETE
- `.../analytics`, `.../audit` GET
- `/api/health` GET validates database only, not every downstream service

After registration/login, use the returned `csrf` as `X-CSRF-Token` on authenticated mutations. `/me` returns CSRF and available orgs after reload. Session tokens stay HttpOnly. List endpoints currently lack cursor pagination (audit limited to 100, passages to 100); implement for large tenants. HTTP errors use FastAPI `{detail}`. 401 unauthenticated, 403 role/CSRF, 404 hidden resource, 409 invalid state, 413 size, 415 unsupported format, 422 validation, 502 provider, 503 unconfigured mail.

The web currently keeps handwritten strict interfaces for its consumed response subset. OpenAPI is the shared canonical machine-readable contract; generated TypeScript client integration is future work.
