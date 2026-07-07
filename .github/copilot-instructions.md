# Copilot Code Review Instructions — FastAPI Starter Kit

## Security-First Review Standards

### 1. API Security (CRITICAL)
- **Authentication/Authorization**
  - Verify JWT tokens are validated on protected endpoints
  - Check for proper role-based access control (RBAC)
  - Flag missing `Depends(get_current_user)` on protected routes
  - Ensure password hashing uses bcrypt/argon2, never plaintext
- **Input Validation**
  - All Pydantic models should have proper validators
  - Check for SQL injection risks in raw queries
  - Verify file upload size limits and type validation
  - Flag missing input sanitization on user-provided data
- **Rate Limiting**
  - Check that rate limiting middleware is applied
  - Verify sensitive endpoints (login, register) have stricter limits

### 2. Database Security
- **SQLAlchemy Best Practices**
  - Use parameterized queries, never string concatenation
  - Check for N+1 query issues (missing eager loading)
  - Verify database credentials use environment variables
  - Flag any hardcoded connection strings
- **Migrations**
  - Alembic migrations should be reversible (`downgrade()` implemented)
  - Check for data loss risks in schema changes
  - Verify migrations are tested before merge

### 3. Async/Await Patterns
- Flag blocking I/O in async functions (requests, time.sleep)
- Verify proper use of `await` with async database sessions
- Check for missing `async with` context managers
- Ensure background tasks don't block event loop

### 4. Docker & Deployment Security
- **Dockerfile**
  - Base images should use specific tags with digests (not `:latest`)
  - Run as non-root user (`USER appuser`)
  - Multi-stage builds to minimize attack surface
  - No secrets in environment variables or layers
- **docker-compose.yml**
  - Database passwords must use `_FILE` suffix or secrets
  - Check for exposed ports that should be internal only
  - Verify health checks are configured

### 5. Testing & Coverage
- New routes MUST have corresponding tests in `tests/`
- Check for proper test isolation (rollback after each test)
- Verify edge cases: invalid input, unauthorized access, rate limits
- Flag missing exception handling tests

### 6. Dependencies
- `requirements.txt` or `pyproject.toml` should pin exact versions
- Flag known vulnerable packages (check CVE databases)
- Verify dev dependencies are separate from production

### 7. Logging & Error Handling
- Never log sensitive data (passwords, tokens, PII)
- Use structured logging (JSON format preferred)
- Error responses should not leak stack traces in production
- Check for proper exception handling in route handlers

## Code Quality Standards
- Type hints required on all function signatures
- Docstrings required for all public functions/classes
- Follow PEP 8 (use ruff for linting)
- Avoid nested ternary operators (max 1 level deep)

## Response Format
```
**[SEVERITY]**: API Security - Missing Authentication

**Location**: `app/api/routes/users.py:45`
**Problem**: Endpoint `/api/users/{user_id}/delete` is missing authentication dependency
**Risk**: Unauthenticated users can delete any user account (CRITICAL vulnerability)
**Fix**: 
\```python
@router.delete("/{user_id}")
async def delete_user(
    user_id: int,
    current_user: User = Depends(get_current_active_user),  # Add this
    db: AsyncSession = Depends(get_db)
):
    if current_user.id != user_id and not current_user.is_superuser:
        raise HTTPException(status_code=403, detail="Not authorized")
    # ... rest of function
\```
```

Severity: CRITICAL | HIGH | MEDIUM | LOW | ADVISORY
