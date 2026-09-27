from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncEngine
from source.domain.value_objects.user_role import UserRole
from tests.integration.conftest import seeded_account


async def test_roles_and_protected_deletion(
    client: AsyncClient, engine: AsyncEngine
) -> None:
    owner = await seeded_account(
        client, engine, "owner", UserRole.ADMIN, is_superadmin=True
    )
    roles = await client.get("/api/v1/roles", headers=owner.headers)
    assert roles.status_code == 200
    assert roles.json() == {
        "items": [
            {"value": "user", "label": "Пользователь"},
            {"value": "admin", "label": "Администратор"},
        ]
    }
    response = await client.delete("/api/v1/users/me", headers=owner.headers)
    assert response.status_code == 409 and response.json() == {
        "error": "protected_account"
    }
    assert (
        await client.get("/api/v1/users/me", headers=owner.headers)
    ).status_code == 200
    updated = await client.patch(
        "/api/v1/users/me",
        headers=owner.headers,
        json={"name": "Jane", "role": "user", "is_superadmin": False},
    )
    assert updated.status_code == 200
    assert updated.json()["role"] == "admin"
    assert updated.json()["is_superadmin"] is True
    assert updated.json()["name"] == "Jane"


async def test_roles_require_valid_identity(
    client: AsyncClient, engine: AsyncEngine
) -> None:
    assert (await client.get("/api/v1/roles")).status_code == 401
    user = await seeded_account(client, engine, "reader")
    assert (await client.get("/api/v1/roles", headers=user.headers)).status_code == 200
