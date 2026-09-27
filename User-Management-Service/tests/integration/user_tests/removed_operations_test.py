import json
import pytest
from httpx import AsyncClient
from source.main import app
from tests.integration.conftest import account, response_data


@pytest.mark.parametrize("authorized", [False, True])
@pytest.mark.parametrize(
    "method,path",
    [
        ("POST", "/users/me/image"),
        ("GET", "/users/me/image"),
        ("DELETE", "/users/me/image"),
        ("GET", "/users/{user}"),
        ("PATCH", "/users/{user}"),
        ("DELETE", "/users/{user}"),
        ("POST", "/users/{user}/image"),
        ("GET", "/users/{user}/image"),
        ("DELETE", "/users/{user}/image"),
        ("POST", "/users/change_role/{user}"),
        ("POST", "/users/change_block_state/{user}"),
        ("POST", "/users/{user}/unblock"),
    ],
)
async def test_removed_operations_no_disclosure_mutation(
    client: AsyncClient, method: str, path: str, authorized: bool
) -> None:
    alice, bob = await account(client), await account(client, "bob")
    before_a = response_data(
        await client.get("/api/v1/users/me", headers=alice.headers)
    )
    before_b = response_data(await client.get("/api/v1/users/me", headers=bob.headers))
    response = await client.request(
        method,
        "/api/v1" + path.format(user=bob.id),
        headers=alice.headers if authorized else {},
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
        ("/healthcheck", "get"),
        ("/api/v1/roles", "get"),
        ("/api/v1/users", "get"),
        ("/api/v1/users/{user_id}/role", "patch"),
        ("/api/v1/users/{user_id}/block", "post"),
    }
    assert actual == expected
    document = json.dumps(schema)
    for removed in (
        "group_id",
        "Pagination",
        "ImageResponse",
        "ImageUploadResponse",
        "image_s3_path",
        "image_url",
    ):
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
