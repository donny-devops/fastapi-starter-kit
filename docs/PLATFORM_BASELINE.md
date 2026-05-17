# Platform Baseline

This document defines the intended infrastructure, data, container, and policy posture for `fastapi-starter-kit`.

## Current implementation

| Capability | Status | Notes |
| --- | --- | --- |
| FastAPI service | Implemented | `main.py` exposes the application and health endpoint. |
| PostgreSQL compatibility | Planned / deployment-ready | The starter currently defaults to SQLite for local development; production deployments should use PostgreSQL via `DATABASE_URL`. |
| Docker | Implemented | `Dockerfile` builds and runs the API container. |
| AWS | Recommended deployment target | Use ECS Fargate or App Runner for the API, with RDS PostgreSQL for persistence. |
| Terraform | Recommended for production | Use Terraform to provision networking, IAM, ECS/App Runner, RDS, logging, and secrets. |
| Supabase | Optional | Only use Supabase when a managed Postgres + auth/dashboard workflow is preferred over AWS RDS. Do not enable both Supabase and RDS for the same environment without a clear migration plan. |

## Recommended production path

```text
Client -> HTTPS Load Balancer / App Runner -> FastAPI container -> PostgreSQL
                                        -> CloudWatch logs / metrics
```

## Required environment variables

```text
DATABASE_URL=postgresql+psycopg://<user>:<password>@<host>:5432/<database>
ALLOWED_ORIGINS=https://example.com
LOG_LEVEL=INFO
```

Secrets must be supplied by a secrets manager or protected environment variables. Do not commit `.env` files.

## AWS baseline

Recommended AWS components:

- VPC with private subnets for database resources
- ECS Fargate or App Runner for the API container
- RDS PostgreSQL for production data
- Secrets Manager or SSM Parameter Store for credentials
- CloudWatch Logs for application logs
- IAM roles with least privilege
- GitHub Actions OIDC for deployments; avoid long-lived AWS access keys

## PostgreSQL baseline

Production PostgreSQL requirements:

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
