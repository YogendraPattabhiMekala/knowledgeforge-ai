import asyncio
from celery import Celery
from .config import settings
from .ingestion import ingest

celery_app = Celery(
    "knowledgeforge", broker=settings.redis_url, backend=settings.redis_url
)
celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    task_acks_late=True,
    worker_prefetch_multiplier=1,
    task_soft_time_limit=540,
    task_time_limit=600,
    broker_connection_retry_on_startup=True,
)


@celery_app.task(
    bind=True,
    autoretry_for=(Exception,),
    retry_backoff=2,
    retry_backoff_max=60,
    retry_jitter=True,
    max_retries=3,
)
def ingestion_task(self, document_id, org_id):
    # One event loop per process invocation; dispose async pools before loop teardown.
    async def run():
        from .db import engine

        try:
            await ingest(document_id, org_id)
        finally:
            await engine.dispose()

    asyncio.run(run())
