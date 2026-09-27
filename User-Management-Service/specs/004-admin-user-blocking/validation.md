# Implementation validation

Current result for the two-role catalog amendment: **182 passed, zero failed,
zero skipped** on PostgreSQL/Redis/RabbitMQ and the rebuilt startup container.
The sections below retain the original implementation history; the final amendment
section supersedes the historical three-role design and 177-test result.


## Baseline (2026-09-27)

- Existing uncommitted changes from features 002/003 preserved; branch unchanged.
- Python 3.12.14 and uv 0.12.6 available. Interpreter requires sandbox escalation; UV_CACHE_DIR uses workspace .uv-cache.
- Docker initially absent from PATH. Discovered the existing per-user Docker Desktop executable at C:/Users/yomi/AppData/Local/Programs/DockerDesktop/resources/bin/docker.exe; Docker client/server 29.8.0 available. No production database or volume touched.
- Baseline: `uv run pytest tests/unit -q`: 45 passed; Ruff passed; strict mypy passed (122 files).
- Ignore files already contain Python, environment, build, editor and Docker exclusions.

## Verification status

## Implementation and checkpoints

- Three-role domain enum, guarded immutable transitions, safe DTOs, current-state authorization, narrow storage writes and explicit transaction commits implemented.
- Initial-only bootstrap, PostgreSQL advisory lock across migrations/creation, safe diagnostics and lazy initial settings implemented. Existing account notification is verified.
- Four new HTTP operations, local validation errors, profile output fields and protected deletion implemented; historical feature specifications preserved.
- Existing real Redis/RabbitMQ tests were discovered and executed; the analysis concern about preparing real-adapter verification is resolved by those tests.
- Red/green evidence: T003, US1 bootstrap, US2 role-change and US3/US4 scenario tests initially failed on missing implementation; US5 response-field assertions initially failed before schemas were updated.
- Foundation checkpoint: 48 unit tests and one isolated schema test passed; mypy passed.
- Real PostgreSQL/admin/schema/Redis/RabbitMQ checkpoint: 31 passed, zero skipped.
- Startup/entrypoint/restart checkpoint: 13 passed, zero skipped. Includes two independent runners, three repeats, ignored changed settings, renamed profile, conflicting identity, missing/invalid data, lock timeout, unavailable DB, abrupt process exit after INSERT before commit, and container refusal to exec after failure.
- Pre-final unit suite: 59 passed. Ruff check and format check passed; strict mypy passed. No unresolved typing or DDD exceptions identified, and no suppression added.
- Final review added three safe network-error tests: two initially failed on raw ConnectionRefusedError; the infrastructure boundary now translates both SQLAlchemy and OS network errors, and all three pass. Final strict mypy and format check cover 160 files.

## Isolated execution environment

Only Compose project `ums-admin-codex-20260927` was created/restarted/removed. PostgreSQL 16, Redis 7 and RabbitMQ 4 use tmpfs. Host ports: 55434, 56380, 55673, 55674 and 58001. `.env.admin-test` contains disposable test values and is excluded by Git/Docker ignore rules. Existing project `user-management-service` and its volumes were not changed.

Commands use the discovered Docker executable, workspace UV_CACHE_DIR, UMS_REQUIRE_POSTGRES=1, explicit UMS_TEST_POSTGRES_URL/REDIS_URL/BROKER_URL and, for container checks, UMS_TEST_APP_URL/DOCKER/COMPOSE_PROJECT/COMPOSE_ENV_FILE plus disposable test bootstrap credentials.

## Requirement-to-test mapping

