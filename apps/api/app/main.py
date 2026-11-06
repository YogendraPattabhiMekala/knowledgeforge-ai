"""Application composition only. Domain HTTP handlers live in routes/."""

from contextlib import asynccontextmanager
from fastapi import FastAPI
from sqlalchemy import text
import structlog
from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor
from .config import settings
from .db import Base, engine
from .middleware import install_security
from .routes import auth, organizations, documents, conversations, operations

structlog.configure(
    processors=[
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.processors.format_exc_info,
        structlog.processors.JSONRenderer(),
    ]
)


@asynccontextmanager
async def lifespan(app):
    if settings.bootstrap_schema:
        async with engine.begin() as connection:
            if engine.dialect.name == "postgresql":
                await connection.execute(text("CREATE EXTENSION IF NOT EXISTS vector"))
            await connection.run_sync(Base.metadata.create_all)
    yield
    await engine.dispose()


app = FastAPI(title="KnowledgeForge AI", version="0.2.0", lifespan=lifespan)
install_security(app)
FastAPIInstrumentor.instrument_app(app)
for domain in (auth, organizations, documents, conversations, operations):
    app.include_router(domain.router)
