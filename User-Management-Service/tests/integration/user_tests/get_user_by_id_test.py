import pytest
from httpx import AsyncClient
from fastapi import status
from source.presentation.api.schemas.auth import UserSignupRequest
from source.domain.value_objects import ID


@pytest.mark.asyncio(loop_scope="session")
class TestGetUserById:
    async def test_success(self, client: AsyncClient, auth_headers):
        admin_headers = await auth_headers(role="admin")

        unique_id = str(ID().value)[:8]
        signup_payload = UserSignupRequest(
            name="Target",
            surname="User",
            username=f"target_{unique_id}",
            password="Test1234",
            email=f"target_{unique_id}@email.com",
        )
        signup_response = await client.post(
            "/api/v1/auth/signup", json=signup_payload.model_dump()
        )
        assert signup_response.status_code in (
            status.HTTP_200_OK,
            status.HTTP_201_CREATED,
        )
        target_user_id = signup_response.json()["id"]

        get_response = await client.get(
            f"/api/v1/users/{target_user_id}", headers=admin_headers
        )

        assert get_response.status_code == status.HTTP_200_OK
        user_data = get_response.json()
        assert user_data["id"] == target_user_id
        assert user_data["username"] == signup_payload.username
        assert user_data["email"] == signup_payload.email
