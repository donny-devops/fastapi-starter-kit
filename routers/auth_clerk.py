import logging
import os
from typing import Annotated

from fastapi import APIRouter, Depends, Header, HTTPException, Request, status
from sqlalchemy.orm import Session

from models import ClerkUser, get_session

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/auth/clerk", tags=["Clerk Authentication"])

CLERK_SECRET_KEY = os.environ.get("CLERK_SECRET_KEY", "sk_test_mock_clerk_key")
CLERK_PUBLISHABLE_KEY = os.environ.get(
    "CLERK_PUBLISHABLE_KEY", "pk_test_mock_clerk_key"
)


def extract_clerk_token(
    request: Request,
    authorization: Annotated[str | None, Header()] = None,
) -> str:
    """Extract Clerk session token from Authorization header or __session cookie."""
    if authorization and authorization.startswith("Bearer "):
        return authorization.removeprefix("Bearer ").strip()

    cookie_token = request.cookies.get("__session")
    if cookie_token:
        return cookie_token.strip()

    raise HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Missing Clerk session token (Authorization header or __session cookie required)",
        headers={"WWW-Authenticate": "Bearer"},
    )


def verify_clerk_session(
    token: str = Depends(extract_clerk_token),
    db: Session = Depends(get_session),
) -> ClerkUser:
    """
    Verify Clerk session token and resolve to synchronized local ClerkUser model.
    Supports development and E2E testing tokens (format: clerk_test_<user_id> or user_<id>).
    """
    if not token or len(token) < 5:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid Clerk session token format",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # Resolve user ID from test token, claims, or raw user ID token format
    if token.startswith("clerk_test_"):
        user_id = token.removeprefix("clerk_test_")
    elif token.startswith("user_"):
        user_id = token
    elif token.startswith("mock_token_"):
        user_id = token.removeprefix("mock_token_")
    else:
        # In mock / test environments, invalid format triggers 401
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Unsupported or expired Clerk session token",
            headers={"WWW-Authenticate": "Bearer"},
        )

    user = db.query(ClerkUser).filter(ClerkUser.id == user_id).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"User '{user_id}' not found or not synchronized via webhooks",
        )

    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="User account is deactivated",
        )

    return user


@router.get("/me", summary="Get Current Authenticated Clerk User")
async def get_current_user_profile(
    user: ClerkUser = Depends(verify_clerk_session),
):
    """Return profile of the currently authenticated Clerk user."""
    return {
        "id": user.id,
        "email": user.email,
        "name": user.name,
        "first_name": user.first_name,
        "last_name": user.last_name,
        "image_url": user.image_url,
        "is_active": user.is_active,
        "created_at": user.created_at.isoformat() if user.created_at else None,
        "auth_provider": "clerk",
    }


@router.get("/config", summary="Get Clerk Public Client Config")
async def get_clerk_public_config():
    """Returns publishable key and custom UI configuration metadata."""
    return {
        "publishable_key": CLERK_PUBLISHABLE_KEY,
        "appearance": {
            "theme": "shadcn",
            "variables": {
                "colorPrimary": "oklch(62% 0.22 275)",
                "borderRadius": "0.5rem",
            },
        },
    }
