import pytest
from httpx import AsyncClient
from source.infrastructure.jwt import TokenProvider
from tests.integration.conftest import account, response_data


async def test_login_claims_cookie(
    client: AsyncClient, provider: TokenProvider
) -> None:
    user = await account(client)
    assert set(await provider.decode_token(user.access)) == {"sub", "email", "exp"}
    assert set(await provider.decode_token(user.refresh)) == {"sub", "exp", "jti"}
    response = await client.post(
        "/api/v1/auth/login", data={"username": "alice", "password": "Test1234"}
    )
    assert set(response_data(response)) == {
        "access_token",
        "refresh_token",
        "token_type",
    }
    assert response_data(response)["token_type"] == "bearer"
    assert "httponly" in response.headers["set-cookie"].lower()


@pytest.mark.parametrize(
    "username,password", [("missing", "Test1234"), ("alice", "wrong")]
)
async def test_invalid_login(client: AsyncClient, username: str, password: str) -> None:
    await account(client)
    response = await client.post(
        "/api/v1/auth/login", data={"username": username, "password": password}
    )
    assert response.status_code == 401
    assert "set-cookie" not in response.headers


async def test_malformed_form(client: AsyncClient) -> None:
    assert (await client.post("/api/v1/auth/login", data={})).status_code == 422
