# Security controls and limitations

## Permission matrix
| Operation | Owner | Admin | Member | Viewer |
|---|---|---|---|---|
| Search/read authorized documents | yes | yes | yes | yes |
| Ask/create own conversations | yes | yes | yes | no |
| Read another user's conversation | no | no | no | no |
| Upload/delete/retry documents | yes | yes | no | no |
| Create/delete workspaces | yes | yes | no | no |
| Read private docs | all org | all org | own only | own only |
| List members/audit | yes | yes | no | no |
| Add/remove/change non-owner members | yes | no | no | no |
| Rename organization | yes | no | no | no |
| Own profile and own conversation deletion | yes | yes | yes | yes |

Workspace is an organizational grouping, not a separate access-control boundary. Collections alias workspaces; nested collections are not implemented. Owner transfer is rejected.

## Authentication
Passwords: Argon2id, library defaults; 12–128 character validation. Cookies contain a random 48-byte URL-safe token, database stores SHA-256 digest, 8-hour expiry. Secure is environment-configurable; HttpOnly and SameSite=Lax are always set. State-changing authenticated routes require a per-session synchronizer CSRF token in a custom header. `/auth/refresh` rotates and revokes the previous session atomically; this is not a JWT access/refresh system. Logout deletes the server session. Password reset deletes all sessions. There is no automatic sliding renewal or refresh-family reuse detection.

Anonymous auth endpoints consume JSON, CORS is not enabled, and no wildcard credentialed origin is accepted. Configure TLS and same-origin proxying. Origin checks compare against PUBLIC_URL and explicitly configured allowed_origins. Configure deployment-specific edge/proxy throttling before public deployment. Auth/chat throttling is atomic in Redis in the Compose stack; the single-process demo has a bounded 4096-key window cache. The proxy peer can aggregate clients, so deployment-specific edge/IP policy is still needed. Proxy trust and client-IP handling must be configured at the deployment edge.

Email action tokens are random, stored hashed, expire in 30 minutes and are consumed once in ordinary sequential use. Action tokens are consumed atomically with DELETE RETURNING; repeat consumption is rejected. SMTP uses STARTTLS and optional credentials. Verification is not required for access. Outbound mail errors log generic operational failures; reset responses do not reveal account existence. No-mail reset is clearly unavailable, not a fake successful flow.

## Isolation
HTTP org access requires membership. All retrieval candidates are filtered before ranking. Downloads re-check membership/document visibility and return attachment/octet-stream with opaque storage keys, never public object URLs. Source excerpts are returned only through authorized operations. Historic citations are revalidated. No database RLS policy is installed: isolation depends on application query correctness, tested with negative cases. Shared document titles/search terms must not go into logs.

## Storage and content risks
Files are limited to 20 MB with filename, extension, UTF-8/PDF signature and DOCX archive checks. Streamed request bodies are capped at 21 MB. Original filenames are not used as object paths. Downloads use RFC 5987 encoding and nosniff. Extraction is not sandboxed; malware scanning, encrypted-PDF handling and resource-isolated parsers remain production blockers. DOCX archive entries, expansion ratio/bytes, paths, macros and XML declarations are checked before parsing. Production requires a configured S3_SERVER_SIDE_ENCRYPTION (AES256 or aws:kms) and writes request that encryption mode; bucket/IAM/lifecycle policy is still an operator responsibility. Local MinIO defaults to no server-side encryption because KMS is not configured. Local preview files are not encrypted. The shared demo account is intentionally public and must never contain sensitive content.

## Model threats
Prompts separate untrusted evidence and demand evidence-based answers; no tools are available to the model. Numeric references are validated, not semantic correctness. Prompt injection can still contaminate answers. Provider data retention, egress, PII filtering and model contract review remain unimplemented controls. Chat history can retain content after a document is deleted in the DB; the UI/API hide inaccessible cited messages, but a retention/purge policy is needed.

## Deployment blockers
See deployment/READINESS.md. No compliance, penetration-test, encryption-at-rest certification, or security audit claims are made. CSP currently permits inline/eval for framework compatibility; implement nonce-based production CSP. Final dependency audits cover the frontend production tree and the fully resolved Python lock; container OS layers and upstream Go dependencies were not comprehensively scanned.

### Fresh recheck safeguards
Runtime modes are validated, embedding dimensions are fixed at 1536, SMTP failure logs contain event names only, and oversized streamed bodies return 413 even when the parser translates receive errors. Frontend delayed responses and destructive confirmations are scoped/cleared on organization changes; server authorization remains authoritative. Docker build contexts exclude host environments, local credentials, runtime data and test outputs.
