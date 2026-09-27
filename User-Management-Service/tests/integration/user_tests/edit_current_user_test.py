import pytest
from httpx import AsyncClient
from tests.integration.conftest import account, response_data


async def test_patch_ignores_foreign_targets_keys_and_legacy(
    client: AsyncClient,
) -> None:
    alice, bob = await account(client), await account(client, "bob")
    before = response_data(await client.get("/api/v1/users/me", headers=bob.headers))
    response = await client.patch(
        "/api/v1/users/me",
        headers=alice.headers,
        json={
            "name": "Jane",
            "id": bob.id,
            "user_id": bob.id,
            "image_s3_path": "bob-key",
            "role": "admin",
            "group_id": "legacy",
            "is_blocked": True,
            "is_superadmin": True,
        },
    )
    assert response.status_code == 200
    data = response_data(response)
    assert set(data) == {
        "name",
        "surname",
        "username",
        "email",
        "phone_number",
        "role",
        "is_blocked",
        "is_superadmin",
    }
    assert data["name"] == "Jane"
    assert (
        data["role"] == "user"
        and data["is_blocked"] is False
        and data["is_superadmin"] is False
    )
    assert (
        response_data(await client.get("/api/v1/users/me", headers=bob.headers))
        == before
    )
    assert (
        await client.patch("/api/v1/users/me", headers=alice.headers, json={})
    ).status_code == 200


async def test_only_legacy_fields_do_not_change_profile(client: AsyncClient) -> None:
    alice = await account(client)
    before = response_data(await client.get("/api/v1/users/me", headers=alice.headers))
    response = await client.patch(
        "/api/v1/users/me",
        headers=alice.headers,
        json={"image_s3_path": "legacy", "image_url": "legacy", "id": "foreign"},
    )
    assert response.status_code == 200
    assert "image_s3_path" not in response_data(response)
    assert "image_url" not in response_data(response)
    assert (
        response_data(await client.get("/api/v1/users/me", headers=alice.headers))
        == before
    )


@pytest.mark.parametrize(
    "field,value,status",
    [("name", "A", 400), ("surname", "bad name", 400), ("email", "invalid", 422)],
)
async def test_validation(
    client: AsyncClient, field: str, value: str, status: int
) -> None:
    alice = await account(client)
    assert (
        await client.patch(
            "/api/v1/users/me", headers=alice.headers, json={field: value}
        )
    ).status_code == status


@pytest.mark.parametrize("field", ["username", "email", "phone_number"])
async def test_update_conflicts(client: AsyncClient, field: str) -> None:
    alice, bob = await account(client), await account(client, "bob")
    assert (
        await client.patch(
            "/api/v1/users/me", headers=bob.headers, json={"phone_number": "123"}
        )
    ).status_code == 200
    value = {"username": "bob", "email": "bob@example.com", "phone_number": "123"}[
        field
    ]
    assert (
        await client.patch(
            "/api/v1/users/me", headers=alice.headers, json={field: value}
        )
    ).status_code == 409


async def test_missing_auth_deleted_subject(client: AsyncClient) -> None:
    assert (await client.patch("/api/v1/users/me", json={})).status_code == 401
    alice = await account(client)
    await client.delete("/api/v1/users/me", headers=alice.headers)
    assert (
        await client.patch("/api/v1/users/me", headers=alice.headers, json={})
    ).status_code == 404
