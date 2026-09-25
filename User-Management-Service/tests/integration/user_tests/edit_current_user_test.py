import pytest
from httpx import AsyncClient
from fastapi import status


@pytest.mark.asyncio(loop_scope="session")
class TestEditCurrentUser:
    async def test_success(self, client: AsyncClient, auth_headers):
        headers = await auth_headers()

        edit_payload = {"name": "UpdatedName", "surname": "UpdatedSurname"}
        response = await client.patch(
            "/api/v1/users/me", json=edit_payload, headers=headers
        )

        assert response.status_code == status.HTTP_200_OK

        response_data = response.json()
        assert response_data["name"] == "UpdatedName"
        assert response_data["surname"] == "UpdatedSurname"

        check_response = await client.get("/api/v1/users/me", headers=headers)
        assert check_response.json()["name"] == "UpdatedName"
