import json
import pytest
from httpx import AsyncClient
from source.main import app
from tests.integration.conftest import account, response_data
from tests.adapters.storage import FakeStorage


@pytest.mark.parametrize(
    "method,path",
    [
        ("GET", "/users"),
        ("GET", "/users/{user}"),
        ("PATCH", "/users/{user}"),
        ("DELETE", "/users/{user}"),
        ("POST", "/users/{user}/image"),
        ("GET", "/users/{user}/image"),
        ("DELETE", "/users/{user}/image"),
        ("POST", "/users/change_role/{user}"),
        ("POST", "/users/change_block_state/{user}"),
    ],
)
async def test_removed_operations_no_disclosure_mutation(
    client: AsyncClient, storage: FakeStorage, method: str, path: str
) -> None:
    alice, bob = await account(client), await account(client, "bob")
    before_a = response_data(
        await client.get("/api/v1/users/me", headers=alice.headers)
    )
    before_b = response_data(await client.get("/api/v1/users/me", headers=bob.headers))
    response = await client.request(
        method,
        "/api/v1" + path.format(user=bob.id),
        headers=alice.headers,
        json={"name": "Other", "role": "admin"},
    )
    assert response.status_code == 404
    assert (
        response_data(await client.get("/api/v1/users/me", headers=alice.headers))
        == before_a
    )
    assert (
        response_data(await client.get("/api/v1/users/me", headers=bob.headers))
        == before_b
    )
    assert not storage.objects and not storage.signed and not storage.deleted


def test_exact_openapi_surface_and_input_fields() -> None:
    schema = app.openapi()
    paths: object = schema["paths"]
    assert isinstance(paths, dict)
    actual = {(path, method) for path, methods in paths.items() for method in methods}
    expected = {
        ("/api/v1/auth/signup", "post"),
        ("/api/v1/auth/login", "post"),
        ("/api/v1/auth/refresh-token", "post"),
        ("/api/v1/auth/reset-password", "post"),
        ("/api/v1/users/me", "get"),
        ("/api/v1/users/me", "patch"),
        ("/api/v1/users/me", "delete"),
        ("/api/v1/users/me/image", "get"),
        ("/api/v1/users/me/image", "post"),
        ("/api/v1/users/me/image", "delete"),
        ("/healthcheck", "get"),
    }
    assert actual == expected
    document = json.dumps(schema)
    for removed in ("group_id", "is_blocked", "UserRole", "ChangeRole", "Pagination"):
        assert removed not in document
    from source.presentation.api.schemas.user import UserEditRequest
    from source.presentation.api.schemas.auth import UserSignupRequest

    assert set(UserEditRequest.model_fields) == {
        "name",
        "surname",
        "username",
        "email",
        "phone_number",
    }
    assert set(UserSignupRequest.model_fields) == {
        "name",
        "surname",
        "username",
        "password",
        "email",
        "phone_number",
    }
