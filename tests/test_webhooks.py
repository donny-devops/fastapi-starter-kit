import base64
import json
import time
from datetime import datetime, timezone

import pytest
from httpx import AsyncClient
from svix.webhooks import Webhook

import routers.webhooks as webhooks_router
from models import ClerkUser, SessionLocal, init_sqlalchemy_db

TEST_KEY = "whsec_" + base64.b64encode(b"012345678901234567890123").decode()

init_sqlalchemy_db()


@pytest.fixture(autouse=True)
def override_secret(monkeypatch):
    init_sqlalchemy_db()
    monkeypatch.setattr(webhooks_router, "CLERK_WEBHOOK_SIGNING_SECRET", TEST_KEY)
    session = SessionLocal()
    session.query(ClerkUser).delete()
    session.commit()
    session.close()
    yield
    session = SessionLocal()
    session.query(ClerkUser).delete()
    session.commit()
    session.close()


def sign_payload(payload_dict: dict, secret: str = TEST_KEY, msg_id: str | None = None) -> tuple[str, dict]:
    raw_body = json.dumps(payload_dict)
    msg_id = msg_id or f"msg_{int(time.time() * 1000)}"
    now = datetime.now(timezone.utc)
    timestamp_epoch = int(now.timestamp())

    wh = Webhook(secret)
    signature = wh.sign(msg_id, now, raw_body)

    headers = {
        "svix-id": msg_id,
        "svix-timestamp": str(timestamp_epoch),
        "svix-signature": signature,
        "content-type": "application/json",
    }
    return raw_body, headers


@pytest.mark.asyncio
async def test_clerk_webhook_missing_headers(client: AsyncClient):
    resp = await client.post("/api/webhooks/clerk", content="{}")
    assert resp.status_code == 400
    assert "Missing Svix headers" in resp.json()["detail"]


@pytest.mark.asyncio
async def test_clerk_webhook_invalid_signature(client: AsyncClient):
    payload = {"type": "user.created", "data": {"id": "user_bad_sig"}}
    raw_body, headers = sign_payload(payload)
    headers["svix-signature"] = "v1,invalid_signature_hex"

    resp = await client.post("/api/webhooks/clerk", content=raw_body, headers=headers)
    assert resp.status_code == 400
    assert "Invalid webhook signature" in resp.json()["detail"]


@pytest.mark.asyncio
async def test_clerk_webhook_user_created(client: AsyncClient):
    payload = {
        "type": "user.created",
        "data": {
            "id": "user_2test12345",
            "email_addresses": [{"email_address": "clerk_alice@example.com"}],
            "first_name": "Alice",
            "last_name": "Clerkson",
            "image_url": "https://img.clerk.com/alice.png",
        },
    }
    raw_body, headers = sign_payload(payload)

    resp = await client.post("/api/webhooks/clerk", content=raw_body, headers=headers)
    assert resp.status_code == 200
    assert resp.json()["received"] is True
    assert resp.json()["event_type"] == "user.created"

    session = SessionLocal()
    user = session.query(ClerkUser).filter(ClerkUser.id == "user_2test12345").first()
    assert user is not None
    assert user.email == "clerk_alice@example.com"
    assert user.name == "Alice Clerkson"
    assert user.is_active is True
    session.close()


@pytest.mark.asyncio
async def test_clerk_webhook_user_updated(client: AsyncClient):
    session = SessionLocal()
    initial_user = ClerkUser(
        id="user_2test_update",
        email="old_email@example.com",
        name="Bob",
        first_name="Bob",
    )
    session.add(initial_user)
    session.commit()
    session.close()

    payload = {
        "type": "user.updated",
        "data": {
            "id": "user_2test_update",
            "email_addresses": [{"email_address": "new_email@example.com"}],
            "first_name": "Robert",
            "last_name": "Builder",
        },
    }
    raw_body, headers = sign_payload(payload)

    resp = await client.post("/api/webhooks/clerk", content=raw_body, headers=headers)
    assert resp.status_code == 200

    session = SessionLocal()
    user = session.query(ClerkUser).filter(ClerkUser.id == "user_2test_update").first()
    assert user is not None
    assert user.email == "new_email@example.com"
    assert user.name == "Robert Builder"
    session.close()


@pytest.mark.asyncio
async def test_clerk_webhook_user_deleted(client: AsyncClient):
    session = SessionLocal()
    user_to_delete = ClerkUser(
        id="user_2test_delete",
        email="delete_me@example.com",
    )
    session.add(user_to_delete)
    session.commit()
    session.close()

    payload = {
        "type": "user.deleted",
        "data": {"id": "user_2test_delete"},
    }
    raw_body, headers = sign_payload(payload)

    resp = await client.post("/api/webhooks/clerk", content=raw_body, headers=headers)
    assert resp.status_code == 200

    session = SessionLocal()
    user = session.query(ClerkUser).filter(ClerkUser.id == "user_2test_delete").first()
    assert user is None
    session.close()


@pytest.mark.asyncio
async def test_clerk_webhook_unhandled_event(client: AsyncClient):
    payload = {
        "type": "session.created",
        "data": {"id": "sess_12345"},
    }
    raw_body, headers = sign_payload(payload)

    resp = await client.post("/api/webhooks/clerk", content=raw_body, headers=headers)
    assert resp.status_code == 200
    assert resp.json()["received"] is True
    assert resp.json()["event_type"] == "session.created"
