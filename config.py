import os
from dotenv import load_dotenv

load_dotenv()

DATABASE_URL: str = os.getenv("DATABASE_URL", "sqlite:///./app.db")

ALLOWED_ORIGINS: list[str] = os.getenv(
    "ALLOWED_ORIGINS",
    "http://localhost:3000",
).split(",")

LOG_LEVEL: str = os.getenv("LOG_LEVEL", "INFO").upper()

SECRET_KEY: str = os.getenv("SECRET_KEY", "change-me-in-production")

# GitHub OAuth
GITHUB_CLIENT_ID: str = os.getenv("GITHUB_CLIENT_ID", "")
GITHUB_CLIENT_SECRET: str = os.getenv("GITHUB_CLIENT_SECRET", "")
GITHUB_REDIRECT_URI: str = os.getenv(
    "GITHUB_REDIRECT_URI",
    "http://localhost:8000/auth/github/callback",
)
