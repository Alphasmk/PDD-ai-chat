import pytest
from httpx import AsyncClient
from tests.integration.conftest import signup_payload, response_data


@pytest.mark.parametrize("role", ["admin", "superadmin"])
async def test_signup_shape_and_ignored_fields(client: AsyncClient, role: str) -> None:
    payload = {
        **signup_payload(),
        "role": role,
        "group_id": "old",
        "is_blocked": True,
        "is_superadmin": True,
        "image_s3_path": "foreign",
    }
    response = await client.post("/api/v1/auth/signup", json=payload)
    assert response.status_code == 201
    data = response_data(response)
    assert set(data) == {
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
    assert data["updated_at"] is None
    assert (
        data["role"] == "user"
        and data["is_blocked"] is False
        and data["is_superadmin"] is False
    )


@pytest.mark.parametrize(
    "field,value,status",
    [
        ("name", "A", 400),
        ("surname", "bad name", 400),
        ("password", "short", 400),
        ("email", "invalid", 422),
    ],
)
async def test_invalid_signup(
    client: AsyncClient, field: str, value: str, status: int
) -> None:
    payload = signup_payload()
    payload[field] = value
    assert (
        await client.post("/api/v1/auth/signup", json=payload)
    ).status_code == status
    assert (
        await client.post("/api/v1/auth/signup", json=signup_payload())
    ).status_code == 201


@pytest.mark.parametrize("field", ["username", "email", "phone_number"])
async def test_unique_conflicts(client: AsyncClient, field: str) -> None:
    first = {**signup_payload(), "phone_number": "123"}
    assert (await client.post("/api/v1/auth/signup", json=first)).status_code == 201
    second = {**signup_payload("bob"), "phone_number": "456"}
    second[field] = first[field]
    assert (await client.post("/api/v1/auth/signup", json=second)).status_code == 409


async def test_malformed_signup(client: AsyncClient) -> None:
    assert (await client.post("/api/v1/auth/signup", json={})).status_code == 422
