from datetime import datetime
from uuid import uuid4
import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncEngine, AsyncSession
from source.infrastructure.database.models import User
from source.domain.value_objects.user_role import UserRole
from tests.integration.conftest import seeded_account


@pytest.mark.parametrize("limit", [50, 100])
async def test_125_accounts_stable_pagination(
    client: AsyncClient, engine: AsyncEngine, limit: int
) -> None:
    owner = await seeded_account(
        client, engine, "owner", UserRole.ADMIN, is_superadmin=True
    )
    admin = await seeded_account(client, engine, "admin", UserRole.ADMIN)
    async with AsyncSession(engine) as session:
        session.add_all(
            [
                User(
                    id=uuid4(),
                    name="Alice",
                    surname="Smith",
                    username=f"user{i}",
                    password_hash="not-a-public-secret",
                    email=f"user{i}@example.com",
                    created_at=datetime(2026, 1, 1),
                    role_id=1,
                    is_blocked=i % 2 == 0,
                )
                for i in range(123)
            ]
        )
        await session.commit()
    ids: list[str] = []
    for offset in range(0, 200, limit):
        response = await client.get(
            "/api/v1/users",
            params={"limit": limit, "offset": offset},
            headers=admin.headers,
        )
        assert response.status_code == 200
        data = response.json()
        assert data["limit"] == limit and data["offset"] == offset
        for item in data["items"]:
            assert set(item) == {
                "id",
                "name",
                "surname",
                "username",
                "email",
                "role",
                "is_blocked",
                "is_superadmin",
            }
            ids.append(item["id"])
    assert len(ids) == len(set(ids)) == 125
    assert {owner.id, admin.id} <= set(ids)
    default = (await client.get("/api/v1/users", headers=owner.headers)).json()
    assert default["limit"] == 50 and default["offset"] == 0
    assert (
        await client.get("/api/v1/users", params={"offset": 125}, headers=admin.headers)
    ).json()["items"] == []
    # Rows with equal created_at are ordered by UUID, independent of insertion order.
    assert ids[:123] == sorted(ids[:123])


async def test_list_access_and_old_session_role_changes(
    client: AsyncClient, engine: AsyncEngine
) -> None:
    owner = await seeded_account(
        client, engine, "owner", UserRole.ADMIN, is_superadmin=True
    )
    user = await seeded_account(client, engine, "reader")
    assert (await client.get("/api/v1/users")).status_code == 401
    assert (await client.get("/api/v1/users", headers=user.headers)).status_code == 403
    for role, expected in (("admin", 200), ("user", 403)):
        assert (
            await client.patch(
                f"/api/v1/users/{user.id}/role",
                headers=owner.headers,
                json={"role": role},
            )
        ).status_code == 200
        assert (
            await client.get("/api/v1/users", headers=user.headers)
        ).status_code == expected
        assert (
            await client.get("/api/v1/users/me", headers=user.headers)
        ).status_code == 200
    for params in ({"limit": 0}, {"limit": 101}, {"offset": -1}, {"limit": "x"}):
        response = await client.get(
            "/api/v1/users", params=params, headers=owner.headers
        )
        assert response.status_code == 422 and response.json() == {
            "error": "invalid_request"
        }
