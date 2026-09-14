import sqlite3

import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient

from cache import l1
from database import get_db, init_db, set_connection_factory
from main import app
from rate_limit import limiter

TEST_DB_URI = "file:testdb?mode=memory&cache=shared"

_keeper = sqlite3.connect(TEST_DB_URI, uri=True, check_same_thread=False)
_keeper.row_factory = sqlite3.Row
_keeper.execute("PRAGMA foreign_keys = ON")
init_db(_keeper)


def _memory_connect() -> sqlite3.Connection:
    conn = sqlite3.connect(TEST_DB_URI, uri=True, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


set_connection_factory(_memory_connect)


def _override_get_db():
    conn = _memory_connect()
    try:
        yield conn
    finally:
        conn.close()


app.dependency_overrides[get_db] = _override_get_db


@pytest.fixture(autouse=True)
def clean_tables():
    l1.clear()
    limiter.reset()
    yield
    _keeper.execute("DELETE FROM items")
    _keeper.execute("DELETE FROM users")
    try:
        _keeper.execute("DELETE FROM sqlite_sequence")
    except sqlite3.OperationalError:
        pass
    _keeper.commit()


@pytest_asyncio.fixture
async def client() -> AsyncClient:
    async with AsyncClient(
        transport=ASGITransport(app=app),
        base_url="http://test",
    ) as ac:
        yield ac


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
