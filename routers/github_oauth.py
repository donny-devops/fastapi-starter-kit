import secrets
from urllib.parse import urlencode

import httpx
from fastapi import APIRouter, HTTPException, Query, Request
from fastapi.responses import JSONResponse, RedirectResponse

from config import (
    GITHUB_CLIENT_ID,
    GITHUB_CLIENT_SECRET,
    GITHUB_REDIRECT_URI,
)

router = APIRouter(prefix="/auth", tags=["GitHub OAuth"])

GITHUB_AUTHORIZE_URL = "https://github.com/login/oauth/authorize"
GITHUB_TOKEN_URL = "https://github.com/login/oauth/access_token"
GITHUB_USER_URL = "https://api.github.com/user"

# In-memory state store — replace with Redis/DB in production
_oauth_state_store: set[str] = set()


@router.get("/login/github", summary="Redirect to GitHub OAuth")
async def login_github():
    """Generate a state token and redirect the user to GitHub's OAuth consent screen."""
    if not GITHUB_CLIENT_ID:
        raise HTTPException(status_code=500, detail="GITHUB_CLIENT_ID is not configured")

    state = secrets.token_urlsafe(32)
    _oauth_state_store.add(state)

    params = {
        "client_id": GITHUB_CLIENT_ID,
        "redirect_uri": GITHUB_REDIRECT_URI,
        "scope": "read:user user:email",
        "state": state,
    }
    return RedirectResponse(
        url=f"{GITHUB_AUTHORIZE_URL}?{urlencode(params)}",
        status_code=302,
    )


@router.get("/github/callback", summary="GitHub OAuth callback")
async def github_callback(
    request: Request,
    code: str | None = Query(default=None),
    state: str | None = Query(default=None),
    error: str | None = Query(default=None),
    error_description: str | None = Query(default=None),
):
    """Receive the OAuth code from GitHub, validate state, and exchange for an access token."""
    if error:
        raise HTTPException(
            status_code=400,
            detail={"error": error, "error_description": error_description},
        )

    if not code or not state:
        raise HTTPException(status_code=400, detail="Missing code or state parameter")

    if state not in _oauth_state_store:
        raise HTTPException(status_code=400, detail="Invalid or expired OAuth state")
    _oauth_state_store.discard(state)

    if not GITHUB_CLIENT_ID or not GITHUB_CLIENT_SECRET:
        raise HTTPException(
            status_code=500,
            detail="GitHub OAuth credentials are not fully configured",
        )

    token_payload = {
        "client_id": GITHUB_CLIENT_ID,
        "client_secret": GITHUB_CLIENT_SECRET,
        "code": code,
        "redirect_uri": GITHUB_REDIRECT_URI,
        "state": state,
    }

    async with httpx.AsyncClient(timeout=15.0) as client:
        # Exchange code for access token
        token_resp = await client.post(
            GITHUB_TOKEN_URL,
            data=token_payload,
            headers={"Accept": "application/json"},
        )
        if token_resp.status_code != 200:
            raise HTTPException(
                status_code=502,
                detail=f"GitHub token exchange failed: {token_resp.text}",
            )

        token_data = token_resp.json()
        if "error" in token_data:
            raise HTTPException(status_code=400, detail=token_data)

        access_token: str = token_data.get("access_token", "")
        if not access_token:
            raise HTTPException(status_code=400, detail="No access token in GitHub response")

        # Fetch authenticated GitHub user
        user_resp = await client.get(
            GITHUB_USER_URL,
            headers={
                "Authorization": f"Bearer {access_token}",
                "Accept": "application/vnd.github+json",
                "X-GitHub-Api-Version": "2022-11-28",
            },
        )
        if user_resp.status_code != 200:
            raise HTTPException(
                status_code=502,
                detail=f"Failed to fetch GitHub user: {user_resp.text}",
            )

        github_user = user_resp.json()

    return JSONResponse(
        {
            "message": "GitHub OAuth successful",
            "access_token": access_token,
            "token_type": token_data.get("token_type"),
            "scope": token_data.get("scope"),
            "github_user": {
                "id": github_user.get("id"),
                "login": github_user.get("login"),
                "name": github_user.get("name"),
                "email": github_user.get("email"),
                "html_url": github_user.get("html_url"),
                "avatar_url": github_user.get("avatar_url"),
            },
        }
    )
