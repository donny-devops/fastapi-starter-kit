import os
import sys

from dotenv import load_dotenv

load_dotenv()

DATABASE_URL: str = os.getenv("DATABASE_URL", "sqlite:///./app.db")
ALLOWED_ORIGINS: list[str] = os.getenv(
    "ALLOWED_ORIGINS",
    "http://localhost:3000",
).split(",")
LOG_LEVEL: str = os.getenv("LOG_LEVEL", "INFO").upper()

_SECRET_KEY_RAW: str = os.getenv("SECRET_KEY", "")
_INSECURE_DEFAULTS = {"", "change-me-in-production"}
if _SECRET_KEY_RAW in _INSECURE_DEFAULTS:
    if not DATABASE_URL.startswith("sqlite"):
        print(
            "FATAL: SECRET_KEY must be set to a secure value in production.",
            file=sys.stderr,
        )
        sys.exit(1)
    _SECRET_KEY_RAW = "dev-only-insecure-key-do-not-use-in-prod"
SECRET_KEY: str = _SECRET_KEY_RAW

# GitHub OAuth
GITHUB_CLIENT_ID: str = os.getenv("GITHUB_CLIENT_ID", "")
GITHUB_CLIENT_SECRET: str = os.getenv("GITHUB_CLIENT_SECRET", "")
GITHUB_REDIRECT_URI: str = os.getenv(
    "GITHUB_REDIRECT_URI",
    "http://localhost:8000/auth/github/callback",
)
