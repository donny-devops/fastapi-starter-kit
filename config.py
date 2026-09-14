import os
import sys

from dotenv import load_dotenv

load_dotenv()

# Prefer SQLITE_PATH; DATABASE_URL remains accepted for existing .env files.
SQLITE_PATH: str = os.getenv("SQLITE_PATH") or os.getenv(
    "DATABASE_URL",
    "./app.db",
)
RATE_LIMIT_PER_MINUTE: int = int(os.getenv("RATE_LIMIT_PER_MINUTE", "50000"))
L1_CACHE_MAXSIZE: int = int(os.getenv("L1_CACHE_MAXSIZE", "4096"))
L1_CACHE_TTL_SECONDS: float = float(os.getenv("L1_CACHE_TTL_SECONDS", "30"))
ALLOWED_ORIGINS: list[str] = [
    origin.strip()
    for origin in os.getenv("ALLOWED_ORIGINS", "http://localhost:3000").split(",")
    if origin.strip()
]
LOG_LEVEL: str = os.getenv("LOG_LEVEL", "INFO").upper()

_SECRET_KEY_RAW: str = os.getenv("SECRET_KEY", "")
_INSECURE_DEFAULTS = {"", "change-me-in-production"}
if _SECRET_KEY_RAW in _INSECURE_DEFAULTS:
    print(
        "WARNING: SECRET_KEY is unset; using a development-only default.",
        file=sys.stderr,
    )
    _SECRET_KEY_RAW = "dev-only-insecure-key-do-not-use-in-prod"
SECRET_KEY: str = _SECRET_KEY_RAW

# GitHub OAuth
GITHUB_CLIENT_ID: str = os.getenv("GITHUB_CLIENT_ID", "")
GITHUB_CLIENT_SECRET: str = os.getenv("GITHUB_CLIENT_SECRET", "")
GITHUB_REDIRECT_URI: str = os.getenv(
    "GITHUB_REDIRECT_URI",
    "http://localhost:8000/auth/github/callback",
)
