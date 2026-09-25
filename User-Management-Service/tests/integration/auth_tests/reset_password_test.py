import pytest
from httpx import AsyncClient
from fastapi import status


@pytest.mark.asyncio(loop_scope="session")
class TestResetPassword:
    async def test_success(self, client: AsyncClient):
        reset_payload = {"email": "testuser@gmail.com"}

        response = await client.post("/api/v1/auth/reset-password", json=reset_payload)

        assert response.status_code == status.HTTP_200_OK
        response_data = response.json()
        assert (
            response_data["message"]
            == "Password reset link has been sent to your email"
        )
