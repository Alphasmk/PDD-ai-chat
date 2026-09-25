import pytest
from httpx import AsyncClient
from fastapi import status
from source.domain.value_objects import ID
from source.presentation.api.schemas.auth import UserSignupRequest


@pytest.mark.asyncio(loop_scope="session")
class TestGetUsers:
    async def test_success_pagination(self, client: AsyncClient, auth_headers):
        headers = await auth_headers(role="admin")
        unique_id = str(ID().value)[:8]
        signup_payload = UserSignupRequest(
            name="test",
            surname="test",
            username=f"testuser_{unique_id}",
            password="Test1234",
            email=f"testuser_{unique_id}@email.com",
        )
        await client.post("/api/v1/auth/signup", json=signup_payload.model_dump())

        params = {"limit": 10, "page": 1, "order_by": "asc"}

        response = await client.get("/api/v1/users", params=params, headers=headers)

        assert response.status_code == status.HTTP_200_OK
        data = response.json()

        assert isinstance(data, list)
        assert len(data) <= 10

        if len(data) > 0:
            assert "id" in data[0]
            assert "username" in data[0]
            usernames_in_response = [user["username"] for user in data]
            assert f"testuser_{unique_id}" in usernames_in_response
