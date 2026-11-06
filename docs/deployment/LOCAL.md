# Deployment and operations

## Local stack
Copy `.env.example` to `.env`, change passwords, run `docker compose up --build -d`. Migration runs to completion before API/worker. Storage-init creates a private bucket. Only web port 3000 and loopback MinIO console 9001 are published. Containers run app processes as non-root. The worker is a separate process using the API image.

`make seed` creates one synthetic organization and owner; it is idempotent by fixture-user existence and blocked when ENVIRONMENT=production. Delete/recreate a disposable database to reset fixtures. Never seed production.

## Production preparation
This Compose file is a local starting point, not a hosted architecture. Terminate TLS, configure PUBLIC_URL, SECURE_COOKIES=true, ENVIRONMENT=production, PostgreSQL URL, TASK_MODE=celery, STORAGE_BACKEND=s3, provider secret injection, restrictive bucket policy and backups. Production guard rejects SQLite/local storage/in-process task mode/insecure cookies and missing S3 encryption configuration. It does not establish complete readiness.

Next rewrite destinations are compiled at build time. Build with the intended API_INTERNAL_URL (Dockerfile ARG defaults to http://api:8000). Do not expose localhost addresses to browser JavaScript. Web fetches only relative `/api` URLs. Never pass OPENAI_API_KEY to a NEXT_PUBLIC variable.

## Failure handling
Celery uses late acknowledgment, JSON serialization, prefetch=1, 3 retries with bounded exponential backoff/jitter and 540/600s soft/hard limits. Terminal task state is FAILED and document status is failed; UI retry is an explicit administrative operation. No separate dead-letter queue is implemented. A killed worker or queue dispatch crash may leave processing/queued rows; operators must inspect logs and recover them manually. No transactional outbox or stale-job sweeper yet.

## Observability
`docker compose logs -f api worker` produces application logs and processing failures. `/api/health` checks DB connectivity only. Add readiness checks for broker, storage and worker liveness. FastAPI is instrumented for OpenTelemetry; an exporting SDK/collector configuration is not bundled. Never log document contents or credentials. No measured SLOs exist. The final local Compose run is verified in docs/VALIDATION.md; this is not an AWS deployment.

## Backup and rollback
Back up PostgreSQL and object storage together, encrypt backups, test restore, and document retention before production. Redis persistence is enabled but not a substitute for an ingestion outbox. Schema rollback is destructive for the initial migration; use forward-compatible expand/contract migrations after real data exists. Restore is not tested here. Terraform folder contains design notes only.
