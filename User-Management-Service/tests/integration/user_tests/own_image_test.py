import pytest
from httpx import AsyncClient
from tests.adapters.storage import FakeStorage
from tests.integration.conftest import account, json_string
from source.settings.constansts import MAX_FILE_SIZE


@pytest.mark.parametrize("mime", ["image/jpeg", "image/png", "image/webp"])
async def test_own_image_lifecycle_isolation(
    client: AsyncClient, storage: FakeStorage, mime: str
) -> None:
    alice, bob = await account(client), await account(client, "bob")
    bob_upload = await client.post(
        "/api/v1/users/me/image",
        headers=bob.headers,
        files={"image": ("bob.png", b"bob", "image/png")},
    )
    bob_key = json_string(bob_upload, "image_s3_path")
    upload = await client.post(
        "/api/v1/users/me/image",
        headers=alice.headers,
        params={"user_id": bob.id},
        files={"image": ("alice.img", b"alice", mime)},
    )
    assert upload.status_code == 200
    alice_key = json_string(upload, "image_s3_path")
    await client.patch(
        "/api/v1/users/me", headers=alice.headers, json={"image_s3_path": bob_key}
    )
    get = await client.get(
        "/api/v1/users/me/image", headers=alice.headers, params={"id": bob.id}
    )
    assert get.status_code == 200 and alice_key in json_string(get, "image_url")
    assert storage.signed == [alice_key]
    replace = await client.post(
        "/api/v1/users/me/image",
        headers=alice.headers,
        files={"image": ("replace.png", b"new", "image/png")},
    )
    assert replace.status_code == 200 and alice_key in storage.deleted
    delete = await client.delete(
        "/api/v1/users/me/image", headers=alice.headers, params={"id": bob.id}
    )
    assert delete.status_code == 200 and delete.content == b"null"
    assert (
        await client.get("/api/v1/users/me/image", headers=alice.headers)
    ).status_code == 404
    assert storage.objects[bob_key] == b"bob"
    assert (
        await client.get("/api/v1/users/me/image", headers=bob.headers)
    ).status_code == 200


async def test_upload_limits(client: AsyncClient) -> None:
    alice = await account(client)
    assert (
        await client.post(
            "/api/v1/users/me/image",
            headers=alice.headers,
            files={"image": ("bad.txt", b"x", "text/plain")},
        )
    ).status_code == 400
    assert (
        await client.post(
            "/api/v1/users/me/image",
            headers=alice.headers,
            files={"image": ("large.png", b"x" * (MAX_FILE_SIZE + 1), "image/png")},
        )
    ).status_code == 413
    assert (
        await client.post(
            "/api/v1/users/me/image",
            headers=alice.headers,
            files={"image": ("max.png", b"x" * MAX_FILE_SIZE, "image/png")},
        )
    ).status_code == 200
    assert (
        await client.post("/api/v1/users/me/image", headers=alice.headers)
    ).status_code == 422


@pytest.mark.parametrize("method", ["GET", "POST", "DELETE"])
async def test_missing_invalid_and_deleted_session(
    client: AsyncClient, method: str
) -> None:
    assert (await client.request(method, "/api/v1/users/me/image")).status_code == 401
    assert (
        await client.request(
            method,
            "/api/v1/users/me/image",
            headers={"Authorization": "Bearer invalid"},
        )
    ).status_code == 401
    alice = await account(client)
    await client.delete("/api/v1/users/me", headers=alice.headers)
    assert (
        await client.request(method, "/api/v1/users/me/image", headers=alice.headers)
    ).status_code == 404


async def test_missing_image_and_storage_errors(
    client: AsyncClient, storage: FakeStorage
) -> None:
    alice = await account(client)
    assert (
        await client.get("/api/v1/users/me/image", headers=alice.headers)
    ).status_code == 404
    assert (
        await client.delete("/api/v1/users/me/image", headers=alice.headers)
    ).status_code == 404
    storage.fail_upload = True
    assert (
        await client.post(
            "/api/v1/users/me/image",
            headers=alice.headers,
            files={"image": ("test.png", b"test", "image/png")},
        )
    ).status_code == 400
    storage.fail_upload = False
    assert (
        await client.post(
            "/api/v1/users/me/image",
            headers=alice.headers,
            files={"image": ("test.png", b"test", "image/png")},
        )
    ).status_code == 200
    storage.fail_sign = True
    assert (
        await client.get("/api/v1/users/me/image", headers=alice.headers)
    ).status_code == 400
    storage.fail_delete = True
    assert (
        await client.delete("/api/v1/users/me/image", headers=alice.headers)
    ).status_code == 400
