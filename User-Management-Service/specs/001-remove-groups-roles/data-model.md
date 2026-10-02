# Data Model: Users-Only Service

## User

The only persisted domain entity is `User`. It has no role, group membership, blocking state,
or privilege category.

`users` is the only business table. Alembic may create `alembic_version` as migration
metadata; it is not a domain entity. After baseline migration and before registration,
`users` must contain zero rows. No bootstrap inserts are permitted.

| Field | Domain type | Persistence rule | API visibility |
|---|---|---|---|
| `id` | `ID` / UUID | Primary key, generated UUID, not null | Read-only |
| `name` | `Name` | Required string; current 2–20 length and name-character rules | Read/write |
| `surname` | `Name` | Required string; current 2–20 length and name-character rules | Read/write |
| `username` | `str` | Required, unique index; preserve current uniqueness semantics | Read/write |
| `password_hash` | `PasswordHash` | Required; stored hash only | Never exposed |
| `email` | `Email` | Required and unique; Pydantic email plus domain validation | Read/write |
| `phone_number` | `str \| None` | Nullable and unique when non-null; preserve current semantics | Read/write |
| `image_s3_path` | `str \| None` | Nullable storage reference owned by this user | Read-only in profile; changed only by own-image use cases |
| `created_at` | `datetime` | Required timestamp | Read-only |
| `updated_at` | `datetime \| None` | Nullable update timestamp | Read-only |

The existing raw-password rules remain: length 8–20 and the current allowed-character
expression. `from_trusted` restoration is permitted for persisted values under the constitution;
new input and state changes still pass domain validation. Timestamp mapping must remain explicit
because the current ORM and domain defaults differ in timezone awareness.

## Session token data

JWT access tokens contain `sub`, `email`, and `exp`. Refresh tokens contain `sub`, `exp`,
and a fresh provider-generated `jti` for each issuance, including same-second rotations.
Refresh tokens remain HttpOnly-cookie transported and blacklisted in Redis until expiry. No token
contains `role`, `group_id`, `is_blocked`, or a replacement permission claim.

The authenticated `sub` must resolve to an existing user before a protected action proceeds.
Deleted users and tokens from an old installation do not gain access to a new installation.

## User image

An image is an optional user-owned object reference. Upload, GET, and delete are self-service
operations. The profile update contract cannot accept an arbitrary object key. The image API
retains the current JPEG/PNG/WebP and 5 MiB limits and its existing storage error mapping.

## Removed entities and attributes

The target schema contains none of the following:

- `groups` table or group entity/repository/DTO/schema/routes;
- `group_id`, membership records, or group foreign keys;
- `role` column, `UserRole` enum, role DTOs, or role-change operations;
- `is_blocked`, block-state operations, or blocked-user behavior;
- super-user bootstrap data or settings.

## State transitions

```text
no account --register--> active account --login--> authenticated session
authenticated session --refresh--> rotated authenticated session
authenticated session --update own profile--> active account
authenticated session --upload/delete own image--> active account with updated image reference
authenticated session --delete own account--> no account
```

There is no role, group-membership, blocking, or privilege state transition.
