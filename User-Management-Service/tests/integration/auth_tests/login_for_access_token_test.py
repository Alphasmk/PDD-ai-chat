import pytest
from httpx import AsyncClient
from fastapi import status
from source.presentation.api.schemas.auth import UserSignupRequest


@pytest.mark.asyncio(loop_scope="session")
class TestLoginUser:
    async def test_success(self, client: AsyncClient):
        signup_payload = UserSignupRequest(
            name="testuser",
            surname="testuser",
            username="testuser",
            password="Test1234",
            email="test_email@email.com",
        )
        await client.post("/api/v1/auth/signup", json=signup_payload.model_dump())

        login_data = {"username": "testuser", "password": "Test1234"}

        response = await client.post("/api/v1/auth/login", data=login_data)

        assert response.status_code == status.HTTP_200_OK
        json_data = response.json()
        assert "access_token" in json_data
        assert "refresh_token" in json_data
        assert json_data["token_type"] == "bearer"

        assert "refresh_token" in response.cookies
        assert response.cookies["refresh_token"] == json_data["refresh_token"]
