# Research: Remove Groups, Roles, and Cross-User Operations

## Decision 1: Use a users-only migration baseline

**Decision**: Replace the executable Alembic revision chain with one new baseline revision
whose `down_revision` is `None` and whose schema creates only `users` and its required
indexes/constraints. The target starts from a new empty database. Existing database upgrades,
data migration, and stamping an old database with the new baseline are unsupported.

**Rationale**: The specification requires a fresh empty installation and forbids shipping
executable creation of groups, role enums, membership foreign keys, or blocking fields.
Appending a drop migration would still ship the old model and would contradict FR-013.

**Alternatives considered**: A drop migration preserves an obsolete chain and supports an
out-of-scope upgrade path; retaining nullable legacy columns leaves removed concepts in the
target model. Both are rejected.

Alembic's `alembic_version` table is permitted migration metadata. Schema assertions must
distinguish it from the single business table, `users`, and check zero users before signup.

## Decision 2: Derive ownership from the authenticated subject

**Decision**: Retain repository lookup by authenticated user ID internally, but remove all
public arbitrary-user targets. Own profile and image use cases receive the authenticated
subject and never accept a client-selected target ID. Remove list, get-by-ID, edit-by-ID,
delete-by-ID, block, and role-change flows.

**Rationale**: A repository's internal lookup is needed to authenticate, update, and delete
the current user; it does not imply a public cross-user capability. Deriving the target from
the verified token makes the ownership rule testable and prevents ID substitution.

**Alternatives considered**: Keeping arbitrary IDs with authorization checks retains a larger
attack surface and the removed feature shape. Keeping a list endpoint without privileged roles
would violate the explicit self-service decision.

## Decision 3: Keep refresh-token transport and revocation semantics

**Decision**: Keep the access-token response, HttpOnly refresh cookie, bearer requirement for
refresh, Redis blacklist, expiry validation, and missing-user checks. Access payload contains
`sub`, `email`, and `exp`; refresh payload contains `sub`, `exp`, and a provider-generated
unique `jti` per issuance. Neither contains role or group data. Deterministic same-second
rotation tests must prove the replacement is distinct and usable while replay is rejected.
The existing full-token Redis blacklist key is retained. This is token correctness, not
a user privilege or role feature.

**Rationale**: FR-003 and FR-007 preserve authentication and refresh behavior while removing
authorization categories. Redis token revocation is session security, not user blocking.
The current JWT provider adds only `exp` to `sub`, so issuance in the same second can produce
an identical token that has just been blacklisted. A fresh `jti` removes that collision.

**Alternatives considered**: Removing refresh revocation changes existing security behavior;
putting a replacement role or permission claim into tokens recreates the removed model.

## Decision 4: Make image storage keys output-only

**Decision**: Remove `image_s3_path` from profile PATCH input and its update DTO. Keep it in
read responses where required. Only own-image upload and own-image delete may change the
stored key. Own-image GET signs only the authenticated user's stored key.

**Rationale**: The current writable path permits a user to assign another user's key and
retrieve or delete that object's image. Removing the arbitrary assignment is the smallest
change that enforces FR-004/FR-005 without inventing a new storage-ownership table.

**Alternatives considered**: Validate path ownership in a new table or encode ownership in
object keys. Both add data and migration complexity despite the fresh-install scope.

## Decision 5: Remove domain categories and super-user bootstrap

**Decision**: Delete domain `UserRole`, group entities/repositories/routes/schemas, `is_blocked`,
group IDs, role/group DTOs, role/group error mappings, super-user settings, bootstrap script,
and related tests/fixtures. Preserve the Dockerfile's `appgroup` OS account.

**Rationale**: FR-001/002/008/009/010 require removal from code, tests, settings, startup,
and contracts. The operating-system group is unrelated to the user domain and is needed for
non-root container execution.

**Alternatives considered**: Leave disabled modules or nullable legacy fields. This would
violate the requirement that removed functionality not remain hidden in the target supply.

## Decision 6: Strict typing is a staged gate with explicit review

**Decision**: Pin and configure mypy strict checking for retained source, tests, and scripts;
fix touched interfaces and fixtures. Existing unrelated gaps may be handled only by the
individual review exception process in the constitution, with failed checks visible.

**Rationale**: The constitution requires strict typing but the current repository has no mypy
configuration, untyped fixtures, and local/global ignores. The feature should not introduce
new blanket ignores while the baseline is repaired.

**Alternatives considered**: Treating Ruff or Pydantic as a type checker, or keeping a global
`mypy: ignore-errors`, would conceal the very boundary errors this feature changes.

## Decision 7: Validate with isolated temporary services

**Decision**: Use a fresh PostgreSQL database plus temporary Redis and RabbitMQ services for
integration checks. Do not reuse production volumes. The existing test compose file's tmpfs
services are the model, but fixed container names and ports must be made isolated if parallel
runs are required.

**Rationale**: The target explicitly has no data migration. A disposable environment proves
the baseline and avoids destructive operations on a user's existing database.

**Alternatives considered**: Running against production compose volumes risks data loss and
cannot prove the fresh-install requirement.

## Decision 8: Remove dependency consumers in the foundational change

**Decision**: Delete obsolete routes, use cases, factories, imports and exports in the same
foundational stage as their domain and repository dependencies. Adapt retained consumers
before running any user-story checkpoint. Later removal tasks are verification only.

**Rationale**: `source/main.py` currently imports the group router, and group use cases import
`UserRole` and `GroupEntity`. Deleting their providers first breaks application imports.
Shared use-case modules also prevent treating all story implementation as independent work.

**Alternatives considered**: Postpone consumer removal to US3 or retain temporary stubs.
The former breaks the US1 checkpoint; the latter retains forbidden executable concepts.

## Decision 9: Verify self-service rules at both application and HTTP boundaries

**Decision**: Use typed fake repositories/storage/token ports for domain and application unit
tests; retain HTTP and persistence integration tests as separate checks. Cover all retained
profile/image use cases, ownership, validation, missing users/images, and storage errors.

**Rationale**: Constitution 3.0.0 principle V requires invariant and use-case tests independent
of real services. HTTP-only tests do not establish those required layer-level checks.

**Alternatives considered**: Only route tests or only replacing removed-feature tests leaves
the changed self-service use cases without explicit unit verification.

## Decision 10: Preserve unknown-field and refresh transport behavior

**Decision**: Retained JSON request models continue ignoring unknown fields under the existing
Pydantic model policy. Removed fields are absent from schemas/DTOs and never affect state.
Refresh retains bearer-header presence plus validation of the refresh cookie; it does not
require a still-valid access token. Own-account routes validate the access token and user.

**Rationale**: The spec explicitly preserves unknown-field handling. Current base schemas use
plain BaseModel; the refresh route extracts the bearer value but validates the cookie in
ResetTokens. Existing error maps distinguish invalid session data (401) and absent user (404).

**Alternatives considered**: Reject every unknown field with 422 or require a valid access
token during refresh; both change retained behavior beyond the agreed feature scope.
