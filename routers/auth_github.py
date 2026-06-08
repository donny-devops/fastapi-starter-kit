import logging
import httpx  # noqa: F401
from fastapi import APIRouter, HTTPException, Request, status  # noqa: F401
from fastapi.responses import RedirectResponse  # noqa: F401
from config import GITHUB_CLIENT_ID, GITHUB_CLIENT_SECRET, GITHUB_REDIRECT_URI  # noqa: F401

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/auth/github", tags=["auth"])

GITHUB_AUTHORIZE_URL = "https://github.com/login/oauth/authorize"
GITHUB_TOKEN_URL     = "https://github.com/login/oauth/access_token"
GITHUB_USER_URL      = "https://api.github.com/user"
