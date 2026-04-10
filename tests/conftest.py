import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from database import Base, get_db
from main import app

# ---------------------------------------------------------------------------
# Test database — single in-memory SQLite shared across all tests via StaticPool
# ---------------------------------------------------------------------------
_engine = create_engine(
    "sqlite:///:memory:",
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)
_TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=_engine)
Base.metadata.create_all(bind=_engine)


def _override_get_db():
    db = _TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()


app.dependency_overrides[get_db] = _override_get_db


# ---------------------------------------------------------------------------
# Wipe every table after each test so tests are fully isolated
# ---------------------------------------------------------------------------
@pytest.fixture(autouse=True)
def clean_tables():
    yield
    with _engine.connect() as conn:
        for table in reversed(Base.metadata.sorted_tables):
            conn.execute(table.delete())
        conn.commit()


# ---------------------------------------------------------------------------
# HTTP client
# ---------------------------------------------------------------------------
@pytest_asyncio.fixture
async def client() -> AsyncClient:
    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as ac:
        yield ac


# ---------------------------------------------------------------------------
# Shared seed data (created via the API so they go through the same session)
# ---------------------------------------------------------------------------
@pytest_asyncio.fixture
async def seeded_user(client: AsyncClient) -> dict:
    resp = await client.post(
        "/users/", json={"name": "Alice", "email": "alice@example.com"}
    )
    assert resp.status_code == 201
    return resp.json()


@pytest_asyncio.fixture
async def seeded_item(client: AsyncClient, seeded_user: dict) -> dict:
    resp = await client.post(
        "/items/",
        json={
            "title": "Widget",
            "description": "A test widget",
            "owner_id": seeded_user["id"],
        },
    )
    assert resp.status_code == 201
    return resp.json()