| Requirements | Observable verification |
|---|---|
| FR-001, SC-002 | [Domain role invariants](../../tests/unit/user_access_invariants_test.py), [role/protected account HTTP](../../tests/integration/admin_tests/superadmin_protection_test.py), [schema constraints](../../tests/integration/settings/fresh_schema_test.py), [OpenAPI](../../tests/integration/admin_tests/access_contract_test.py) |
| FR-002–004, SC-001, SC-008 | [Bootstrap unit/config](../../tests/unit/bootstrap_use_case_test.py), [independent processes and negative entrypoints](../../tests/integration/settings/admin_startup_test.py), [actual production container](../../tests/integration/settings/startup_test.py) |
| FR-005 | [Protected transitions](../../tests/unit/user_access_invariants_test.py), [delete usecase rollback](../../tests/unit/user_usecases_tests/delete_user_test.py), [protected HTTP](../../tests/integration/admin_tests/superadmin_protection_test.py), [role](../../tests/integration/admin_tests/change_role_test.py), [block](../../tests/integration/admin_tests/block_user_test.py) |
| FR-006–007, SC-003 | [Role-change usecase](../../tests/unit/admin_usecases_tests/change_role_test.py), [HTTP](../../tests/integration/admin_tests/change_role_test.py), [existing sessions](../../tests/integration/admin_tests/list_users_test.py), [demoted actor](../../tests/integration/admin_tests/block_user_test.py) |
| FR-008–010, SC-004 | [Safe list usecase](../../tests/unit/admin_usecases_tests/list_users_test.py), [125-account pagination](../../tests/integration/admin_tests/list_users_test.py), [access matrix](../../tests/integration/admin_tests/access_contract_test.py) |
| FR-011–012, SC-006 | [Block usecase](../../tests/unit/admin_usecases_tests/block_user_test.py), [HTTP block](../../tests/integration/admin_tests/block_user_test.py), [multiple sessions/commit failures](../../tests/integration/admin_tests/blocked_sessions_test.py), [restart persistence](../../tests/integration/settings/startup_test.py) |
| FR-013 | [Current subject](../../tests/unit/current_subject_test.py), [old-session role effects](../../tests/integration/admin_tests/list_users_test.py), [PostgreSQL races/stale ORM](../../tests/integration/admin_tests/concurrent_changes_test.py), [blocked sessions](../../tests/integration/admin_tests/blocked_sessions_test.py) |
| FR-014, SC-007 | [Signup privilege injection](../../tests/integration/auth_tests/signup_user_test.py), [profile privilege injection](../../tests/integration/user_tests/edit_current_user_test.py), [all roles](../../tests/integration/admin_tests/access_contract_test.py), [registration usecase](../../tests/unit/user_usecases_tests/register_user_test.py) |
| FR-015, SC-005 | [Role errors](../../tests/integration/admin_tests/change_role_test.py), [block errors](../../tests/integration/admin_tests/block_user_test.py), [validation/pagination](../../tests/integration/admin_tests/list_users_test.py), [access/OpenAPI matrix](../../tests/integration/admin_tests/access_contract_test.py), [fail-closed state and commit](../../tests/integration/admin_tests/blocked_sessions_test.py), [SQL/network failures](../../tests/unit/database_failure_test.py) |
| FR-016 | [Auth regressions](../../tests/integration/auth_tests), [self-service regressions](../../tests/integration/user_tests), [real Redis/RabbitMQ](../../tests/integration/settings/real_services_test.py), [blocked recovery](../../tests/integration/admin_tests/blocked_sessions_test.py) |
| FR-017 | [README](../../README.md), [quickstart](quickstart.md), [startup diagnostics and actual entrypoint](../../tests/integration/settings/admin_startup_test.py) |

## Historical full-suite result before the two-role amendment

`uv run pytest tests/unit tests/integration -q`: **177 passed, zero failed, zero skipped**, 122.58s. PostgreSQL required; real Redis/RabbitMQ and the rebuilt production container enabled. This includes 62 unit tests and 115 integration tests. The prior fresh-installation full run also passed (174 tests before adding the three network-error regressions).

Final gates: `uv run ruff check source tests scripts` passed; `uv run ruff format --check source tests scripts` passed (160 files); `uv run mypy source tests scripts` passed (160 files); `git diff --check` passed. Git emits an existing uv.lock line-ending advisory, not a whitespace error.

All 50 tasks completed. Spec, plan, data model, HTTP/startup contracts, quickstart and constitution 5.0.0 reconciled with the implementation. No extension configuration exists, so no after_implement hooks are registered. Test containers and their disposable network are removed after verification; no production deployment, database reset or volume removal performed.

## Two-role catalog amendment — 2026-09-27

- User explicitly requested a separate model/table with exactly two roles and
  confirmed retaining the protected superadmin as admin/is_superadmin=true.
- RoleEntity, IRoleRepository, ORM Role and RoleRepository implemented; GET /roles
  reads the seeded catalog. Users reference roles through role_id; enum/API values
  are user/admin. Bootstrap/current permissions use the protected flag.
- role_catalog_20260927 follows users_roles_20260927. Tests perform downgrade to the
  old schema, insert all three old roles, upgrade, downgrade and upgrade again.
  UUID, name/surname, username, email, phone, password hash, timestamps and blocking
  remain identical. The old superadmin becomes admin with the protected flag.
- Actual PostgreSQL schema/constraints, ORM relationship, catalog label read,
  OpenAPI two-value enum, protected profile flag, role/block operations, old sessions,
  races and independent-process/container startup all verified.
- Local preliminary suite: 164 passed, 17 service-dependent skipped (before the
  final added catalog test). These skips were subsequently exercised on real services.
- Final full suite: `uv run pytest tests/unit tests/integration -q`: **182 passed**,
  **0 skipped**, **0 failed**, 136.43s. Required PostgreSQL and explicit disposable
  Compose environment enabled; source code was rebuilt into app_test.
- Ruff check passed; strict mypy passed for 166 files. Final format/diff checks are
  recorded after documentation review. No dependency changes or type suppressions
  were needed for this amendment.
- T051–T056 completed; current docs and constitution 6.0.0 reflect the two-role
  catalog and forward migration. Historical specs/checklists were not rewritten.

Final amendment gates: Ruff check and format check passed (166 files), strict mypy
passed (166 files), git diff --check passed. The six updated migration/catalog and
protected-account tests additionally passed on temporary SQLite. Checklist
requirements.md remained read-only (16/16 checked); no extension configuration or
mandatory hooks exist. Current spec, plan and amendment task coverage reconciled.

Disposable Compose project ums-admin-codex-20260927 was removed after verification,
without down -v or production database operations. No deployment or commit performed.
