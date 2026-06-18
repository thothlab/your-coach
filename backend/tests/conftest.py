import asyncio
import os
import subprocess
import sys
from collections.abc import AsyncIterator

# Force the test environment BEFORE any trainbeat import.
# Tests sign initData with a known token; we must control it deterministically,
# regardless of any TELEGRAM_BOT_TOKEN inherited from the CI environment.
_TEST_DB_URL = "postgresql+asyncpg://trainbeat:trainbeat@localhost:5432/trainbeat_test"
os.environ["DATABASE_URL"] = _TEST_DB_URL
os.environ["TELEGRAM_BOT_TOKEN"] = "1234567890:test-bot-token-7777777777"
os.environ.setdefault("APP_ENV", "test")
os.environ.setdefault("TELEGRAM_WEBAPP_URL", "https://localhost:5173")

import asyncpg  # noqa: E402
import httpx  # noqa: E402
import pytest  # noqa: E402
import pytest_asyncio  # noqa: E402
from sqlalchemy import text  # noqa: E402

from trainbeat.db import SessionLocal, engine  # noqa: E402
from trainbeat.main import app  # noqa: E402

_BACKEND_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def _ensure_test_db_exists() -> None:
    async def _do() -> None:
        admin_url = "postgresql://trainbeat:trainbeat@localhost:5432/postgres"
        conn = await asyncpg.connect(admin_url)
        try:
            await conn.execute("CREATE DATABASE trainbeat_test")
        except asyncpg.exceptions.DuplicateDatabaseError:
            pass
        finally:
            await conn.close()

    asyncio.run(_do())


@pytest.fixture(scope="session", autouse=True)
def setup_test_db() -> None:
    _ensure_test_db_exists()
    env = {**os.environ, "DATABASE_URL": _TEST_DB_URL}
    subprocess.run(
        [sys.executable, "-m", "alembic", "upgrade", "head"],
        check=True,
        cwd=_BACKEND_DIR,
        env=env,
    )


async def _truncate_all() -> None:
    async with engine.begin() as conn:
        result = await conn.execute(
            text(
                "SELECT tablename FROM pg_tables "
                "WHERE schemaname='public' AND tablename != 'alembic_version'"
            )
        )
        tables = [row[0] for row in result.all()]
        if tables:
            joined = ", ".join(tables)
            await conn.execute(text(f"TRUNCATE TABLE {joined} RESTART IDENTITY CASCADE"))


@pytest_asyncio.fixture
async def db_session() -> AsyncIterator:
    await _truncate_all()
    async with SessionLocal() as session:
        yield session


@pytest_asyncio.fixture
async def http_client() -> AsyncIterator[httpx.AsyncClient]:
    await _truncate_all()
    transport = httpx.ASGITransport(app=app)
    async with httpx.AsyncClient(transport=transport, base_url="http://test") as client:
        yield client
