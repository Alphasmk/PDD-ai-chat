---
description: "Dependency-ordered tasks for the users-only service"
---

# Tasks: Remove Groups, Roles, and Cross-User Operations

**Feature**: `001-remove-groups-roles` | **Updated**: 2026-09-26 | **Git branch**: `fix/um`

**Input**: `spec.md`, `plan.md`, `research.md`, `data-model.md`, `contracts/http-api.md`, and `quickstart.md` in `specs/001-remove-groups-roles/`.
**Authority**: Constitution 3.0.0; the spec's historical 2.0.0 amendment prerequisite is superseded.
**Tests**: Required by FR-015 and constitution V. Implementation progress is recorded below; validation results are in validation.md. Paths are repository-relative; new test files are explicitly identified.
**Parallelism**: `[P]` applies only within the indicated test wave after its prerequisites. Shared modules and exports have sequential ownership.

## Phase 1: Setup

**Purpose**: Establish tooling and isolated validation without modifying existing data.

- [X] T001 Record constitution 3.0.0 gates, current typing/DDD discrepancies, and the retained endpoint inventory in new `specs/001-remove-groups-roles/validation.md`; use `plan.md` as the current design authority.
- [X] T002 Pin mypy and required stubs in `pyproject.toml`, update `uv.lock`, and configure strict checking across `source`, `tests`, and Python `scripts`; remove blanket type-check suppression without hiding failures.
- [X] T003 Make `docker-compose.test.yaml` disposable and isolated: remove fixed container names, parameterize conflicting host ports, retain temporary data, and document matching test environment settings in `specs/001-remove-groups-roles/quickstart.md`.

## Phase 2: Foundational (Blocks All Stories)

**Purpose**: Complete one coordinated dependency removal before any story checkpoint. T004–T014 form one integration batch; temporary broken imports inside that batch are not a completed checkpoint. No runtime deletion is deferred to US3.

- [X] T004 Remove group routes/schemas/factories/use cases and their exports in `source/presentation/api/routes/group_router.py`, `source/presentation/api/schemas/group.py`, `source/presentation/api/dependencies/group_deps.py`, and `source/application/use_cases/group_use_cases.py`; remove group router registration in `source/main.py` and group conversion/imports in `source/application/use_cases/base.py`.
- [X] T005 Remove list, arbitrary-target profile/image, role-change, and blocking operations from `source/application/use_cases/user_use_cases.py` and `source/presentation/api/routes/user_router.py`; update `source/application/use_cases/__init__.py` and `source/presentation/api/dependencies/` exports/factories, retaining self-service operations for adaptation in T012.
- [X] T006 Remove super-user creation from `source/application/use_cases/user_use_cases.py` and dependencies, delete `scripts/create_superuser.py` and `source/settings/separated_configs/super_user_config.py`, and remove bootstrap references from `scripts/entry.sh`, `source/settings/config.py`, `source/settings/separated_configs/__init__.py`, and `.env.example`; retain ordinary startup and Dockerfile OS `appgroup`.
- [X] T007 Simplify `source/domain/entities/user.py` and delete obsolete group entities, role enums and domain exceptions/exports in `source/domain/`; preserve ID "Primary key, generated UUID, not null", name/surname "Required string; current 2–20 length and name-character rules", password hash "Required; stored hash only", and raw password "length 8–20 and the current allowed-character expression" from `data-model.md`.
- [X] T008 Update `source/application/dto/users_dto.py` and `source/application/dto/` exports/token types: remove role/group/block/pagination DTOs and target-user inputs; remove writable `image_s3_path` from create/update input, retain read output, and represent authenticated subject explicitly with typed values.
- [X] T009 Update `source/application/interfaces/repositories.py`, `source/infrastructure/database/user_repository.py`, and interface/database exports; delete `source/infrastructure/database/group_repository.py`; retain internal subject-ID and login lookups, add/update/delete and typed domain mapping, removing list/group/role/block ports.
- [X] T010 Update `source/infrastructure/database/models/users.py` and model exports, deleting `source/infrastructure/database/models/groups.py`; preserve username "Required, unique index; preserve current uniqueness semantics", email "Required and unique; Pydantic email plus domain validation", phone "Nullable and unique when non-null; preserve current semantics", image "Nullable storage reference owned by this user", created_at "Required timestamp", and updated_at "Nullable update timestamp"; make timezone conversion explicit in repository mapping.
- [X] T011 Replace the executable revision chain in `source/infrastructure/database/alembic/versions/` with one baseline having `down_revision = None`, matching T010; allow only the `users` business table and `alembic_version` metadata, with zero users before signup and no old-database upgrade/stamping or data migration.
- [X] T012 Adapt retained signatures and callers together in `source/application/use_cases/user_use_cases.py`, `source/presentation/api/routes/auth_router.py`, `source/presentation/api/routes/user_router.py`, and `source/presentation/api/dependencies/`: derive account/image targets exclusively from verified subject, resolve existing users, remove obsolete authorization branches and claims, and preserve internal repository lookup and current refresh transport.
- [X] T013 Align `source/presentation/api/schemas/auth.py`, `source/presentation/api/schemas/user.py`, `source/presentation/exceptions.py`, and `source/application/exceptions/` exports with `contracts/http-api.md`: no removed fields, ignored unknown JSON inputs, no writable image key, retained typed responses and significant error maps.
- [X] T014 Replace fixtures/adapters in `tests/conftest.py`, `tests/integration/conftest.py`, `tests/unit/user_usecases_tests/conftest.py`, `tests/unit/utils/shared_data.py`, and `tests/adapters/` with typed ordinary-user ports; remove obsolete unit tests in `tests/unit/group_usecases_tests/` and role/block/list/arbitrary-user test modules, update retained test signatures/imports and remove obsolete integration imports so collection requires no deleted symbols.
- [X] T015 Add new `tests/unit/domain_invariants_test.py` covering valid/invalid Name, Email, RawPassword, PasswordHash and ID behavior and validation on updates after trusted restoration; use no real infrastructure and do not add invariants beyond `data-model.md`.
- [X] T016 With isolated test configuration, import `source/main.py`, run `uv run pytest --collect-only tests` and domain unit tests, apply the fresh baseline, and record results in `specs/001-remove-groups-roles/validation.md`; resolve all obsolete-symbol imports before starting US1.

