# Implementation Plan: Remove Groups, Roles, and Cross-User Operations

**Feature**: `001-remove-groups-roles` | **Git branch**: `fix/um` | **Date**: 2026-09-26 | **Spec**: [spec.md](spec.md)

**Input**: Feature specification from `specs/001-remove-groups-roles/spec.md`

## Summary

The service will become a self-service user account API. Registration, login, refresh,
password-reset requests, own-profile operations, and own-image operations remain. Groups,
membership, roles, blocking, super-user bootstrap, user listing, and arbitrary-user routes
are removed from source, schemas, persistence, fixtures, and documentation. The target is a
fresh users-only database; migration of an existing database is explicitly out of scope.

The design keeps the current domain/application/infrastructure/presentation boundaries.
Authentication tokens carry subject, expiry, access email or refresh `jti`; account operations
derive the target user from the authenticated subject. `image_s3_path` remains output-only;
profile updates cannot assign an arbitrary storage key.

## Technical Context

**Language/Version**: Python 3.12 (`>=3.12, <3.13`)

**Primary Dependencies**: FastAPI 0.135.1, Pydantic 2.12.5, SQLAlchemy asyncio 2.0.48,
  Alembic 1.18.4, asyncpg, PyJWT, Redis, aio-pika, aioboto3, pytest, pytest-asyncio, Ruff

**Storage**: PostgreSQL users table only; Redis refresh-token blacklist; S3-compatible object
  storage for user-owned images; RabbitMQ for the existing password-reset message.

**Testing**: pytest unit and integration suites, httpx ASGI client, Alembic migrations,
  Ruff formatting/linting, and mypy strict checking for retained source, tests, and scripts.

**Target Platform**: Linux container and local development environment; validation uses the
  project test compose services with isolated temporary data.

**Project Type**: FastAPI web service.

**Performance Goals**: Preserve current endpoint behavior and practical latency. This feature
  adds no new throughput target; removed list, role, group, and cross-user workflows must add
  no runtime work.

**Constraints**: No old-database migration or compatibility layer; no role, group, membership,
  blocking, super-user, list, or arbitrary-target behavior in the target source tree. Existing
  authentication, validation, refresh-token revocation, image size/type limits, and password-
  reset publishing remain unless they depend on removed concepts.

**Scale/Scope**: One bounded context and one users table. A user owns at most one image path;
  all protected operations are scoped to the authenticated subject.

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| Principle / gate | Status | Evidence and required action |
|---|---|---|
| User-management scope | PASS | Constitution 3.0.0 already requires registration, authentication, and self-service without groups, roles, blocking, or cross-user operations. |
| Python and FastAPI | PASS | The design retains Python 3.12 and FastAPI contracts. |
| Strict typing | PASS WITH REVIEW ITEMS | The target design uses typed DTOs and ports. Existing mypy gaps and explicit ignores remain review items; no blanket suppression is introduced. |
| DDD boundaries | PASS | Domain loses group/role/blocking concepts; application owns self-service use cases; infrastructure owns persistence and storage adapters; presentation owns HTTP. |
| Verifiable contracts | PASS | Every retained endpoint and removed endpoint family has contract or absence tests; fresh database setup is tested. |
| Technical constraints | PASS | PostgreSQL, Redis, S3-compatible storage, RabbitMQ, and existing project tooling remain in scope. |

The governing constitution is 3.0.0. The historical 2.0.0 prerequisite in the input spec
is superseded by the current constitution; no further amendment is needed for this design.
These are design gates, not claims that implementation checks have passed. Any typing or
DDD exception requires a recorded maintainer decision with reason, bounded scope, owner,
and exit condition; failed checks must remain visible.

## Project Structure

### Documentation (this feature)

```text
specs/001-remove-groups-roles/
├── plan.md
├── research.md
├── data-model.md
├── contracts/
│   └── http-api.md
├── quickstart.md
└── tasks.md                 # created by $speckit-tasks
```

### Source Code (repository root)

