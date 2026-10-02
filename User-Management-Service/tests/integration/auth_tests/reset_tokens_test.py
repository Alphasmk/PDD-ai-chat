from datetime import datetime, timezone
from unittest.mock import patch
import pytest
from httpx import AsyncClient
from source.infrastructure.jwt import TokenProvider
from tests.integration.conftest import account, json_string


async def test_same_second_rotation_cookie_replay(client: AsyncClient) -> None:
    user = await account(client)
    with patch("source.infrastructure.jwt.token_provider.datetime") as clock:
        clock.now.return_value = datetime.now(timezone.utc)
        first = await client.post("/api/v1/auth/refresh-token", headers=user.headers)
        assert first.status_code == 200, first.text
        new = json_string(first, "refresh_token")
        assert new != user.refresh
        assert "httponly" in first.headers["set-cookie"].lower()
        second = await client.post("/api/v1/auth/refresh-token", headers=user.headers)
        assert second.status_code == 200 and json_string(second, "refresh_token") != new
    client.cookies.set("refresh_token", user.refresh)
    assert (
        await client.post("/api/v1/auth/refresh-token", headers=user.headers)
    ).status_code == 401


async def test_expired_access_header_is_sufficient(client: AsyncClient) -> None:
    user = await account(client)
    expired = TokenProvider("isolated-http-test-secret-32-characters", "HS256", -1, 7)
    token = await expired.create_access_token(
        {"sub": user.id, "email": "alice@example.com"}
    )
    assert (
        await client.post(
            "/api/v1/auth/refresh-token", headers={"Authorization": f"Bearer {token}"}
        )
    ).status_code == 200


@pytest.mark.parametrize("cookie", [None, "malformed"])
async def test_invalid_cookie(client: AsyncClient, cookie: str | None) -> None:
    user = await account(client)
    client.cookies.clear()
    if cookie:
        client.cookies.set("refresh_token", cookie)
    assert (
        await client.post("/api/v1/auth/refresh-token", headers=user.headers)
    ).status_code == 401


async def test_missing_bearer_deleted_subject(client: AsyncClient) -> None:
    user = await account(client)
    assert (await client.post("/api/v1/auth/refresh-token")).status_code == 401
    assert (
        await client.delete("/api/v1/users/me", headers=user.headers)
    ).status_code == 200
    assert (
        await client.post("/api/v1/auth/refresh-token", headers=user.headers)
    ).status_code == 404


async def test_expired_refresh_and_access_cookie(client: AsyncClient) -> None:
    user = await account(client)
    expired = TokenProvider("isolated-http-test-secret-32-characters", "HS256", 15, -1)
    expired_refresh = await expired.create_refresh_token({"sub": user.id})
    for invalid_cookie in (expired_refresh, user.access):
        client.cookies.clear()
        client.cookies.set("refresh_token", invalid_cookie)
        response = await client.post("/api/v1/auth/refresh-token", headers=user.headers)
        assert response.status_code == 401
        assert "set-cookie" not in response.headers
