# HTTP API Contract: Users-Only Service

All routes use the `/api/v1` prefix. Own-account routes require a valid bearer access token
whose subject resolves to an existing user. Refresh requires bearer-header presence and a
valid refresh cookie, preserving the existing flow even when the access token has expired.
The API exposes only registration/authentication and self-service account/image operations.

## Retained public endpoints

| Method and path | Auth | Request | Success |
|---|---|---|---|
| `POST /auth/signup` | None | JSON: `name`, `surname`, `username`, `password`, `email`; optional `phone_number` | `201 UserResponse` |
| `POST /auth/login` | None | Form: `username`, `password` | `200 TokenResponse`; sets HttpOnly `refresh_token` cookie |
| `POST /auth/refresh-token` | Bearer presence + refresh cookie | No body; refresh cookie | `200 TokenResponse`; replaces cookie |
| `POST /auth/reset-password` | None | JSON: `email` | `200 {message}` |
| `GET /users/me` | Bearer | None | `200 UserResponse` |
| `PATCH /users/me` | Bearer | JSON: optional `name`, `surname`, `username`, `email`, `phone_number` | `200 UserEditResponse` |
| `DELETE /users/me` | Bearer | None | `200 UserDeleteResponse` |
| `POST /users/me/image` | Bearer | Multipart `image` | `200 {image_s3_path}` |
| `GET /users/me/image` | Bearer | None | `200 {image_url}` |
| `DELETE /users/me/image` | Bearer | None | `200 null` (preserve current route behavior) |

`PATCH /users/me` MUST NOT define or apply `id`, `image_s3_path`, role, group, block, or
target-user fields. Unknown fields are ignored under the existing JSON model policy;
they cannot select a target or modify storage references. Image references change only
through own-image upload/delete; image GET reads the current user's stored reference.

Access JWT claims are `sub`, `email`, `exp`; newly issued refresh JWT claims are `sub`,
`exp`, `jti`. The provider generates a unique refresh `jti` on each issuance. A same-second
rotation must yield a usable replacement token and reject reuse of the previous token.

## Response shapes

`UserResponse` contains `id`, `name`, `surname`, `username`, `email`, nullable
`phone_number`, nullable `image_s3_path`, `created_at`, and nullable `updated_at`.
It contains no role, group, or blocking fields. `UserEditResponse` contains the editable
profile fields plus nullable `image_s3_path`; it does not expose a password hash.
`UserDeleteResponse` contains `id`, `username`, and `email`. `TokenResponse` contains
`access_token`, `refresh_token`, and `token_type="bearer"`.

## Error expectations

- `400`: domain validation or storage-operation failures mapped by the existing error system.
- `401`: missing, expired, malformed, or revoked authentication/session data.
- `404`: absent authenticated user or absent own image; removed route families are not present
  in OpenAPI and normal routing returns not found.
- `409`: duplicate username, email, or phone where the existing repository maps conflicts.
- `413`: own-image upload exceeds 5 MiB.
- `422`: malformed JSON, form, multipart shape, or invalid schema field values such as email.
  Unknown JSON fields are ignored and do not independently produce 422.

## Removed endpoint families

The following must not appear in OpenAPI or route registration:

- `/groups` and all group membership routes;
- `/users` list and `/{user_id}` get/edit/delete/image routes;
- `/users/change_role/{user_id}`;
- `/users/change_block_state/{user_id}`.

Calls to those paths produce the framework's normal missing-route response and have no side
effects. The absence checks must also cover schemas, dependency factories, use-case exports,
and error mappings so the old behavior cannot be reached through another route.