**Checkpoint**: Application imports and all tests collect; fresh schema applies; no removed runtime consumers remain. Story behavior is verified below.

## Phase 3: US1 — Registration and Authentication Without Categories (P1)

**Goal**: Preserve signup, login, refresh and password-reset request with ordinary users.
**Independent test**: Register on a fresh database, log in, rotate twice in the same second, reject replay, and publish a password-reset request; verify claims and significant errors.

### Tests (parallel wave after T016)

- [X] T017 [P] [US1] Update `tests/unit/user_usecases_tests/register_user_test.py` and `tests/unit/user_usecases_tests/login_user_test.py` for ordinary users, validation, hashing, invalid credentials and no partial account/session creation on failure.
- [X] T018 [P] [US1] Update `tests/unit/user_usecases_tests/reset_tokens_test.py` and add `tests/unit/current_subject_test.py` and `tests/unit/token_provider_test.py` for missing/deleted users, invalid/expired/revoked tokens and deterministic same-second refresh uniqueness using the real JWT provider; assert old-token replay fails while the replacement remains usable.
- [X] T019 [P] [US1] Update `tests/integration/auth_tests/signup_user_test.py`, `tests/integration/auth_tests/login_for_access_token_test.py`, `tests/integration/auth_tests/reset_tokens_test.py`, and `tests/integration/auth_tests/reset_password_test.py` for exact contract shapes, ignored legacy fields, unique-data conflicts, HttpOnly rotation, bearer-presence refresh with expired access token, 401 session errors and 404 missing subject.
- [X] T020 [P] [US1] Update `tests/unit/user_usecases_tests/reset_user_password_test.py` to verify the existing publisher port call and failure propagation without a real broker or implementing additional recovery stages.

### Implementation and checkpoint (after test wave)

- [X] T021 [US1] Implement fresh provider-generated `jti` per refresh issuance in `source/infrastructure/jwt/token_provider.py`, its typed port in `source/application/interfaces/token_provider.py`, and token fake under `tests/adapters/`; access claims are exactly `sub,email,exp`, new refresh claims exactly `sub,exp,jti`; retain full-token Redis blacklist keys and expiry.
- [X] T022 [US1] Finish RegisterUser/LoginUser/ResetTokens/GetCurrentUserFromToken behavior in `source/application/use_cases/user_use_cases.py` and factories in `source/presentation/api/dependencies/`; resolve absent subjects, retain cookie refresh/revocation and password-reset publishing, and make T017–T020 pass without restoring removed categories.
- [X] T023 [US1] Verify all four auth endpoints in `source/presentation/api/routes/auth_router.py` against `contracts/http-api.md`, run US1 unit/integration tests and record actual results in `specs/001-remove-groups-roles/validation.md`.

