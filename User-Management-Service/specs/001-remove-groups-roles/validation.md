# Implementation validation

Authority: constitution 3.0.0 and plan.md. All three stories are implemented.
No existing database was used as a migration or validation target.

## Initial review (T001)

The working tree was clean. No AGENTS.md or extension hooks were present.
The requirements checklist passed (16/16). Typing gaps included blanket
`mypy: ignore-errors`, untyped JWT dictionaries, fixtures, factories, session
generators and broker pools. Lifecycle ports depended on infrastructure library
types from application; they now live in infrastructure/interfaces.py and are
used only by adapters and composition. Application and domain have no framework
or infrastructure imports. No typing or DDD exceptions are requested or accepted.

Retained endpoints: POST auth/signup, auth/login, auth/refresh-token,
auth/reset-password; GET/PATCH/DELETE users/me; POST/GET/DELETE users/me/image
(all under /api/v1), plus the existing /healthcheck operational route.

## Implementation checkpoints

- T001–T003: pinned mypy/Ruff/stubs, refreshed lock, strict checking with Pydantic
  plugin, disposable compose data/ports and ignore files.
- T004–T014: removed all obsolete consumers, exports, fields, tables, revisions,
  bootstrap and behavior tests as one dependency batch; adapted retained callers
  and typed ordinary-user fixtures. Only one users baseline remains.
- T015–T016: application import/test collection succeeded (87 tests at this stage);
  all 19 domain tests passed. The baseline applied on fresh SQLite and subsequently
  on fresh PostgreSQL schemas. PasswordHash/ID retain their existing typed-wrapper
  behavior; no extra validation rules were introduced. UUID parsing at the JWT
  boundary rejects invalid subjects.
- T017–T023: registration/login/reset/session tests written before provider jti
  completion. Initial run: 9 failures, 24 passes; failures exposed absent jti and
  transaction cleanup on conflicts. Both fixed. Unit plus auth run: 70 passed.
  Deterministic frozen-clock tests verify different refresh tokens within one
  second; replay rejection leaves replacement usable.
- T024–T031: unit and HTTP ownership/image tests cover all six self operations,
  foreign IDs/keys, empty patches, conflicts, invalid/deleted subjects, storage
  failures, replacement, MIME and exactly/over 5 MiB limits. Initial HTTP failures
  exposed endpoint-only error handling in fastapi-error-map. Global typed FastAPI
  exception handlers now also cover dependencies and preserve standard
  HTTPException handling. The unused dependency was removed. Final profile/image
  run at this stage: 31 passed.
- T032–T036: removed-route and OpenAPI assertions, schema/mapping/constraints tests,
  source audit, current installation/API documentation and constitution assumption.
- T037: production Dockerfile built; scripts/entry.sh applied users_only_20260926
  and launched Uvicorn without any bootstrap settings. Compose application and
  all three services were healthy. PostgreSQL query before signup returned 0 users.
  Network startup acceptance test passed: ordinary A/B signup/login, own profile
  and update, unknown foreign fields, two refresh rotations/replay, removed route,
  password-reset publication, own deletion and zero users again.

## Execution environment

Python 3.12.14 on Windows. Docker Desktop 4.91.0 was installed outside PATH at
C:/Users/yomi/AppData/Local/Programs/DockerDesktop/resources/bin/docker.exe.
WSL Ubuntu had no Docker integration; the Windows client reached desktop-linux.
Disposable project: ums-users-only-codex; PostgreSQL 16, Redis 7, RabbitMQ 4.
Ports: 5434, 6380, 5673, 15673, application 8001.

The test example supplies disposable credentials only. PostgreSQL HTTP/schema tests
create random schemas and delete only those schemas. Redis verification deletes
only test subject keys and checks TTL/replay. RabbitMQ verification consumes actual
published messages in uniquely named test queues and deletes only those queues. S3 is intentionally
replaced by typed storage fakes as required by the plan; no remote bucket was used.

Commands (Windows used the absolute Docker executable above):
```powershell
uv sync
uv run pytest --collect-only tests
uv run pytest tests/unit/domain_invariants_test.py
docker compose --env-file .env.test -p ums-users-only-codex -f docker-compose.test.yaml up -d --wait
$env:UMS_TEST_POSTGRES_URL = "postgresql+asyncpg://postgres:disposable@localhost:5434/ums_test"
$env:UMS_TEST_REDIS_URL = "redis://:disposable@localhost:6380/0"
$env:UMS_TEST_BROKER_URL = "amqp://test:disposable@localhost:5673/"
uv run pytest tests/integration -q --tb=short
docker compose --env-file .env.test -p ums-users-only-codex -f docker-compose.test.yaml --profile startup up -d --build --wait
docker compose --env-file .env.test -p ums-users-only-codex -f docker-compose.test.yaml exec -T postgres_test psql -U postgres -d ums_test -c "select count(*) from users;"
$env:UMS_TEST_APP_URL = "http://localhost:8001"
uv run pytest tests/integration/settings/startup_test.py -q --tb=short
```

Observed before the final gates: PostgreSQL/Redis/RabbitMQ integration suite:
70 passed; startup acceptance: 1 passed; strict mypy: no issues in 130 files.
Earlier mypy findings were fixed, with no blanket or specific suppression added.

## Removed-concept audit (T035)

Command: `rg -n -i 'group|role|block|super.?user|super_admin|pagination|get_users' source scripts tests .env.example Dockerfile`.

