from uuid import uuid4
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncEngine
from source.domain.value_objects.user_role import UserRole
from tests.integration.conftest import seeded_account


async def test_block_contract_and_demoted_actor(
    client: AsyncClient, engine: AsyncEngine
) -> None:
    owner = await seeded_account(
        client, engine, "owner", UserRole.ADMIN, is_superadmin=True
    )
    admin = await seeded_account(client, engine, "admin", UserRole.ADMIN)
    user = await seeded_account(client, engine, "alice")
    assert (
        await client.post(f"/api/v1/users/{uuid4()}/block", headers=user.headers)
    ).status_code == 403
    assert (await client.post(f"/api/v1/users/{user.id}/block")).status_code == 401
    assert (
        await client.post(f"/api/v1/users/{owner.id}/block", headers=admin.headers)
    ).status_code == 409
    assert (
        await client.post(f"/api/v1/users/{admin.id}/block", headers=admin.headers)
    ).status_code == 409
    assert (
        await client.post(f"/api/v1/users/{uuid4()}/block", headers=admin.headers)
    ).json() == {"error": "user_not_found"}
    assert (
        await client.post("/api/v1/users/bad/block", headers=admin.headers)
    ).status_code == 422
    for _ in range(2):
        response = await client.post(
            f"/api/v1/users/{user.id}/block", headers=admin.headers
        )
        assert response.status_code == 200 and response.json() == {
            "id": user.id,
            "role": "user",
            "is_blocked": True,
            "is_superadmin": False,
        }
    await client.patch(
        f"/api/v1/users/{admin.id}/role", headers=owner.headers, json={"role": "user"}
    )
    assert (
        await client.post(f"/api/v1/users/{user.id}/block", headers=admin.headers)
    ).status_code == 403
    assert (
        await client.post(f"/api/v1/users/{admin.id}/block", headers=owner.headers)
    ).status_code == 200