## Phase 4: US2 — Own Profile and Image (P1)

**Goal**: Read, update and delete only the authenticated account and its image.
**Independent test**: Create A and B; exercise all six `/users/me` operations as A, inject B's ID/key, and verify B remains unread and unchanged; invalid sessions are rejected.

### Tests (parallel wave after T023)

- [X] T024 [P] [US2] Update `tests/unit/user_usecases_tests/update_user_test.py`, `tests/unit/user_usecases_tests/delete_user_test.py`, and `tests/unit/user_usecases_tests/get_current_user_from_db_test.py` for subject-only lookup, success/empty patch/missing user, domain validation after trusted restoration and no changes to B, using typed fake ports only.
- [X] T025 [P] [US2] Update `tests/unit/user_usecases_tests/set_user_image_test.py`, `tests/unit/user_usecases_tests/get_user_image_test.py`, and `tests/unit/user_usecases_tests/delete_user_image_test.py` for own-key selection, replacement, missing user/image, upload/sign/delete failures and unchanged B data with typed storage/repository fakes.
- [X] T026 [P] [US2] Update `tests/integration/user_tests/get_current_user_test.py`, `tests/integration/user_tests/edit_current_user_test.py`, and `tests/integration/user_tests/delete_current_user_test.py` for exact responses, validation/conflicts, missing/invalid session, deleted subjects and ignored foreign ID/image key/legacy fields with no cross-user effects.
- [X] T027 [P] [US2] Add `tests/integration/user_tests/own_image_test.py` using isolated storage fakes for upload/GET/delete, "JPEG/PNG/WebP and 5 MiB limits", missing image, mapped storage errors, invalid sessions and two-user isolation; assert successful delete preserves `200 null`.

### Implementation and checkpoint

- [X] T028 [US2] Complete subject-only GetCurrentUserFromDB/UpdateUser/DeleteUser in `source/application/use_cases/user_use_cases.py` with typed domain conversion, update validation, existing errors and no arbitrary target argument; make T024 pass.
- [X] T029 [US2] Complete SetUserImage/GetUserImage/DeleteUserImage in `source/application/use_cases/user_use_cases.py` and `source/application/interfaces/storage.py`: select only the subject's stored path, preserve replacement and failure semantics, and make T025 pass.
- [X] T030 [US2] Finalize self-profile/image routes in `source/presentation/api/routes/user_router.py`, schemas in `source/presentation/api/schemas/user.py`, factories in `source/presentation/api/dependencies/user_deps.py`, and `source/presentation/exceptions.py`; match contract, ignored unknown fields, format/size limits and subject-derived targets.
- [X] T031 [US2] Run US2 unit/integration tests and the two-user scenarios from `specs/001-remove-groups-roles/quickstart.md`; record success and failure outcomes in `specs/001-remove-groups-roles/validation.md`.

## Phase 5: US3 — Complete Removal and Fresh Installation (P2)

**Goal**: Prove absence of removed capabilities and readiness of a zero-user installation.
**Independent test**: Start a fresh installation without super-user settings; inspect schema/OpenAPI/source and call all removed route families without state changes.

### Tests (parallel wave after T031)

- [X] T032 [P] [US3] Add `tests/integration/group_tests/removed_groups_test.py` and remove superseded group behavior tests there; exercise all former group/membership methods, assert route absence and no data disclosure or mutation.
- [X] T033 [P] [US3] Add `tests/integration/user_tests/removed_operations_test.py` covering list, arbitrary profile/image, role and block route families; assert normal missing-route responses, no side effects and absence from generated OpenAPI, including obsolete schema fields.
- [X] T034 [P] [US3] Add `tests/integration/settings/fresh_schema_test.py` to apply the baseline to an empty isolated database and assert exact business columns/constraints/indexes, only `users` plus allowed `alembic_version` metadata, zero initial users and ordinary first signup; verify retained repository mappings and uniqueness constraints.

### Documentation and checkpoint

