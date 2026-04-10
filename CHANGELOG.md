# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added
- GitHub Actions CI workflow (`.github/workflows/ci.yml`): ruff lint, ruff format
  check, pytest, and Docker build on every push and PR; Docker build is gated on
  lint + test passing and uses GHA layer cache

### Changed
- Dockerfile: production dependencies now filtered with `sed` (replaces fragile
  `grep … | xargs` pipe); container now runs as a non-root `appuser`
- `docker-compose.yml`: `environment` block moved above `volumes` for readability;
  healthcheck `test` command formatted as a multi-line YAML sequence

## [0.1.0] - 2026-04-10

### Added
- FastAPI application with CORS middleware, structured logging, and global error handler
- SQLite database via SQLAlchemy with automatic table creation on startup
- Full CRUD REST endpoints for `/users` and `/items`
- Pydantic v2 request/response schemas with `from_attributes` ORM mode
- Environment config via `python-dotenv` (`DATABASE_URL`, `ALLOWED_ORIGINS`, `LOG_LEVEL`)
- `GET /health` endpoint
- Comprehensive pytest suite (55 tests) using `httpx.AsyncClient` and in-memory SQLite
- Dockerfile with slim Python base and production-only dependencies
- `docker-compose.yml` with named volume for SQLite persistence and a healthcheck
- GitHub Actions CI workflow: ruff lint, pytest, and Docker build on every push and PR