```text
source/
├── domain/
│   ├── entities/user.py
│   ├── value_objects/
│   ├── exceptions/
│   └── interfaces/
├── application/
│   ├── dto/
│   ├── interfaces/
│   └── use_cases/
├── infrastructure/
│   ├── database/
│   │   ├── models/
│   │   └── alembic/versions/
│   ├── jwt/
│   ├── cache/
│   ├── hasher/
│   ├── message_broker/
│   └── storage/
├── presentation/api/
│   ├── routes/
│   ├── schemas/
│   └── dependencies/
└── main.py

tests/
├── unit/
├── integration/
└── adapters/
```

The structure stays a single service. Group, role, blocking, list, arbitrary-user, and
super-user modules are deleted; retained modules are simplified in place. The Dockerfile's
Linux `appgroup` remains because it is an operating-system runtime account, not a domain group.

## Phase 0: Research Summary

Research decisions are recorded in [research.md](research.md). The relevant unknowns are
resolved: the users-only migration is a fresh baseline, self-service ownership is derived
from the authenticated subject, refresh transport remains cookie-based, and the image path
is removed from writable profile input to close a cross-user storage-key bypass.

## Phase 1: Design Summary

- [data-model.md](data-model.md) defines the users-only domain and persistence model.
- [contracts/http-api.md](contracts/http-api.md) defines retained endpoints and removed route
  families, including response/error expectations.
- [quickstart.md](quickstart.md) defines isolated validation for the fresh database, auth,
  self-service ownership, image ownership, and absence of removed behavior.

## Post-Design Constitution Re-check

| Gate | Result |
|---|---|
| Scope and ownership | PASS against constitution 3.0.0; the design has no group, role, blocking, or cross-user capability. |
| Typed DDD boundaries | PASS; all retained boundaries and data conversions are listed in the design artifacts. |
| Testability | PASS; contract, absence, unit, integration, and fresh-install checks are defined. |
| Migration policy | PASS; a new users-only baseline is required and old database upgrades are unsupported. |

## Complexity Tracking

| Violation | Why Needed | Simpler Alternative Rejected Because |
|---|---|---|
| None | The feature removes concepts and reduces the existing surface area. | No additional project or architectural boundary is introduced. |

## Implementation ordering for task generation

1. Configure strict typing and disposable validation services. Retain existing user work.
2. Complete one coordinated foundational change across domain, DTOs, repositories, models,
   migration baseline, use cases, imports/exports, dependency factories, routes, settings,
   bootstrap, and fixtures. Delete group/role/block/cross-user consumers together with their
   dependencies; remove group-router registration in `source/main.py` in this same stage.
   Adapt retained use-case signatures and route callers together. Shared modules such as
   `user_use_cases.py` and package exports require sequential ownership.
3. Before a story checkpoint, confirm application/test collection succeeds with the isolated
   test configuration and the new baseline applies. No deleted symbol may remain imported.
4. Complete US1 auth validation, then US2 profile/image validation. US3 verifies absence,
   fresh startup, and documentation; it must not postpone prerequisite runtime deletions.
5. Run all final gates. An intermediate US1 checkpoint is not a releasable feature; all three
   stories are mandatory before release.

Give bootstrap removal and migration-chain replacement one implementation task each; later
tasks verify their absence rather than repeat deletion. Regenerate the existing `tasks.md`
with `$speckit-tasks` before implementation: its current phase ordering is superseded here.

## Required verification coverage

- Domain unit tests: valid and invalid Name, Email, RawPassword, PasswordHash and ID inputs;
  preserve existing invariants, and validate profile changes even after trusted restoration.
- Application unit tests with typed fake ports: registration/login/refresh and missing users;
  own-profile read/update/delete; own-image upload/get/delete and replacement. Assert that
  only the authenticated subject is used, B's data is unchanged, writable storage keys cannot
  enter profile updates, and missing images/storage failures preserve documented outcomes.
- HTTP integration tests: every retained endpoint's success and significant errors, two-user
  isolation, ignored unknown legacy fields, token expiry/replay including same-second refresh
  uniqueness, and removed-route/OpenAPI absence.
- Persistence integration tests: fresh baseline, constraints and mapping, zero users before
  signup; `users` is the only business table and `alembic_version` is allowed metadata.
- Ruff, strict mypy across source/tests/scripts, unit and integration pytest, and all quickstart
  checks are release gates. Record actual results and any approved typing/DDD exceptions.
