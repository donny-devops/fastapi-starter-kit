# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added
- Cloudflare mesh scale-up on the origin: L1 LRU cache, 50k req/min rate
  limit, `/ops/*` shard routing, 6-way LLM failover catalog, 768-d vector
  batch ingest, D1 migration, and `cloudflare/worker.js` edge proxy.
- `GET /ready` sqlite3 ping and `GET /auth/me` for the GitHub session profile
- GitHub OAuth tests (`tests/test_auth_github.py`)

### Changed
- Replaced SQLAlchemy with the Python standard-library `sqlite3` driver. Schema
  is created in `database.py`; CRUD uses parameterized SQL. `models.py` and the
  `sqlalchemy` dependency are removed.
- Restored valid YAML for the Trivy step in `.github/workflows/ci.yml` (diff
  markers had been committed, so GitHub skipped the workflow) and pin
  `aquasecurity/trivy-action@v0.36.0` (`v0.28.0` pulls unpublished
  `setup-trivy@v0.2.1`).
- Dockerfile keeps `httpx` (needed by GitHub OAuth) and creates a writable
  `/app/data` directory for the Compose SQLite volume.
- `SECRET_KEY` is required when `APP_ENV=production`; session `Secure` /
  `SameSite` flags are env-driven. Compose `.env` is optional.
- GitHub OAuth 502 responses no longer echo upstream bodies; access tokens stay
  out of JSON and the session profile.
- Copilot review instructions match sqlite3 + optional GitHub session OAuth
  (CRUD remains public; JWT is not part of this starter).

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
