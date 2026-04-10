# fastapi-starter-kit

[![CI](https://github.com/YOUR_USERNAME/YOUR_REPO/actions/workflows/ci.yml/badge.svg)](https://github.com/YOUR_USERNAME/YOUR_REPO/actions/workflows/ci.yml)
[![Python 3.12](https://img.shields.io/badge/python-3.12-blue.svg)](https://www.python.org/downloads/)
[![Ruff](https://img.shields.io/endpoint?url=https://raw.githubusercontent.com/astral-sh/ruff/main/assets/badge/v2.json)](https://github.com/astral-sh/ruff)
[![License: MIT](https://img.shields.io/badge/license-MIT-green.svg)](LICENSE)

A production-ready FastAPI starter with SQLite/SQLAlchemy, full CRUD for users
and items, Pydantic v2 schemas, CORS, structured logging, dotenv config, a
pytest suite, and Docker support.

---

## Contents

- [Architecture](#architecture)
- [Project structure](#project-structure)
- [Local setup](#local-setup)
- [Docker setup](#docker-setup)
- [Environment variables](#environment-variables)
- [API reference](#api-reference)
- [Running tests](#running-tests)
- [Contributing](#contributing)

---

## Architecture

Each HTTP request passes through the following layers:

```
HTTP request
     │
     ▼
 main.py ── CORS middleware
     │   └─ global exception handler (→ 500 JSON)
     ▼
 Router  ── Pydantic input validation (→ 422 on failure)
     │       routers/users.py  |  routers/items.py
     ▼
 crud.py ── SQLAlchemy ORM queries
     │
     ▼
 SQLite  ── app.db (file) or :memory: (tests)
```

**Key design decisions:**

- **Flat module layout** — `config`, `database`, `models`, `schemas`, and `crud`
  are top-level modules; routers live in `routers/`. No unnecessary nesting.
- **Dependency injection** — `get_db` is a FastAPI dependency. Tests override it
  with an in-memory session; no mocking required.
- **No ORM relationships in responses** — response schemas are flat Pydantic
  models. Relationship data is fetched explicitly if needed, keeping serialization
  predictable.
- **Cascade deletes** — deleting a `User` automatically deletes their `Item`
  records via SQLAlchemy's `cascade="all, delete-orphan"`.

---

## Project structure

```
fastapi-starter-kit/
├── main.py              # App entry: CORS, logging, routers, error handler
├── config.py            # Env config (python-dotenv)
├── database.py          # SQLAlchemy engine, SessionLocal, Base, get_db
├── models.py            # ORM models: User, Item
├── schemas.py           # Pydantic schemas: Create / Update / Response
├── crud.py              # All database operations
├── routers/
│   ├── users.py         # /users endpoints
│   └── items.py         # /items endpoints
├── tests/
│   ├── conftest.py      # Fixtures: in-memory DB, client, seeded data
│   ├── test_health.py
│   ├── test_users.py
│   └── test_items.py
├── .env.example         # Copy to .env before first run
├── .github/
│   └── workflows/
│       └── ci.yml       # CI: ruff lint+format, pytest, Docker build
├── Dockerfile
├── docker-compose.yml
├── pytest.ini
└── requirements.txt
```

---

## Local setup

**Requirements:** Python 3.12+

```bash
# 1. Create and activate a virtual environment
python -m venv .venv
source .venv/bin/activate        # Windows: .venv\Scripts\activate

# 2. Install dependencies
pip install -r requirements.txt

# 3. Configure environment
cp .env.example .env             # edit values as needed

# 4. Start the dev server (auto-reload on file changes)
uvicorn main:app --reload
```

The server starts at `http://localhost:8000`. The SQLite database (`app.db`) is
created automatically on the first request.

Interactive docs:

| URL | Interface |
|-----|-----------|
| `http://localhost:8000/docs` | Swagger UI |
| `http://localhost:8000/redoc` | ReDoc |

---

## Docker setup

**Requirements:** Docker 24+ with the Compose plugin

```bash
# 1. Configure environment
cp .env.example .env             # edit values as needed

# 2. Build and start
docker compose up --build

# 3. Stop and remove containers (data volume is preserved)
docker compose down
```

The app is available at `http://localhost:8000`. The SQLite database is stored in
a named Docker volume (`db-data`) mounted at `/app/data` inside the container, so
data persists across container restarts and rebuilds.

To wipe the database volume:

```bash
docker compose down -v
```

**Healthcheck** — Docker polls `GET /health` every 30 s (3 retries, 10 s start
period). The container is marked `healthy` once the endpoint returns 200.

---

## Environment variables

Copy `.env.example` to `.env` and adjust as needed. All variables have defaults
so the app starts without a `.env` file.

| Variable | Default | Description |
|----------|---------|-------------|
| `DATABASE_URL` | `sqlite:///./app.db` | SQLAlchemy connection string |
| `ALLOWED_ORIGINS` | `http://localhost:3000` | Comma-separated list of CORS origins |
| `LOG_LEVEL` | `INFO` | Logging verbosity: `DEBUG` `INFO` `WARNING` `ERROR` |

---

## API reference

### Health

#### `GET /health`

```
HTTP/1.1 200 OK

{"status": "ok"}
```

---

### Users

#### `GET /users/`

Returns a paginated list of users.

| Query param | Default | Description |
|-------------|---------|-------------|
| `skip` | `0` | Records to skip |
| `limit` | `100` | Max records to return |

```
HTTP/1.1 200 OK

[
  {
    "id": 1,
    "name": "Alice",
    "email": "alice@example.com",
    "is_active": true,
    "created_at": "2026-04-10T12:00:00Z"
  }
]
```

#### `GET /users/{id}`

```
HTTP/1.1 200 OK        → user object
HTTP/1.1 404 Not Found → {"detail": "User not found"}
```

#### `POST /users/`

```json
{"name": "Alice", "email": "alice@example.com"}
```

```
HTTP/1.1 201 Created   → user object
HTTP/1.1 409 Conflict  → {"detail": "Email already registered"}
HTTP/1.1 422           → validation error detail
```

#### `PUT /users/{id}`

All fields are optional. Only supplied fields are updated.

```json
{"name": "Alicia", "email": "alicia@example.com", "is_active": false}
```

```
HTTP/1.1 200 OK        → updated user object
HTTP/1.1 404 Not Found → {"detail": "User not found"}
```

#### `DELETE /users/{id}`

Cascades — also deletes all items owned by this user.

```
HTTP/1.1 204 No Content
HTTP/1.1 404 Not Found → {"detail": "User not found"}
```

---

### Items

#### `GET /items/`

| Query param | Default | Description |
|-------------|---------|-------------|
| `skip` | `0` | Records to skip |
| `limit` | `100` | Max records to return |

```
HTTP/1.1 200 OK

[
  {
    "id": 1,
    "title": "Widget",
    "description": "A fine widget",
    "owner_id": 1
  }
]
```

#### `GET /items/{id}`

```
HTTP/1.1 200 OK        → item object
HTTP/1.1 404 Not Found → {"detail": "Item not found"}
```

#### `POST /items/`

`owner_id` must reference an existing user.

```json
{"title": "Widget", "description": "A fine widget", "owner_id": 1}
```

```
HTTP/1.1 201 Created   → item object
HTTP/1.1 404 Not Found → {"detail": "Owner user not found"}
HTTP/1.1 422           → validation error detail
```

#### `PUT /items/{id}`

All fields are optional. Pass `"description": null` to clear it.

```json
{"title": "Updated Widget", "description": null}
```

```
HTTP/1.1 200 OK        → updated item object
HTTP/1.1 404 Not Found → {"detail": "Item not found"}
```

#### `DELETE /items/{id}`

Does not affect the owning user.

```
HTTP/1.1 204 No Content
HTTP/1.1 404 Not Found → {"detail": "Item not found"}
```

---

## Running tests

```bash
pytest -v
```

The test suite uses an in-memory SQLite database (via `StaticPool`) and
`httpx.AsyncClient` — no running server or external services required. Each test
function starts with a clean database.

```bash
pytest -v -k "TestCreateUser"    # run a single class
pytest -v --tb=short             # compact tracebacks
```

To run lint and format checks locally (same checks as CI):

```bash
ruff check .
ruff format --check .
```

---

## Contributing

See [CONTRIBUTING.md](CONTRIBUTING.md) for the development workflow, code style
guide, and pull request process.

For security issues, see [SECURITY.md](SECURITY.md).
