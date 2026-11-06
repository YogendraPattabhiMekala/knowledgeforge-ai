# Worker
The worker runs the same domain package as the API; no duplicated ingestion logic.
Entrypoint: `celery -A app.tasks.celery_app worker --loglevel=INFO --concurrency=2`
See `apps/api/app/tasks.py` and `app/ingestion.py`.
