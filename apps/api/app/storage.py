from pathlib import Path
from .config import settings


def s3():
    import boto3

    return boto3.client(
        "s3",
        endpoint_url=settings.s3_endpoint or None,
        aws_access_key_id=settings.aws_access_key_id,
        aws_secret_access_key=settings.aws_secret_access_key,
    )


def put(key, data):
    if settings.storage_backend == "s3":
        s3().put_object(
            Bucket=settings.s3_bucket,
            Key=key,
            Body=data,
            **(
                {"ServerSideEncryption": settings.s3_server_side_encryption}
                if settings.s3_server_side_encryption
                else {}
            ),
        )
    else:
        p = Path(settings.storage_path) / key
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_bytes(data)


def get(key):
    if settings.storage_backend == "s3":
        return s3().get_object(Bucket=settings.s3_bucket, Key=key)["Body"].read()
    return (Path(settings.storage_path) / key).read_bytes()


def remove(key):
    if settings.storage_backend == "s3":
        s3().delete_object(Bucket=settings.s3_bucket, Key=key)
    else:
        (Path(settings.storage_path) / key).unlink(missing_ok=True)
