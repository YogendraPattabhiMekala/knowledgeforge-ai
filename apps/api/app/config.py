from typing import Literal
from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")
    database_url: str = "sqlite+aiosqlite:///./knowledgeforge.db"
    environment: Literal["development", "test", "production"] = "development"
    secure_cookies: bool = False
    storage_backend: Literal["local", "s3"] = "local"
    storage_path: str = "./uploads"
    s3_endpoint: str = "http://minio:9000"
    s3_bucket: str = "knowledgeforge"
    s3_server_side_encryption: Literal["", "AES256", "aws:kms"] = ""
    aws_access_key_id: str = "minioadmin"
    aws_secret_access_key: str = "minioadmin"
    redis_url: str = "redis://redis:6379/0"
    task_mode: Literal["inline", "celery"] = "inline"
    openai_api_key: str = ""
    openai_base_url: str = "https://api.openai.com/v1"
    chat_model: str = "gpt-4o-mini"
    embedding_model: str = "text-embedding-3-small"
    embedding_dimensions: int = Field(default=1536, ge=1536, le=1536)
    relevance_min_coverage: float = Field(default=0.8, ge=0.0, le=1.0)
    relevance_min_matches: int = Field(default=2, ge=1, le=20)
    bootstrap_schema: bool = True
    public_url: str = "http://localhost:3000"
    allowed_origins: list[str] = ["http://localhost:3000", "http://localhost:3001"]
    smtp_host: str = ""
    smtp_port: int = 587
    smtp_user: str = ""
    smtp_password: str = ""
    smtp_from: str = "noreply@knowledgeforge.local"


settings = Settings()
if settings.environment == "production":
    if (
        not settings.secure_cookies
        or settings.storage_backend != "s3"
        or settings.task_mode != "celery"
    ):
        raise RuntimeError("Production requires secure cookies, S3, and Celery")
    if not settings.s3_server_side_encryption:
        raise RuntimeError(
            "Production requires S3 server-side encryption configuration"
        )
    if not settings.database_url.startswith("postgresql"):
        raise RuntimeError("Production requires PostgreSQL")
