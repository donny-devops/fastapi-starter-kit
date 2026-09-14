# Platform Baseline

This document defines the intended infrastructure, data, container, and policy posture for `fastapi-starter-kit`.

## Current implementation

| Capability | Status | Notes |
| --- | --- | --- |
| FastAPI service | Implemented | `main.py` exposes the application and health endpoint. |
| SQLite | Implemented | Persistence uses the Python `sqlite3` stdlib driver. Schema is created at startup. |
| PostgreSQL | Out of scope for the app runtime | This starter does not speak PostgreSQL. Use SQLite via `SQLITE_PATH` or a `sqlite:///` `DATABASE_URL`. |
| Docker | Implemented | `Dockerfile` builds and runs the API container. |
| AWS | Recommended deployment target | Use ECS Fargate or App Runner for the API, with RDS PostgreSQL for persistence. |
| Terraform | Recommended for production | Use Terraform to provision networking, IAM, ECS/App Runner, RDS, logging, and secrets. |
| Supabase | Optional | Only use Supabase when a managed Postgres + auth/dashboard workflow is preferred over AWS RDS. Do not enable both Supabase and RDS for the same environment without a clear migration plan. |

## Recommended production path

```text
Client -> Cloudflare Worker (optional) -> FastAPI container -> SQLite volume
                                        -> CloudWatch logs / metrics
```

## Required environment variables

```text
SQLITE_PATH=/app/data/app.db
ALLOWED_ORIGINS=https://example.com
LOG_LEVEL=INFO
RATE_LIMIT_PER_MINUTE=50000
```

Secrets must be supplied by a secrets manager or protected environment variables. Do not commit `.env` files.

## AWS baseline

Recommended AWS components:

- VPC with private subnets for database resources
- ECS Fargate or App Runner for the API container
- RDS PostgreSQL is **not** required by this starter; persist SQLite on a volume or EFS if you stay on sqlite3. PostgreSQL remains an option only if you replace the driver.
- Secrets Manager or SSM Parameter Store for credentials
- CloudWatch Logs for application logs
- IAM roles with least privilege
- GitHub Actions OIDC for deployments; avoid long-lived AWS access keys

## PostgreSQL baseline

This starter ships SQLite only. A PostgreSQL cutover would mean replacing `database.py` / `crud.py`, not flipping `DATABASE_URL`. If you later adopt PostgreSQL:

- TLS required where supported
- automated backups enabled
- least-privilege application user
- migrations run as a separate controlled step
- no default/admin database credentials in application runtime

## Docker baseline

Container requirements:

- no secrets baked into the image
- non-root runtime user where practical
- deterministic dependency installation
- health endpoint available for orchestration
- minimal production dependencies

## Terraform baseline

Terraform should live in a dedicated `infra/` directory or separate infrastructure repository. Recommended modules:

```text
infra/
  environments/dev/
  environments/prod/
  modules/api-service/
  modules/postgres/
  modules/networking/
```

Terraform state must be remote and encrypted. Never commit local state files.

## Policy checks

Required controls:

- CI must run lint/tests/build where applicable.
- Security hygiene workflow must block obvious private keys and tokens.
- Dependency updates must be reviewed before merge.
- `main` should require pull requests and passing checks before merge.
