# Contributing

Thank you for taking the time to contribute.

## Getting started

1. **Fork** the repository and clone your fork.
2. Create a branch from `main`:
   ```bash
   git checkout -b feat/your-feature-name
   ```
3. Set up your environment:
   ```bash
   python -m venv .venv
   source .venv/bin/activate   # Windows: .venv\Scripts\activate
   pip install -r requirements.txt
   cp .env.example .env
   ```

## Code style

This project uses [ruff](https://docs.astral.sh/ruff/) for linting and formatting.

```bash
ruff check .          # show lint violations
ruff check --fix .    # auto-fix where possible
ruff format .         # reformat code
```

CI enforces both `ruff check` and `ruff format --check` — commits that fail
either check will not be merged.

## Running tests

```bash
pytest -v
```

Tests use an in-memory SQLite database and do not require a running server.
Add new tests in `tests/` alongside existing ones. All new endpoints and CRUD
functions should have corresponding test coverage.

## Commit messages

Use the conventional commits style:

```
<type>: <short summary>

[optional body]
```

Common types: `feat`, `fix`, `refactor`, `test`, `docs`, `chore`.

Examples:
```
feat: add pagination to /items endpoint
fix: return 409 instead of 500 on duplicate email
docs: add Docker setup to README
```

## Submitting a pull request

1. Make sure `ruff check .`, `ruff format --check .`, and `pytest -v` all pass locally.
2. Update `CHANGELOG.md` under `[Unreleased]` with a summary of your change.
3. Open a PR against `main`. Describe *what* changed and *why*.
4. A maintainer will review and may request changes. Please address feedback
   in new commits rather than force-pushing, so the review history is preserved.

## Reporting bugs

Open a GitHub issue with:
- A clear title and description
- Steps to reproduce
- Expected vs. actual behavior
- Python version and OS

For security issues, see [SECURITY.md](SECURITY.md) instead.
