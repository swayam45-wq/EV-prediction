"""
Pytest configuration and shared fixtures.

Sets up an in-memory SQLite database for tests so each test run
is isolated and doesn't touch the real database file.
"""

import pytest
import pytest_asyncio
from fastapi.testclient import TestClient
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession

from models.database import Base, get_db
from main import app

# ── In-memory SQLite for tests ───────────────────────────────
TEST_DATABASE_URL = "sqlite+aiosqlite:///:memory:"

test_engine = create_async_engine(TEST_DATABASE_URL, echo=False)
TestSessionLocal = async_sessionmaker(
    test_engine, class_=AsyncSession, expire_on_commit=False
)


async def override_get_db():
    """DB dependency override that uses in-memory test SQLite."""
    async with TestSessionLocal() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise


# Apply override globally for all tests
app.dependency_overrides[get_db] = override_get_db


@pytest_asyncio.fixture(scope="session", autouse=True)
async def create_test_tables():
    """Create all DB tables once per test session."""
    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield
    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)


@pytest.fixture
def client():
    """
    Sync TestClient backed by the FastAPI app with in-memory DB.
    FastAPI's TestClient handles the async/sync event loop bridging.
    """
    with TestClient(app, raise_server_exceptions=True) as c:
        yield c