- [X] T035 [US3] Audit `source/`, `scripts/`, `tests/`, `.env.example`, and `Dockerfile` for removed runtime concepts, obsolete exports and executable migrations; record each remaining match and its rationale in `specs/001-remove-groups-roles/validation.md`, allowing absence assertions, historical documentation and OS `appgroup`, but no hidden implementation.
- [X] T036 [US3] Update `README.md` and `specs/001-remove-groups-roles/quickstart.md` for fresh-install startup, retained API, disposable tests and no super-user or migration prerequisites; reconcile the obsolete constitution-version assumption in `specs/001-remove-groups-roles/spec.md` with 3.0.0 without changing feature scope.
- [X] T037 [US3] Run absence/schema tests and start through `scripts/entry.sh` on the disposable empty database without super-user environment variables; verify zero users before ordinary registration and record results in `specs/001-remove-groups-roles/validation.md`.

## Phase 6: Polish and Release Gates

- [X] T038 Run `uv run ruff check source tests scripts` and `uv run ruff format --check source tests scripts`; fix findings in `source/`, `tests/`, and `scripts/` and record actual results in `specs/001-remove-groups-roles/validation.md`.
- [X] T039 Run `uv run mypy source tests scripts` with strict configuration in `pyproject.toml`; resolve feature errors and record remaining typing/DDD discrepancies in `specs/001-remove-groups-roles/validation.md`, requiring explicit maintainer decisions with reason, bounded scope, owner and exit condition for any exception; failed checks remain visible.
- [X] T040 Run `uv run pytest tests/unit` without real services and `uv run pytest tests/integration` against isolated services, then every `specs/001-remove-groups-roles/quickstart.md` check; record commands, results and reasons for unexecuted checks in `specs/001-remove-groups-roles/validation.md`.
- [X] T041 Compare final source/contracts/tests against every FR-001–FR-015 and SC-001–SC-007 in `specs/001-remove-groups-roles/spec.md`, `data-model.md`, and `contracts/http-api.md`; record traceability and resolve divergences in `specs/001-remove-groups-roles/validation.md` before declaring completion.

## Dependencies and Execution Order

```text
Setup T001–T003
  -> coordinated foundation T004–T016
  -> US1 tests T017–T020 -> T021–T023
  -> US2 tests T024–T027 -> T028–T031
  -> US3 tests T032–T034 -> T035–T037
  -> release gates T038–T041
```

Within unmarked groups use ascending task order. Each marked test wave depends on the preceding checkpoint but its files are independent; shared fixture edits must be completed before dispatching the wave. Do not parallelize story implementation in `user_use_cases.py`, exports, dependencies or error maps. If final gates require edits, rerun affected checks before completion.

## Parallel Examples per Story

- US1: after T016, T017 registration/login unit tests, T018 session unit tests, T019 HTTP tests, and T020 publisher unit tests may proceed concurrently.
- US2: after T023, T024 profile unit tests, T025 image unit tests, T026 profile HTTP tests, and T027 image HTTP tests may proceed concurrently.
- US3: after T031, T032 group absence, T033 removed-user API absence, and T034 fresh-schema tests may proceed concurrently, with distinct disposable databases for test execution.

## Coverage Map

| Requirement | Principal tasks |
|---|---|
| FR-001 | T004, T032, T035 |
| FR-002 | T005, T007–T013, T033, T035 |
| FR-003 | T017–T023 |
| FR-004 | T005, T008, T012, T024–T033 |
| FR-005 | T024–T031 |
| FR-006 | T008, T013, T019, T026, T033 |
| FR-007 | T012, T018, T021–T023 |
| FR-008 | T004–T014, T035 |
| FR-009 | T006, T037 |
| FR-010 | T007–T011, T034 |
| FR-011 | T032, T033 |
| FR-012 | T003, T011, T034, T037 |
| FR-013 | T011, T034, T035 |
| FR-014 | T012, T018, T026, T027 |
| FR-015 | T015, T017–T020, T024–T027, T032–T034, T036, T040 |
| SC-001 | T017–T023 |
| SC-002 | T019, T026, T033, T041 |
| SC-003 | T032, T033 |
| SC-004 | T024–T031, T033 |
| SC-005 | T024–T031 |
| SC-006 | T011, T034, T037 |
| SC-007 | T006, T036, T037 |

## Implementation Strategy

The internal MVP checkpoint is Setup + Foundation + US1: signup/login/refresh/reset request on a fresh database. It is not a release boundary. Continue with US2 ownership verification, US3 absence/startup verification and all release gates. Bootstrap removal (T006) and baseline replacement (T011) each have one implementation owner; subsequent tasks verify outcomes rather than repeat deletion. Tests may expose incomplete behavior after the foundational structural adaptation; resolve those failures in each story before its checkpoint. No database containing existing user data is a validation target.
