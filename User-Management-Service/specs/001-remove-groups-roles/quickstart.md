# Quickstart Validation: Users-Only Service

This guide validates the design against a fresh database and disposable dependencies. It does
not migrate or delete an existing database.

## Prerequisites

- Use the repository's supported Python 3.12 environment (`requires-python` is `>=3.12, <3.13`).
- Install locked dependencies with `uv sync`.
- Provide a test environment file with PostgreSQL, Redis, RabbitMQ, JWT, and storage settings.
- Use a disposable compose project and temporary data. Do not reuse production volumes.

Copy `.env.test.example` to `.env.test`. Host port defaults are PostgreSQL 5434,
Redis 6380, RabbitMQ 5673 and management 15673; override `TEST_POSTGRES_PORT`,
`TEST_REDIS_PORT`, `TEST_BROKER_PORT`, `TEST_BROKER_MANAGEMENT_PORT` for another run.
Set `UMS_TEST_POSTGRES_URL`, `UMS_TEST_REDIS_URL`, `UMS_TEST_BROKER_URL` to matching
localhost URLs when running the real-service tests. Every compose project has
temporary PostgreSQL, Redis and RabbitMQ data and no fixed container names.

## Static and unit checks

From the repository root:

```powershell
uv run ruff check source tests scripts
uv run ruff format --check source tests scripts
uv run mypy source tests scripts
uv run pytest tests/unit
```

Expected result: retained code passes formatting/lint/type checks and unit tests; no test
fixture imports a group, role, block-state, or super-user concept.

Before a story checkpoint, collect tests with `uv run pytest --collect-only tests` using
the isolated test configuration. The foundational change must already remove obsolete
router registration, consumers and exports together with their deleted dependencies.

Unit verification must exercise domain validation and retained profile/image use cases with
typed fake ports, including ownership, missing users/images, and storage failures. It must
not require real PostgreSQL, Redis, RabbitMQ, S3, or an HTTP server. See the coverage matrix
in [plan.md](plan.md) and the rules in [data-model.md](data-model.md).

## Fresh database and integration checks

Start only disposable test services using the project's test compose definition (or its isolated
equivalent), then run:

```powershell
docker compose --env-file .env.test -p ums-users-only -f docker-compose.test.yaml up -d --wait
$env:UMS_TEST_POSTGRES_URL = "postgresql+asyncpg://postgres:disposable@localhost:5434/ums_test"
$env:UMS_TEST_REDIS_URL = "redis://:disposable@localhost:6380/0"
$env:UMS_TEST_BROKER_URL = "amqp://test:disposable@localhost:5673/"
uv run pytest tests/integration
docker compose --env-file .env.test -p ums-users-only -f docker-compose.test.yaml --profile startup up -d --build --wait
Invoke-RestMethod http://localhost:8001/healthcheck
$env:UMS_TEST_APP_URL = "http://localhost:8001"
uv run pytest tests/integration/settings/startup_test.py
docker compose --env-file .env.test -p ums-users-only -f docker-compose.test.yaml --profile startup down -v
```

If Docker is unavailable, the same suite can run against equivalent local services configured
through the test environment. The implementation must document the actual service setup used.

## Required acceptance checks

1. Apply the users-only Alembic baseline to an empty PostgreSQL database. Confirm the schema
   has only the `users` business table, with `alembic_version` allowed as migration metadata,
   and no groups table, role enum, group foreign key, or blocking column. Assert zero users
   before the first registration, then verify approved columns, indexes, and constraints.
2. Register a user and confirm `201`; response and database row contain no role, group, or
   blocking field.
3. Log in and inspect the access token claims. Confirm `sub`, `email`, and `exp` only; refresh
   remains in an HttpOnly cookie with `sub`, `exp`, and a unique `jti`, and no removed claim.
4. Refresh once, confirm token rotation/blacklisting remains functional, then reject a replayed
   refresh token according to the existing error map. Repeat with a fixed clock in the same
   second: the replacement must differ and itself remain usable for the next refresh.
5. Call `GET/PATCH/DELETE /api/v1/users/me` with a valid token. Confirm only the authenticated
   account is read or changed and `PATCH` ignores unknown `image_s3_path` input without
   changing the stored key. Apply the same assertion to a supplied foreign user ID.
6. Upload, retrieve, and delete the authenticated user's own image. Confirm MIME and 5 MiB
   limits and that storage failures use the existing error responses.
7. Attempt old group, role, block, list, and arbitrary-user paths. Confirm they are absent from
   OpenAPI and return the normal missing-route response with no state changes.
8. Start from the empty database without super-user environment variables or bootstrap scripts.
   Confirm the service starts and the first user is created only through registration.

## Targeted regression cases

- Two users: a token for A cannot read, update, delete, upload for, retrieve, or delete the
  image of B. Passing B's ID to a self route cannot change the operation target.
- A profile update cannot assign an S3 key belonging to B.
- Missing, deleted, expired, malformed, and revoked tokens do not create or resurrect a user.
- Duplicate username/email/phone and invalid domain values preserve existing conflict/validation
  behavior.
- Old role/group/block fields in request payloads do not create state or permissions.

Record the actual Ruff, strict mypy, pytest and acceptance results. A failed or unexecuted
check is not a pass. Typing/DDD exceptions require a maintainer decision with reason, scope,
owner and exit condition, per constitution 3.0.0. All three stories are required for release.

Without UMS_TEST_* URLs, HTTP tests use a fresh migrated SQLite database with
storage/cache/publisher fakes; two real-service checks are explicitly skipped.
With UMS_TEST_POSTGRES_URL every HTTP/schema test uses its own random PostgreSQL
schema. Only that schema is removed afterwards. Real Redis tests remove only their
subject-specific keys. RabbitMQ tests use the disposable broker and remove the
test and password-reset queues.

The startup compose profile runs the production Dockerfile and scripts/entry.sh
against the untouched default test schema, on port TEST_APP_PORT (default 8001).
Its test credentials match .env.test.example. Before signup verify zero users:
docker compose --env-file .env.test -p ums-users-only -f docker-compose.test.yaml exec -T postgres_test psql -U postgres -d ums_test -c "select count(*) from users;"
Then register through POST /api/v1/auth/signup. This check is independent of the
random schemas used by pytest. All data disappears when the disposable project
is taken down.
