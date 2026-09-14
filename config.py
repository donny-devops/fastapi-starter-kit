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
APP_ENV: str = os.getenv("APP_ENV", "development").strip().lower() or "development"

_SECRET_KEY_RAW: str = os.getenv("SECRET_KEY", "")
_INSECURE_DEFAULTS = {
    "",
    "change-me-in-production",
    "change-me-in-development",
}
if APP_ENV == "production" or (
    _SECRET_KEY_RAW in _INSECURE_DEFAULTS and APP_ENV not in {"development", "test"}
):
    if _SECRET_KEY_RAW in _INSECURE_DEFAULTS:
        print(
            "FATAL: SECRET_KEY must be set to a secure value when "
            f"APP_ENV={APP_ENV!r}.",
            file=sys.stderr,
        )
        sys.exit(1)
SECRET_KEY: str = _SECRET_KEY_RAW
if SECRET_KEY in _INSECURE_DEFAULTS:
    print(
        "WARNING: SECRET_KEY is unset; using a development-only default.",
        file=sys.stderr,
    )
    SECRET_KEY = "dev-only-insecure-key-do-not-use-in-prod"

_SESSION_HTTPS_RAW = os.getenv("SESSION_HTTPS_ONLY")
if _SESSION_HTTPS_RAW is None:
    SESSION_HTTPS_ONLY: bool = APP_ENV == "production"
else:
    SESSION_HTTPS_ONLY = _SESSION_HTTPS_RAW.strip().lower() in {
        "1",
        "true",
        "yes",
        "on",
    }

_SESSION_SAME_SITE_RAW = os.getenv("SESSION_SAME_SITE", "lax").strip().lower()
if _SESSION_SAME_SITE_RAW not in {"lax", "strict", "none"}:
    _SESSION_SAME_SITE_RAW = "lax"
SESSION_SAME_SITE: str = _SESSION_SAME_SITE_RAW

# GitHub OAuth
GITHUB_CLIENT_ID: str = os.getenv("GITHUB_CLIENT_ID", "")
GITHUB_CLIENT_SECRET: str = os.getenv("GITHUB_CLIENT_SECRET", "")
GITHUB_REDIRECT_URI: str = os.getenv(
    "GITHUB_REDIRECT_URI",
    "http://localhost:8000/auth/github/callback",
)
