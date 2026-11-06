import time
from botocore.exceptions import ClientError, EndpointConnectionError
from .storage import s3
from .config import settings


def main():
    for attempt in range(30):
        try:
            client = s3()
            try:
                client.head_bucket(Bucket=settings.s3_bucket)
            except ClientError as exc:
                if exc.response["ResponseMetadata"]["HTTPStatusCode"] != 404:
                    raise
                client.create_bucket(Bucket=settings.s3_bucket)
            return
        except (ClientError, EndpointConnectionError):
            if attempt == 29:
                raise
            time.sleep(2)


if __name__ == "__main__":
    main()
