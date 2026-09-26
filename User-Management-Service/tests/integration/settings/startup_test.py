"""Acceptance check for the production container and its entry script."""

import os
import json
import pytest
from httpx import AsyncClient
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from source.infrastructure.database.models import User
from tests.integration.conftest import account, response_data, json_string


async def test_container_fresh_startup() -> None:
    url, postgres_url = (
        os.getenv("UMS_TEST_APP_URL"),
        os.getenv("UMS_TEST_POSTGRES_URL"),
    )
    if not url or not postgres_url:
        pytest.skip(
            "Set UMS_TEST_APP_URL and UMS_TEST_POSTGRES_URL for the startup compose profile"
        )
    engine = create_async_engine(postgres_url)
    try:
        async with AsyncSession(engine) as database:
            assert await database.scalar(select(func.count()).select_from(User)) == 0
        async with AsyncClient(base_url=url) as client:
            assert (await client.get("/healthcheck")).status_code == 200
            document = json.dumps(
                response_data(await client.get("/openapi.json"))
            ).lower()
            assert all(
                term not in document
                for term in ("group_id", "is_blocked", "change_role", "super_admin")
            )
            alice = await account(client, "startupalice")
            bob = await account(client, "startupbob")
            try:
                own = await client.get("/api/v1/users/me", headers=alice.headers)
                assert own.status_code == 200 and response_data(own)["id"] == alice.id
                response = await client.patch(
                    "/api/v1/users/me",
                    headers=alice.headers,
                    json={"name": "Jane", "id": bob.id, "image_s3_path": "foreign"},
                )
                assert (
                    response.status_code == 200
                    and response_data(response)["image_s3_path"] is None
                )
                assert (
                    response_data(
                        await client.get("/api/v1/users/me", headers=bob.headers)
                    )["name"]
                    == "Alice"
                )
                client.cookies.clear()
                client.cookies.set("refresh_token", alice.refresh)
                first = await client.post(
                    "/api/v1/auth/refresh-token", headers=alice.headers
                )
                assert (
                    first.status_code == 200
                    and json_string(first, "refresh_token") != alice.refresh
                )
                second = await client.post(
                    "/api/v1/auth/refresh-token", headers=alice.headers
                )
                assert second.status_code == 200
                client.cookies.clear()
                client.cookies.set("refresh_token", alice.refresh)
                assert (
                    await client.post(
                        "/api/v1/auth/refresh-token", headers=alice.headers
                    )
                ).status_code == 401
                assert (
                    await client.get(f"/api/v1/users/{bob.id}", headers=alice.headers)
                ).status_code == 404
                assert (
                    await client.post(
                        "/api/v1/auth/reset-password",
                        json={"email": "startupalice@example.com"},
                    )
                ).status_code == 200
            finally:
                assert (
                    await client.delete("/api/v1/users/me", headers=alice.headers)
                ).status_code == 200
                assert (
                    await client.delete("/api/v1/users/me", headers=bob.headers)
                ).status_code == 200
        async with AsyncSession(engine) as database:
            assert await database.scalar(select(func.count()).select_from(User)) == 0
    finally:
        await engine.dispose()
