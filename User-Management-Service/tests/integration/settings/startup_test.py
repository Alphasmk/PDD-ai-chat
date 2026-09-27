"""Acceptance check for the production container and its entry script."""

import os
import json
import pytest
import asyncio
import subprocess
from uuid import uuid4
from httpx import AsyncClient, HTTPError
from sqlalchemy import select, func, delete
from uuid import UUID
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
            assert await database.scalar(select(func.count()).select_from(User)) == 1
            owner = (await database.execute(select(User))).scalar_one()
            assert owner.role_id == 2 and owner.is_superadmin and not owner.is_blocked
        async with AsyncClient(base_url=url) as client:
            assert (await client.get("/healthcheck")).status_code == 200
            document = json.dumps(
                response_data(await client.get("/openapi.json"))
            ).lower()
            assert all(
                term not in document
                for term in (
                    "group_id",
                    "super_admin",
                    "image_s3_path",
                    "image_url",
                    "imageresponse",
                    "imageuploadresponse",
                    "/me/image",
                )
            )
            alice = await account(client, "startupalice")
            bob = await account(client, "startupbob")
            try:
                own = await client.get("/api/v1/users/me", headers=alice.headers)
                assert own.status_code == 200 and response_data(own)["id"] == alice.id
                assert set(response_data(own)) == {
                    "id",
                    "name",
                    "surname",
                    "username",
                    "email",
                    "phone_number",
                    "created_at",
                    "updated_at",
                    "role",
                    "is_blocked",
                    "is_superadmin",
                }
                for headers in ({}, alice.headers):
                    for method in ("POST", "GET", "DELETE"):
                        removed = await client.request(
                            method, "/api/v1/users/me/image", headers=headers
                        )
                        assert removed.status_code == 404
                response = await client.patch(
                    "/api/v1/users/me",
                    headers=alice.headers,
                    json={"name": "Jane", "id": bob.id, "image_s3_path": "foreign"},
                )
                assert (
                    response.status_code == 200
                    and "image_s3_path" not in response_data(response)
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
            assert await database.scalar(select(func.count()).select_from(User)) == 1
    finally:
        await engine.dispose()


async def test_container_block_persists_after_restart() -> None:
    url = os.environ.get("UMS_TEST_APP_URL")
    docker = os.environ.get("UMS_TEST_DOCKER")
    project = os.environ.get("UMS_TEST_COMPOSE_PROJECT")
    password = os.environ.get("UMS_TEST_SUPERADMIN_PASSWORD")
    username = os.environ.get("UMS_TEST_SUPERADMIN_USERNAME")
    if not all((url, docker, project, password, username)):
        pytest.skip(
            "Disposable container and explicit test bootstrap credentials required"
        )
    assert url is not None and docker is not None and project is not None
    assert username is not None and password is not None
    assert project.startswith("ums-")
    env_file = os.environ.get("UMS_TEST_COMPOSE_ENV_FILE", ".env.test")
    async with AsyncClient(base_url=url) as client:
        login = await client.post(
            "/api/v1/auth/login", data={"username": username, "password": password}
        )
        assert login.status_code == 200
        owner_headers = {
            "Authorization": "Bearer " + json_string(login, "access_token")
        }
        target = await account(client, "blocked" + uuid4().hex[:8])
        assert (
            await client.post(f"/api/v1/users/{target.id}/block", headers=owner_headers)
        ).status_code == 200
        command = [
            docker,
            "compose",
            "--env-file",
            env_file,
            "-p",
            project,
            "-f",
            "docker-compose.test.yaml",
            "--profile",
            "startup",
            "restart",
            "app_test",
        ]
        result = await asyncio.to_thread(
            subprocess.run,
            command,
            capture_output=True,
            timeout=30,
            creationflags=subprocess.CREATE_NO_WINDOW if os.name == "nt" else 0,
        )
        assert result.returncode == 0
        for _ in range(40):
            try:
                if (await client.get("/healthcheck")).status_code == 200:
                    break
            except HTTPError:
                pass
            await asyncio.sleep(0.5)
        else:
            pytest.fail("Disposable application did not become ready after restart")
        assert (
            await client.get("/api/v1/users/me", headers=target.headers)
        ).status_code == 403
        response = await client.get("/api/v1/users", headers=owner_headers)
        assert response.status_code == 200
        items = response_data(response)["items"]
        assert isinstance(items, list)
        assert any(
            isinstance(item, dict)
            and item.get("id") == target.id
            and item.get("is_blocked") is True
            for item in items
        )
        assert (
            await client.post(
                "/api/v1/auth/login",
                data={"username": target.username, "password": "Test1234"},
            )
        ).status_code == 403
        postgres_url = os.environ.get("UMS_TEST_POSTGRES_URL")
        assert postgres_url is not None
        cleanup_engine = create_async_engine(postgres_url)
        try:
            async with AsyncSession(cleanup_engine) as session:
                # Blocked users cannot delete themselves; clean only this test-owned row.
                await session.execute(
                    delete(User).where(
                        User.id == UUID(target.id), User.username == target.username
                    )
                )
                await session.commit()
        finally:
            await cleanup_engine.dispose()
