import os, tempfile
from sqlalchemy.engine import make_url

os.environ["DATABASE_URL"] = os.environ.get(
    "TEST_DATABASE_URL",
    f"sqlite+aiosqlite:///{tempfile.gettempdir()}/knowledgeforge_{os.getpid()}_test.db",
)

url = make_url(os.environ["DATABASE_URL"])
if not (url.database or "").split("/")[-1].split(".")[0].endswith("_test"):
    raise RuntimeError("Refusing destructive tests: database name must end in _test")
os.environ["TASK_MODE"] = "inline"
os.environ["OPENAI_API_KEY"] = ""
os.environ["ENVIRONMENT"] = "test"
import pytest_asyncio
from httpx import AsyncClient, ASGITransport
from sqlalchemy import text
from app.main import app
from app.db import engine, Base
from app.config import settings


@pytest_asyncio.fixture
async def client(tmp_path):
    settings.storage_path = str(tmp_path)
    settings.storage_backend = "local"
    async with engine.begin() as conn:
        if engine.dialect.name == "postgresql":
            await conn.execute(text("CREATE EXTENSION IF NOT EXISTS vector"))
        await conn.run_sync(Base.metadata.drop_all)
        await conn.run_sync(Base.metadata.create_all)
    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as client:
        yield client
    await engine.dispose()
