import pytest
from httpx import AsyncClient
from source.infrastructure.jwt import TokenProvider
from tests.integration.conftest import account, response_data


async def test_reads_only_own_profile(client: AsyncClient) -> None:
    alice, bob = await account(client), await account(client, "bob")
    response = await client.get(
        "/api/v1/users/me", headers=alice.headers, params={"user_id": bob.id}
    )
    assert response.status_code == 200
    assert response_data(response)["id"] == alice.id
    assert set(response_data(response)) == {
        "id",
        "name",
        "surname",
        "username",
        "email",
        "phone_number",
        "image_s3_path",
        "created_at",
        "updated_at",
    }


@pytest.mark.parametrize("header", [None, "Bearer invalid"])
async def test_missing_invalid_auth(client: AsyncClient, header: str | None) -> None:
    headers = {"Authorization": header} if header else {}
    assert (await client.get("/api/v1/users/me", headers=headers)).status_code == 401


async def test_expired_and_deleted_subject(client: AsyncClient) -> None:
    alice = await account(client)
    expired = TokenProvider("isolated-http-test-secret-32-characters", "HS256", -1, 7)
    token = await expired.create_access_token(
        {"sub": alice.id, "email": "alice@example.com"}
    )
    assert (
        await client.get(
            "/api/v1/users/me", headers={"Authorization": f"Bearer {token}"}
        )
    ).status_code == 401
    assert (
        await client.delete("/api/v1/users/me", headers=alice.headers)
    ).status_code == 200
    assert (
        await client.get("/api/v1/users/me", headers=alice.headers)
    ).status_code == 404
