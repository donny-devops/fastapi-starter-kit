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
GITHUB_EMAILS_URL = "https://api.github.com/user/emails"


@router.get("/login/github", summary="Redirect to GitHub OAuth")
async def login_github(request: Request):
    """Generate a state token, store in session, redirect to GitHub consent."""
    if not GITHUB_CLIENT_ID:
        raise HTTPException(status_code=500, detail="GITHUB_CLIENT_ID is not configured")
    state = secrets.token_urlsafe(32)
    request.session["oauth_state"] = state
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
    """Validate state, exchange code for token, fetch user, store in session."""
    if error:
        raise HTTPException(
            status_code=400,
            detail={"error": error, "error_description": error_description},
        )
    if not code or not state:
        raise HTTPException(status_code=400, detail="Missing code or state parameter")

    # Session-based state validation (multi-worker safe)
    expected_state = request.session.pop("oauth_state", None)
    if not expected_state or state != expected_state:
        raise HTTPException(status_code=400, detail="Invalid or expired OAuth state")

    if not GITHUB_CLIENT_ID or not GITHUB_CLIENT_SECRET:
        raise HTTPException(
            status_code=500,
            detail="GitHub OAuth credentials are not fully configured",
        )

    _timeout = httpx.Timeout(connect=5.0, read=10.0, write=5.0, pool=5.0)

    async with httpx.AsyncClient(timeout=_timeout) as client:
        # 1. Exchange code for access token (state not sent - not part of spec)
        token_resp = await client.post(
            GITHUB_TOKEN_URL,
            data={
                "client_id": GITHUB_CLIENT_ID,
                "client_secret": GITHUB_CLIENT_SECRET,
                "code": code,
                "redirect_uri": GITHUB_REDIRECT_URI,
            },
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

        _gh_headers = {
            "Authorization": f"Bearer {access_token}",
            "Accept": "application/vnd.github+json",
            "X-GitHub-Api-Version": "2022-11-28",
        }

        # 2. Fetch user profile
        user_resp = await client.get(GITHUB_USER_URL, headers=_gh_headers)
        if user_resp.status_code != 200:
            raise HTTPException(
                status_code=502,
                detail=f"Failed to fetch GitHub user: {user_resp.text}",
            )
        github_user = user_resp.json()

        # 3. Resolve primary verified email (null for private-email users)
        email = github_user.get("email")
        if not email:
            emails_resp = await client.get(GITHUB_EMAILS_URL, headers=_gh_headers)
            if emails_resp.status_code == 200:
                email = next(
                    (
                        e["email"]
                        for e in emails_resp.json()
                        if e.get("primary") and e.get("verified")
                    ),
                    None,
                )

    # 4. Store access token server-side only - never expose to client
    request.session["access_token"] = access_token
    request.session["github_user_id"] = github_user.get("id")

    return JSONResponse(
        {
            "message": "GitHub OAuth successful",
            "github_user": {
                "id": github_user.get("id"),
                "login": github_user.get("login"),
                "name": github_user.get("name"),
                "email": email,
                "html_url": github_user.get("html_url"),
                "avatar_url": github_user.get("avatar_url"),
            },
        }
    )


@router.get("/logout", summary="Clear session")
async def logout(request: Request):
    request.session.clear()
    return {"status": "logged out"}
