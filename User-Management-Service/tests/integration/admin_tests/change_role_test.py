from uuid import uuid4
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncEngine
from source.domain.value_objects.user_role import UserRole
from tests.integration.conftest import seeded_account


async def test_change_role_contract(client: AsyncClient, engine: AsyncEngine) -> None:
    owner = await seeded_account(
        client, engine, "owner", UserRole.ADMIN, is_superadmin=True
    )
    user = await seeded_account(client, engine, "alice")
    path = f"/api/v1/users/{user.id}/role"
    for payload, error in (
        ({"role": "superadmin"}, "invalid_role"),
        ({"role": "other"}, "invalid_role"),
        ({"role": "admin", "extra": True}, "invalid_request"),
        ({}, "invalid_request"),
    ):
        response = await client.patch(path, headers=owner.headers, json=payload)
        assert response.status_code == 422 and response.json() == {"error": error}
    assert (
        await client.patch(path, headers=owner.headers, json={"role": "admin"})
    ).json() == {
        "id": user.id,
        "role": "admin",
        "is_blocked": False,
        "is_superadmin": False,
    }
    assert (
        await client.patch(path, headers=user.headers, json={"role": "user"})
    ).status_code == 403
    assert (
        await client.patch(
            f"/api/v1/users/{owner.id}/role",
            headers=owner.headers,
            json={"role": "user"},
        )
    ).status_code == 409
    response = await client.patch(
        f"/api/v1/users/{uuid4()}/role", headers=owner.headers, json={"role": "admin"}
    )
    assert response.status_code == 404 and response.json() == {
        "error": "user_not_found"
    }
    assert (
        await client.patch(path, headers=owner.headers, json={"role": "user"})
    ).status_code == 200
    assert (
        await client.patch(
            f"/api/v1/users/{uuid4()}/role",
            headers=user.headers,
            json={"role": "admin"},
        )
    ).status_code == 403
    assert (await client.patch(path, json={"role": "admin"})).status_code == 401
