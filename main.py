import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from starlette.middleware.sessions import SessionMiddleware

from config import ALLOWED_ORIGINS, LOG_LEVEL, SECRET_KEY
from database import init_db
from models import init_sqlalchemy_db
from rate_limit import limiter
from routers import items, users
from routers.auth_clerk import router as clerk_auth_router
from routers.auth_github import router as github_auth_router
from routers.ops import router as ops_router
from routers.webhooks import router as webhooks_router

logging.basicConfig(
    level=getattr(logging, LOG_LEVEL, logging.INFO),
    format="%(asctime)s %(levelname)s %(name)s — %(message)s",
)

logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    init_db()
    init_sqlalchemy_db()
    logger.info("SQLite & SQLAlchemy tables ready")
    yield


app = FastAPI(
    title="fastapi-starter-kit",
    version="1.0.0",
    lifespan=lifespan,
)

app.add_middleware(
    SessionMiddleware,
    secret_key=SECRET_KEY,
    same_site="lax",
    https_only=False,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.exception_handler(Exception)
async def unhandled_exception_handler(request: Request, exc: Exception):
    logger.exception("Unhandled error on %s %s", request.method, request.url)
    return JSONResponse(
        status_code=500,
        content={"detail": "Internal server error"},
    )


app.include_router(users.router)
app.include_router(items.router)
app.include_router(github_auth_router)
app.include_router(clerk_auth_router)
app.include_router(ops_router)
app.include_router(webhooks_router)


@app.middleware("http")
async def mesh_rate_limit(request: Request, call_next):
    if request.url.path in {
        "/health",
        "/docs",
        "/openapi.json",
        "/redoc",
    } or request.url.path.startswith("/api/webhooks"):
        return await call_next(request)
    client = request.headers.get("cf-connecting-ip")
    if not client and request.client:
        client = request.client.host
    allowed, remaining = limiter.allow(client or "unknown")
    if not allowed:
        return JSONResponse(
            status_code=429,
            content={"detail": "Rate limit exceeded"},
            headers={
                "Retry-After": "60",
                "X-RateLimit-Limit": str(limiter.limit_per_minute),
                "X-RateLimit-Remaining": "0",
            },
        )
    response = await call_next(request)
    response.headers["X-RateLimit-Limit"] = str(limiter.limit_per_minute)
    response.headers["X-RateLimit-Remaining"] = str(remaining)
    return response


@app.get("/health", tags=["health"])
def health_check():
    return {"status": "ok"}
