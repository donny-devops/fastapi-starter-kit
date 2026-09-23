import hashlib
import hmac
import json
import logging
import os

from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy.orm import Session
from svix.webhooks import Webhook, WebhookVerificationError

from models import ClerkUser, get_session

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/webhooks", tags=["webhooks"])

CLERK_WEBHOOK_SIGNING_SECRET = os.environ.get(
    "CLERK_WEBHOOK_SIGNING_SECRET", "whsec_test_secret_key_12345"
)
INTERNAL_SERVICE_SECRET = os.environ.get(
    "INTERNAL_SERVICE_SECRET", "mesh_internal_secret_key_998877"
)


@router.post("/clerk", status_code=status.HTTP_200_OK)
async def clerk_webhook(
    request: Request,
    session: Session = Depends(get_session),
):
    headers = request.headers
    raw_body = await request.body()

    service_sig = headers.get("x-service-signature")
    is_internal_verified = False

    if service_sig and INTERNAL_SERVICE_SECRET:
        expected_sig = hmac.new(
            INTERNAL_SERVICE_SECRET.encode("utf-8"),
            raw_body,
            hashlib.sha256,
        ).hexdigest()
        if hmac.compare_digest(expected_sig, service_sig.replace("sha256=", "")):
            is_internal_verified = True

    svix_id = headers.get("svix-id")
    svix_timestamp = headers.get("svix-timestamp")
    svix_signature = headers.get("svix-signature")

    if not is_internal_verified:
        if not svix_id or not svix_timestamp or not svix_signature:
            logger.warning("Clerk webhook rejected: missing Svix headers")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Missing Svix headers (svix-id, svix-timestamp, svix-signature)",
            )

        try:
            wh = Webhook(CLERK_WEBHOOK_SIGNING_SECRET)
            payload = wh.verify(
                raw_body,
                {
                    "svix-id": svix_id,
                    "svix-timestamp": svix_timestamp,
                    "svix-signature": svix_signature,
                },
            )
        except (WebhookVerificationError, Exception) as exc:
            logger.warning("Clerk webhook signature verification failed: %s", exc)
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid webhook signature",
            ) from exc
    else:
        try:
            payload = json.loads(raw_body.decode("utf-8"))
        except Exception as exc:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid JSON payload",
            ) from exc

    event_type = payload.get("type", "unknown")
    data = payload.get("data", {})
    svix_id = svix_id or payload.get("id") or f"edge_{os.urandom(8).hex()}"

    logger.info("Processing Clerk webhook event %s [id=%s]", event_type, svix_id)

    if event_type in {"user.created", "user.updated"}:
        user_id = data.get("id")
        if not user_id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Malformed user event: missing user id",
            )

        email_list = data.get("email_addresses", [])
        email = email_list[0].get("email_address") if email_list else None
        if not email:
            email = f"{user_id}@clerk.placeholder"

        first_name = data.get("first_name")
        last_name = data.get("last_name")
        name = f"{first_name or ''} {last_name or ''}".strip() or None
        image_url = data.get("image_url")

        existing_user = session.query(ClerkUser).filter(ClerkUser.id == user_id).first()
        if existing_user:
            existing_user.email = email
            existing_user.name = name
            existing_user.first_name = first_name
            existing_user.last_name = last_name
            existing_user.image_url = image_url
            existing_user.is_active = True
        else:
            new_user = ClerkUser(
                id=user_id,
                email=email,
                name=name,
                first_name=first_name,
                last_name=last_name,
                image_url=image_url,
                is_active=True,
            )
            session.add(new_user)
        session.commit()

    elif event_type == "user.deleted":
        user_id = data.get("id")
        if user_id:
            existing_user = (
                session.query(ClerkUser).filter(ClerkUser.id == user_id).first()
            )
            if existing_user:
                session.delete(existing_user)
                session.commit()

    return {
        "received": True,
        "event_type": event_type,
        "status": "processed",
        "svix_id": svix_id,
    }
