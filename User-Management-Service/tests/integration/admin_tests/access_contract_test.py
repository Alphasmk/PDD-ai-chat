from dataclasses import dataclass
from uuid import uuid4
import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncEngine, AsyncSession
from sqlalchemy import update
from uuid import UUID
from source.main import app
from source.infrastructure.database.models import User
from source.domain.value_objects.user_role import UserRole
from tests.integration.conftest import seeded_account


@dataclass(frozen=True)
class AccessCase:
    role: UserRole
    blocked: bool
    is_superadmin: bool = False


@pytest.mark.parametrize(
    "case",
    [
        AccessCase(UserRole.USER, False),
        AccessCase(UserRole.ADMIN, False),
        AccessCase(UserRole.ADMIN, False, True),
        AccessCase(UserRole.USER, True),
    ],
)
async def test_access_matrix(
    client: AsyncClient, engine: AsyncEngine, case: AccessCase
) -> None:
    actor = await seeded_account(
        client, engine, "actor", case.role, is_superadmin=case.is_superadmin
    )
    target = await seeded_account(client, engine, "target")
    if case.blocked:
        async with AsyncSession(engine) as session:
            await session.execute(
                update(User).where(User.id == UUID(actor.id)).values(is_blocked=True)
            )
            await session.commit()
    admin_status = 200 if case.role is UserRole.ADMIN and not case.blocked else 403
    profile_status = 403 if case.blocked else 200
    assert (
        await client.get("/api/v1/roles", headers=actor.headers)
    ).status_code == profile_status
    assert (
        await client.get("/api/v1/users", headers=actor.headers)
    ).status_code == admin_status
    assert (
        await client.get("/api/v1/users/me", headers=actor.headers)
    ).status_code == profile_status
    assert (
        await client.patch("/api/v1/users/me", headers=actor.headers, json={})
    ).status_code == profile_status
    role_status = 200 if case.is_superadmin and not case.blocked else 403
    assert (
        await client.patch(
            f"/api/v1/users/{target.id}/role",
            headers=actor.headers,
            json={"role": "user"},
        )
    ).status_code == role_status
    assert (
        await client.post(f"/api/v1/users/{target.id}/block", headers=actor.headers)
    ).status_code == admin_status
    # Protected target and unknown target are indistinguishable to an unauthorized actor.
    if admin_status == 403:
        for target_id in (target.id, str(uuid4())):
            response = await client.post(
                f"/api/v1/users/{target_id}/block", headers=actor.headers
            )
            assert response.status_code == 403
    deletion = await client.delete("/api/v1/users/me", headers=actor.headers)
    assert deletion.status_code == (
        403 if case.blocked else 409 if case.is_superadmin else 200
    )


def test_openapi_role_and_error_contracts() -> None:
    document = app.openapi()
    schemas = document["components"]["schemas"]
    assert schemas["UserRole"]["enum"] == ["user", "admin"]
    assert schemas["ChangeRoleRequest"]["properties"]["role"]["enum"] == [
        "user",
        "admin",
    ]
    assert schemas["ChangeRoleRequest"]["additionalProperties"] is False
    assert set(schemas["AdminUserResponse"]["properties"]) == {
        "id",
        "name",
        "surname",
        "username",
        "email",
        "role",
        "is_blocked",
        "is_superadmin",
    }
    for path, method in (
        ("/api/v1/users", "get"),
        ("/api/v1/users/{user_id}/role", "patch"),
        ("/api/v1/users/{user_id}/block", "post"),
    ):
        assert {"401", "403", "404", "409", "422", "503"} <= set(
            document["paths"][path][method]["responses"]
        )
