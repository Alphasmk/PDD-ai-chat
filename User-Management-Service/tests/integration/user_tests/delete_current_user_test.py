from httpx import AsyncClient
from tests.integration.conftest import account, response_data


async def test_delete_only_own_account(client: AsyncClient) -> None:
    alice, bob = await account(client), await account(client, "bob")
    assert (await client.delete("/api/v1/users/me")).status_code == 401
    response = await client.delete(
        "/api/v1/users/me", headers=alice.headers, params={"id": bob.id}
    )
    assert response.status_code == 200 and response_data(response) == {
        "id": alice.id,
        "username": "alice",
        "email": "alice@example.com",
    }
    assert (
        await client.get("/api/v1/users/me", headers=bob.headers)
    ).status_code == 200
    assert (
        await client.delete("/api/v1/users/me", headers=alice.headers)
    ).status_code == 404
