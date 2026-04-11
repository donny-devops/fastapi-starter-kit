# API Authentication — Proposed Design

> **Status: proposed design, not yet implemented.**
>
> The starter kit currently exposes every endpoint publicly. No authentication
> code, password field, or JWT configuration ships in the repository today.
> This document describes a recommended design you can apply yourself in a
> follow-up change. Every file path below points to the existing module the
> proposed change would extend.

The recommended scheme is the **OAuth2 password flow** issuing short-lived JWT
access tokens. Clients send the token in an `Authorization: Bearer <token>`
header, and FastAPI's dependency system validates it on every protected
request.

---

## Contents

- [Design goals](#design-goals)
- [Required dependencies](#required-dependencies)
- [New environment variables](#new-environment-variables)
- [Model changes](#model-changes)
- [Schema additions](#schema-additions)
- [New module: `auth.py`](#new-module-authpy)
- [New router: `routers/auth.py`](#new-router-routersauthpy)
- [Protecting existing endpoints](#protecting-existing-endpoints)
- [API reference](#api-reference)
- [Client examples](#client-examples)
- [Testing notes](#testing-notes)
- [Security checklist](#security-checklist)

---

## Design goals

The design is intentionally small so it drops cleanly into the existing
codebase:

- **Fit the flat module layout** — a single new top-level `auth.py` alongside
  `config.py`, `database.py`, `models.py`, `schemas.py`, and `crud.py`. No
  new package directories.
- **Reuse the `get_db` dependency** already defined in
  [`database.py`](../database.py) (line 13). The new `get_current_user`
  dependency composes with it, not alongside it.
- **Reuse the Pydantic v2 response style** from
  [`schemas.py`](../schemas.py) (see `UserResponse.model_config = {"from_attributes": True}`
  on line 28).
- **Reuse the `HTTPException` error shape** used throughout
  [`routers/users.py`](../routers/users.py) — `HTTPException(status_code=..., detail="...")`.
- **No breaking change to `UserResponse`** — the password hash lives only on
  the ORM model. Existing clients of `GET /users/` see the same payload.

---

## Required dependencies

Add the following to [`requirements.txt`](../requirements.txt):

```
python-jose[cryptography]==3.3.0
passlib[bcrypt]==1.7.4
python-multipart==0.0.20
```

| Package | Purpose |
|---|---|
| `python-jose[cryptography]` | JWT encode/decode with `cryptography` as the signing backend |
| `passlib[bcrypt]` | Password hashing and verification |
| `python-multipart` | Required by FastAPI's `OAuth2PasswordRequestForm` (form-encoded login body) |

---

## New environment variables

Extend the table in [`README.md`](../README.md#environment-variables) and the
loader in [`config.py`](../config.py) with four new variables:

| Variable | Default | Description |
|----------|---------|-------------|
| `JWT_SECRET` | *(required — no default)* | Signing key for access tokens. Do not reuse across environments. |
| `JWT_ALGORITHM` | `HS256` | JWT signing algorithm |
| `ACCESS_TOKEN_EXPIRE_MINUTES` | `30` | Access-token lifetime in minutes |
| `BCRYPT_ROUNDS` | `12` | Password hashing work factor |

Generate a strong `JWT_SECRET` with:

```bash
python -c "import secrets; print(secrets.token_urlsafe(32))"
```

Example `config.py` additions:

```python
JWT_SECRET: str = os.environ["JWT_SECRET"]  # fail fast if missing
JWT_ALGORITHM: str = os.getenv("JWT_ALGORITHM", "HS256")
ACCESS_TOKEN_EXPIRE_MINUTES: int = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "30"))
BCRYPT_ROUNDS: int = int(os.getenv("BCRYPT_ROUNDS", "12"))
```

---

## Model changes

Add one column to the `User` model in [`models.py`](../models.py) (line 6):

```python
class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    email = Column(String, unique=True, index=True, nullable=False)
    hashed_password = Column(String, nullable=False)   # <-- new
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    items = relationship("Item", back_populates="owner", cascade="all, delete-orphan")
```

`hashed_password` stores a `passlib` bcrypt hash and is never serialised back
to clients. Because this is a `NOT NULL` column, existing rows would violate
the constraint. The starter kit does not include Alembic, so the simplest path
in development is to delete `app.db` and let the app recreate the schema on
the next request (via `Base.metadata.create_all` in
[`main.py`](../main.py) line 21).

---

## Schema additions

Add the following to [`schemas.py`](../schemas.py) alongside the existing
`UserBase`, `UserCreate`, `UserUpdate`, and `UserResponse`:

```python
from typing import Literal
from pydantic import BaseModel, Field


class UserRegister(UserBase):
    password: str = Field(min_length=8)


class UserLogin(BaseModel):
    email: str
    password: str


class Token(BaseModel):
    access_token: str
    token_type: Literal["bearer"] = "bearer"


class TokenPayload(BaseModel):
    sub: str   # user id as string
    exp: int   # unix timestamp
```

`UserResponse` stays exactly as it is — no password fields are added, so
`GET /users/{id}` never leaks a hash.

---

## New module: `auth.py`

Create a new top-level `auth.py` (sibling to `config.py`, `crud.py`,
`database.py`). This module owns all cryptographic and token logic so routers
stay thin:

```python
# auth.py
from datetime import datetime, timedelta, timezone

from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError, jwt
from passlib.context import CryptContext
from sqlalchemy.orm import Session

import crud
from config import ACCESS_TOKEN_EXPIRE_MINUTES, JWT_ALGORITHM, JWT_SECRET, BCRYPT_ROUNDS
from database import get_db
from models import User
from schemas import TokenPayload

pwd_context = CryptContext(schemes=["bcrypt"], bcrypt__rounds=BCRYPT_ROUNDS)
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/login")


def hash_password(plain: str) -> str:
    return pwd_context.hash(plain)


def verify_password(plain: str, hashed: str) -> bool:
    return pwd_context.verify(plain, hashed)


def create_access_token(subject: str) -> str:
    expire = datetime.now(timezone.utc) + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    payload = {"sub": subject, "exp": int(expire.timestamp())}
    return jwt.encode(payload, JWT_SECRET, algorithm=JWT_ALGORITHM)


def decode_access_token(token: str) -> TokenPayload:
    try:
        raw = jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALGORITHM])
        return TokenPayload(**raw)
    except (JWTError, ValueError) as exc:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials",
            headers={"WWW-Authenticate": "Bearer"},
        ) from exc


def get_current_user(
    token: str = Depends(oauth2_scheme),
    db: Session = Depends(get_db),
) -> User:
    payload = decode_access_token(token)
    user = crud.get_user(db, int(payload.sub))
    if user is None or not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return user
```

The dependency chain is `oauth2_scheme → decode_access_token → crud.get_user`,
reusing the existing lookup function from [`crud.py`](../crud.py) (line 9).

---

## New router: `routers/auth.py`

Create a new router file mirroring the style of
[`routers/users.py`](../routers/users.py):

```python
# routers/auth.py
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session

import crud
from auth import create_access_token, get_current_user, hash_password, verify_password
from database import get_db
from models import User
from schemas import Token, UserRegister, UserResponse

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/register", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
def register(data: UserRegister, db: Session = Depends(get_db)):
    if crud.get_user_by_email(db, data.email):
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT, detail="Email already registered"
        )
    user = User(
        name=data.name,
        email=data.email,
        hashed_password=hash_password(data.password),
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


@router.post("/login", response_model=Token)
def login(
    form: OAuth2PasswordRequestForm = Depends(),
    db: Session = Depends(get_db),
):
    user = crud.get_user_by_email(db, form.username)   # form.username holds the email
    if user is None or not verify_password(form.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return Token(access_token=create_access_token(subject=str(user.id)))


@router.get("/me", response_model=UserResponse)
def me(current_user: User = Depends(get_current_user)):
    return current_user
```

Wire the new router into [`main.py`](../main.py) next to the existing two
includes on line 43:

```python
from routers import auth, items, users
...
app.include_router(auth.router)
app.include_router(users.router)
app.include_router(items.router)
```

Note that `POST /auth/register` bypasses `crud.create_user` so it can set
`hashed_password` directly. Alternatively, extend `crud.create_user` to accept
a pre-hashed password — either approach is fine.

---

## Protecting existing endpoints

Add `current_user: User = Depends(get_current_user)` to any handler that
should require authentication. For example, in
[`routers/items.py`](../routers/items.py) the `create_item` handler on line 29
currently takes `owner_id` from the request body:

```python
# Before — owner_id comes from the client (spoofable)
@router.post("/", response_model=ItemResponse, status_code=status.HTTP_201_CREATED)
def create_item(data: ItemCreate, db: Session = Depends(get_db)):
    if not crud.get_user(db, data.owner_id):
        raise HTTPException(status_code=404, detail="Owner user not found")
    return crud.create_item(db, data)
```

With auth, derive `owner_id` from the authenticated user instead — clients can
no longer create items on behalf of someone else:

```python
# After — owner_id comes from the token
from auth import get_current_user
from models import User

@router.post("/", response_model=ItemResponse, status_code=status.HTTP_201_CREATED)
def create_item(
    data: ItemCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return crud.create_item(db, data, owner_id=current_user.id)
```

This requires dropping `owner_id` from `ItemCreate` in
[`schemas.py`](../schemas.py) and adjusting `crud.create_item` to accept
`owner_id` as a keyword argument.

Apply the same `Depends(get_current_user)` to the `users` router handlers
that should be locked down (typically everything except registration).

---

## API reference

### Auth

#### `POST /auth/register`

Create a new user. The password is hashed with bcrypt before it is stored; the
response never includes it.

```json
{
  "name": "Alice",
  "email": "alice@example.com",
  "password": "correct-horse-battery-staple"
}
```

```
HTTP/1.1 201 Created   → user object
HTTP/1.1 409 Conflict  → {"detail": "Email already registered"}
HTTP/1.1 422           → validation error detail (e.g. password too short)
```

#### `POST /auth/login`

Exchange credentials for an access token. The request body is
**form-encoded** (`application/x-www-form-urlencoded`), not JSON, because the
handler uses FastAPI's `OAuth2PasswordRequestForm`. Send the email in the
`username` field.

```
username=alice@example.com&password=correct-horse-battery-staple
```

```
HTTP/1.1 200 OK

{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "token_type": "bearer"
}
```

```
HTTP/1.1 401 Unauthorized → {"detail": "Incorrect email or password"}
```

#### `GET /auth/me`

Return the authenticated user. Requires a valid `Authorization: Bearer ...`
header.

```
HTTP/1.1 200 OK        → user object
HTTP/1.1 401 Unauthorized → {"detail": "Could not validate credentials"}
```

### Authenticated endpoints

Any endpoint protected with `Depends(get_current_user)` expects the header:

```
Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
```

Missing or invalid tokens return one of:

```
HTTP/1.1 401 Unauthorized → {"detail": "Not authenticated"}
HTTP/1.1 401 Unauthorized → {"detail": "Could not validate credentials"}
```

The first response comes from FastAPI's `OAuth2PasswordBearer` when the
`Authorization` header is absent. The second comes from `decode_access_token`
when the header is present but the token is malformed, expired, or refers to
a user that no longer exists.

---

## Client examples

### curl

```bash
# 1. Register (one-time)
curl -X POST http://localhost:8000/auth/register \
  -H "Content-Type: application/json" \
  -d '{"name": "Alice", "email": "alice@example.com", "password": "s3cret-pass"}'

# 2. Log in — note: form-encoded, not JSON
TOKEN=$(curl -s -X POST http://localhost:8000/auth/login \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "username=alice@example.com&password=s3cret-pass" \
  | python -c "import json, sys; print(json.load(sys.stdin)['access_token'])")

# 3. Call a protected endpoint
curl http://localhost:8000/auth/me \
  -H "Authorization: Bearer $TOKEN"
```

### Python (httpx)

```python
import httpx

BASE = "http://localhost:8000"

with httpx.Client(base_url=BASE) as client:
    client.post("/auth/register", json={
        "name": "Alice",
        "email": "alice@example.com",
        "password": "s3cret-pass",
    })

    token = client.post(
        "/auth/login",
        data={"username": "alice@example.com", "password": "s3cret-pass"},
    ).json()["access_token"]

    me = client.get(
        "/auth/me",
        headers={"Authorization": f"Bearer {token}"},
    ).json()
    print(me)
```

---

## Testing notes

The existing test fixtures live in
[`tests/conftest.py`](../tests/conftest.py). The file already installs an
in-memory SQLite engine and overrides `get_db` via
`app.dependency_overrides[get_db]` on line 31, and wipes every table after each
test via the `clean_tables` autouse fixture (lines 37–43).

Add an `authenticated_client` fixture that registers a user, logs in, and
attaches the `Authorization` header to an `httpx.AsyncClient`:

```python
# tests/conftest.py (addition)
@pytest_asyncio.fixture
async def authenticated_client(client: AsyncClient) -> AsyncClient:
    await client.post("/auth/register", json={
        "name": "Test User",
        "email": "test@example.com",
        "password": "test-password-123",
    })
    resp = await client.post(
        "/auth/login",
        data={"username": "test@example.com", "password": "test-password-123"},
    )
    token = resp.json()["access_token"]
    client.headers["Authorization"] = f"Bearer {token}"
    return client
```

Set a deterministic `JWT_SECRET` in the test environment — either export it
before running `pytest`, or define it in `tests/conftest.py` before `from main
import app` runs so config initialisation sees a value:

```python
import os
os.environ.setdefault("JWT_SECRET", "test-secret-do-not-use-in-production")
```

---

## Security checklist

**Do:**

- Serve the API over HTTPS in production. Tokens in plaintext over HTTP are
  trivially captured.
- Keep `JWT_SECRET` out of version control. The starter kit's `.env.example`
  is a template; the real `.env` is gitignored.
- Rotate `JWT_SECRET` if you suspect it is compromised. Rotation invalidates
  every outstanding token — there is no denylist to maintain.
- Keep `ACCESS_TOKEN_EXPIRE_MINUTES` short (30 minutes or less). Shorter
  tokens limit the blast radius of a stolen header.
- Use a high-enough `BCRYPT_ROUNDS` value (12 is a reasonable 2026 default).
  Raise it as hardware gets faster.
- Rate-limit `POST /auth/login` at your reverse proxy or with a library like
  `slowapi` to slow down credential stuffing.

**Don't:**

- Log tokens, passwords, or password hashes. The global handler in
  [`main.py`](../main.py) on line 37 catches exceptions — make sure nothing
  in the auth path adds request bodies to the log context.
- Return `hashed_password` from any response schema. Keep it off
  `UserResponse` and every future read model.
- Accept JWTs from query strings or cookies unless you have a specific reason.
  Stick to the `Authorization` header.
- Reuse `JWT_SECRET` across environments (dev / staging / prod) — a leak in
  one environment should not unlock the others.

For reporting security issues in the starter kit itself, see
[`SECURITY.md`](../SECURITY.md) at the repository root.
