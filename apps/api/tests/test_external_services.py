"""Only enabled inside a DISPOSABLE integration environment; fixtures drop schema."""

import os, asyncio, secrets
import pytest

pytestmark = pytest.mark.skipif(
    os.getenv("INTEGRATION_SERVICES") != "1",
    reason="Requires disposable PostgreSQL, Redis, MinIO and Celery services",
)


@pytest.mark.asyncio
async def test_redis_s3_and_worker_roundtrip(client):
    import boto3
    from redis.asyncio import Redis
    from app.config import settings
    from app.tasks import ingestion_task

    redis = Redis.from_url(settings.redis_url)
    assert await redis.ping()
    await redis.aclose()
    s3 = boto3.client(
        "s3",
        endpoint_url=settings.s3_endpoint,
        aws_access_key_id=settings.aws_access_key_id,
        aws_secret_access_key=settings.aws_secret_access_key,
    )
    key = "integration/" + secrets.token_hex(16)
    await asyncio.to_thread(
        s3.put_object, Bucket=settings.s3_bucket, Key=key, Body=b"integration-check"
    )
    obj = await asyncio.to_thread(s3.get_object, Bucket=settings.s3_bucket, Key=key)
    assert obj["Body"].read() == b"integration-check"
    await asyncio.to_thread(s3.delete_object, Bucket=settings.s3_bucket, Key=key)
    # Nonexistent documents are safe no-ops; verifies broker → worker → DB → result backend.
    result = ingestion_task.delay("nonexistent-integration-document", "nonexistent-org")
    await asyncio.to_thread(result.get, timeout=45)
    assert result.successful()