Every remaining match is confined to the following:
| Location | Rationale |
|---|---|
| Dockerfile (groupadd/appgroup/chown) | Linux runtime group for the non-root process; unrelated to the domain. |
| tests/integration/group_tests/removed_groups_test.py | Old route absence and no side-effect assertions only. |
| tests/integration/user_tests/removed_operations_test.py | Old route/schema absence assertions and negative request inputs. |
| tests/integration/user_tests/edit_current_user_test.py | Ignored legacy input and foreign-target/key regression. |
| tests/integration/auth_tests/signup_user_test.py | Ignored legacy signup input regression. |
| tests/integration/settings/startup_test.py | Absence assertions against the running container's OpenAPI. |

There are zero matches in source/, scripts/ or .env.example. There are no
`Any` annotations, type ignores, mypy suppression or old executable migrations.
Historical feature documentation names removed concepts to explain scope.
The checklist was read only and its markers were not changed.

## Requirements traceability (T041)

| Requirement | Evidence |
|---|---|
| FR-001 | Group modules removed; removed_groups_test covers former CRUD/membership methods and unchanged profile. |
| FR-002 | Entity/DTO/ORM/ports/JWT simplified; exact OpenAPI, response and claim tests. |
| FR-003 | Auth HTTP tests, registration/login/refresh/publisher units and real_services_test. |
| FR-004 | Subject-only signatures; foreign IDs/keys and removed_operations_test verify both accounts unchanged. |
| FR-005 | Profile/image unit and HTTP lifecycle tests for all six own operations. |
| FR-006 | Exact response/input field and OpenAPI assertions; ignored legacy fields cannot change state. |
| FR-007 | Existing/deleted/invalid/expired subject tests; exact JWT payloads, jti uniqueness and real Redis replay checks. |
| FR-008 | Runtime/source/export/settings audit above; obsolete fixtures/tests deleted. |
| FR-009 | Bootstrap script/settings deleted; entry.sh performs only migration/exec; container starts without bootstrap environment. |
| FR-010 | fresh_schema_test checks exact fields, unique constraints, indexes, no foreign keys, only users/alembic_version. |
| FR-011 | Both absence suites require normal 404, no disclosure or mutation, and exact OpenAPI surface. |
| FR-012 | Fresh random PostgreSQL schemas plus disposable default compose schema; no upgrade/stamp/data migration. |
| FR-013 | Single down_revision=None baseline creates only final schema. |
| FR-014 | Protected-route missing/malformed/expired/deleted-session tests; refresh requires bearer presence and a valid refresh cookie. |
| FR-015 | README/quickstart describe retained API/fresh install; old behavior tests replaced by absence/error/ownership checks. |
| SC-001 | Auth HTTP/unit tests and production-container signup/login/refresh/reset acceptance. |
| SC-002 | Exact signup/profile/edit/delete/token shapes and OpenAPI/schema assertions. |
| SC-003 | Removed group/list/arbitrary profile/image/role/block methods return 404 without state changes. |
| SC-004 | Two-user tests, ignored foreign IDs/storage keys, subject-only ports and signatures. |
| SC-005 | Success/error profile/image tests, format/size boundary tests and mapped storage failures. |
| SC-006 | Baseline/schema zero-row assertions, ordinary first signup, container SQL count=0 before signup. |
| SC-007 | Healthy production container and normal first signup without bootstrap variables or script. |

No feature-scope deviations remain. Extra fixes are directly required to make the
retained contract work: unique refresh identifiers, complete error handling,
transaction cleanup, typed UTC mapping and bounded upload reads. The API is
intentionally incompatible with old installations; no migration is offered.

## Final gates (T038–T040)

| Check | Final result |
|---|---|
| uv run ruff check source tests scripts | PASS — all checks passed |
| uv run ruff format --check source tests scripts | PASS — 131 files already formatted |
| uv run mypy source tests scripts | PASS — no issues in 131 files, strict mode, no suppressions/exceptions |
| uv run pytest tests/unit -q | PASS — 50 tests, no services required |
| uv run pytest tests/unit tests/integration --cov=source --cov-report=term-missing:skip-covered -q --tb=short | PASS — 122 tests, no skips, on PostgreSQL/Redis/RabbitMQ and running production container |
| Coverage | 85% source overall; 96% user use cases; 94% JWT provider; auth/user routes 97%/95% |
| Fresh baseline / container | PASS — production build and entry.sh, healthy services, zero users before first signup, startup acceptance |
| git diff --check | PASS |
| Quickstart acceptance 1–8 and targeted regressions | PASS — covered by schema/auth/profile/image/absence/real-services/startup tests |
| Extension hooks | No .specify/extensions.yml before or after implementation; nothing to dispatch |

No numeric minimum coverage is defined in the project/specification. Required
success, significant-error and ownership scenarios are covered. Lifecycle and
production startup execute in the separate container, so they are not counted in
the host pytest coverage measurement; S3 operations intentionally use storage
fakes. These are verification boundaries, not typing/DDD exceptions.

All tasks T001–T041 are completed and marked [X]. Final source matches FR-001–FR-015
and SC-001–SC-007; no maintainer exception or unresolved gate remains.

The first complete rerun found one test-isolation failure (71 passes): a prior
container password-reset message was still in the normal reset queue. The broker
test now routes its in-process HTTP request to its own random queue with a
test-local monkeypatch, then deletes only that queue and its DLQ. The production
container and its queues are unaffected. The corrected real-service tests both
passed.

The test compose application is intentionally left running at localhost:8001
for the user's request to deploy via Docker Compose. Quickstart teardown is
documented but not executed on this final run so the user can inspect the result;
all acceptance checks are executed. Data remains disposable (tmpfs). Teardown:
docker compose --env-file .env.test -p ums-users-only-codex -f docker-compose.test.yaml --profile startup down -v
