# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added
- Cloudflare mesh scale-up on the origin: L1 LRU cache, 50k req/min rate
  limit, `/ops/*` shard routing, 6-way LLM failover catalog, 768-d vector
  batch ingest, D1 migration, and `cloudflare/worker.js` edge proxy.
- Granola engineer Cursor plugin at `.cursor/plugins/granola/`: granola-engineer
  agent, context/prep/review skills, six slash commands, always-on meeting
  context rule, and Granola MCP (`https://mcp.granola.ai/mcp`).

### Changed
- Replaced SQLAlchemy with the Python standard-library `sqlite3` driver. Schema
  is created in `database.py`; CRUD uses parameterized SQL. `models.py` and the
  `sqlalchemy` dependency are removed.
- Restored valid YAML for the Trivy step in `.github/workflows/ci.yml` (diff
  markers had been committed, so GitHub skipped the workflow) and pin
  `aquasecurity/trivy-action@v0.28.0` (the unprefixed `0.28.0` tag does not exist).
- Dockerfile keeps `httpx` (needed by GitHub OAuth) and creates a writable
  `/app/data` directory for the Compose SQLite volume.

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
