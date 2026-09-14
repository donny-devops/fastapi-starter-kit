# Copilot Code Review Instructions — FastAPI Starter Kit

## Security-First Review Standards

This starter uses stdlib `sqlite3`, optional GitHub session OAuth, and an
origin rate limiter. `/users` and `/items` CRUD is **intentionally public**
unless a later auth PR lands. Do not flag missing JWT/`get_current_user` on
those routes as a defect.

### 1. API Security (CRITICAL)
- **Authentication/Authorization**
  - GitHub OAuth (`routers/auth_github.py`) is optional and session-based
  - Flag OAuth callbacks that skip `state` validation
  - Flag responses or logs that include GitHub access tokens or upstream bodies
  - `GET /auth/me` must 401 when no `github_user` is in the session
  - Do not require JWT, RBAC, or `Depends(get_current_user)` on CRUD
- **Input Validation**
  - All Pydantic models should have proper validators
  - Check for SQL injection risks in raw queries
  - Verify file upload size limits and type validation
  - Flag missing input sanitization on user-provided data
- **Rate Limiting**
  - Origin limiter in `main.py` (`rate_limit.py`) must remain on mutating and
    data routes; `/health` and `/ready` stay excluded
  - Verify sensitive endpoints (OAuth login/callback) are not exempted unless
    documented

### 2. Database Security
- **sqlite3 Best Practices**
  - Use parameterized queries (`?` placeholders), never string-concatenate user input into SQL
  - Column names in dynamic UPDATE statements must come from a server-side allowlist
  - Enable `PRAGMA foreign_keys = ON` on every connection
  - Verify the database path comes from environment variables
- **Schema**
  - Table DDL lives in `database.py` (`init_db()` / `SCHEMA`)
  - Check for data loss risks in schema changes
  - Verify schema changes are covered by tests

### 3. Async/Await Patterns
- Flag blocking I/O in async functions (requests, time.sleep)
- Verify proper use of `await` with async I/O
- Check for missing `async with` context managers
- Ensure background tasks don't block event loop

### 4. Docker & Deployment Security
- **Dockerfile**
  - Base images should use specific tags with digests (not `:latest`)
  - Run as non-root user (`USER appuser`)
  - Multi-stage builds to minimize attack surface
  - No secrets in environment variables or layers
- **docker-compose.yml**
  - `SECRET_KEY` must be required when `APP_ENV=production`
  - Check for exposed ports that should be internal only
  - Verify health checks hit `/ready` (DB ping), not only `/health`

### 5. Testing & Coverage
- New routes MUST have corresponding tests in `tests/`
- Check for proper test isolation (rollback after each test)
- Verify edge cases: invalid input, unauthenticated `/auth/me`, rate limits
- Flag missing exception handling tests

### 6. Dependencies
- `requirements.txt` or `pyproject.toml` should pin exact versions
- Flag known vulnerable packages (check CVE databases)
- Verify dev dependencies are separate from production

### 7. Logging & Error Handling
- Never log sensitive data (passwords, tokens, PII)
- Use structured logging (JSON format preferred)
- Error responses should not leak stack traces or upstream OAuth bodies
- Check for proper exception handling in route handlers

## Code Quality Standards
- Type hints required on all function signatures
- Docstrings required for all public functions/classes
- Follow PEP 8 (use ruff for linting)
- Avoid nested ternary operators (max 1 level deep)

## Response Format
```
**[SEVERITY]**: API Security - OAuth state missing

**Location**: `routers/auth_github.py:58`
**Problem**: GitHub callback accepts `code` without comparing `state` to the session value
**Risk**: CSRF against the OAuth callback can bind another user's GitHub identity
**Fix**:
\```python
expected_state = request.session.pop("oauth_state", None)
if not expected_state or state != expected_state:
    raise HTTPException(status_code=400, detail="Invalid or expired OAuth state")
\```
```

Severity: CRITICAL | HIGH | MEDIUM | LOW | ADVISORY
