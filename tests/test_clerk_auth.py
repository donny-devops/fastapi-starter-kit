import pytest
from httpx import AsyncClient

from models import ClerkUser, SessionLocal, init_sqlalchemy_db

init_sqlalchemy_db()


@pytest.fixture(autouse=True)
def clean_users():
    session = SessionLocal()
    session.query(ClerkUser).delete()
    session.commit()
    session.close()
    yield
    session = SessionLocal()
    session.query(ClerkUser).delete()
    session.commit()
    session.close()


@pytest.mark.asyncio
async def test_clerk_config(client: AsyncClient):
    resp = await client.get("/auth/clerk/config")
    assert resp.status_code == 200
    data = resp.json()
    assert "publishable_key" in data
    assert data["appearance"]["theme"] == "shadcn"
    assert data["appearance"]["variables"]["borderRadius"] == "0.5rem"


@pytest.mark.asyncio
async def test_clerk_me_missing_token(client: AsyncClient):
    resp = await client.get("/auth/clerk/me")
    assert resp.status_code == 401
    assert "Missing Clerk session token" in resp.json()["detail"]


@pytest.mark.asyncio
async def test_clerk_me_invalid_token_format(client: AsyncClient):
    resp = await client.get("/auth/clerk/me", headers={"Authorization": "Bearer bad"})
    assert resp.status_code == 401
    assert "Invalid Clerk session token" in resp.json()["detail"]


@pytest.mark.asyncio
async def test_clerk_me_user_not_found(client: AsyncClient):
    resp = await client.get(
        "/auth/clerk/me",
        headers={"Authorization": "Bearer clerk_test_user_nonexistent"},
    )
    assert resp.status_code == 404
    assert "not found" in resp.json()["detail"]


@pytest.mark.asyncio
async def test_clerk_me_authenticated_bearer(client: AsyncClient):
    session = SessionLocal()
    user = ClerkUser(
        id="user_2clerk_alice",
        email="alice@clerk.dev",
        name="Alice Authenticated",
        first_name="Alice",
        last_name="Authenticated",
        is_active=True,
    )
    session.add(user)
    session.commit()
    session.close()

    resp = await client.get(
        "/auth/clerk/me",
        headers={"Authorization": "Bearer clerk_test_user_2clerk_alice"},
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["id"] == "user_2clerk_alice"
    assert data["email"] == "alice@clerk.dev"
    assert data["name"] == "Alice Authenticated"
    assert data["auth_provider"] == "clerk"
    assert data["is_active"] is True


@pytest.mark.asyncio
async def test_clerk_me_authenticated_cookie(client: AsyncClient):
    session = SessionLocal()
    user = ClerkUser(
        id="user_2clerk_bob",
        email="bob@clerk.dev",
        name="Bob Builder",
        is_active=True,
    )
    session.add(user)
    session.commit()
    session.close()

    resp = await client.get(
        "/auth/clerk/me",
        cookies={"__session": "user_2clerk_bob"},
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["id"] == "user_2clerk_bob"
    assert data["email"] == "bob@clerk.dev"


@pytest.mark.asyncio
async def test_clerk_me_inactive_user_forbidden(client: AsyncClient):
    session = SessionLocal()
    user = ClerkUser(
        id="user_2clerk_deactivated",
        email="deactivated@clerk.dev",
        name="Inactive Person",
        is_active=False,
    )
    session.add(user)
    session.commit()
    session.close()

    resp = await client.get(
        "/auth/clerk/me",
        headers={"Authorization": "Bearer user_2clerk_deactivated"},
    )
    assert resp.status_code == 403
    assert "deactivated" in resp.json()["detail"]
