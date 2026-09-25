import pytest
from httpx import AsyncClient
from fastapi import status


@pytest.mark.asyncio(loop_scope="session")
class TestGetCurrentUser:
    async def test_success(self, client: AsyncClient, auth_headers):

        user_headers = await auth_headers()

        edit_payload = {"name": "Updatedname", "surname": "Updatedsurname"}

        response = await client.patch(
            "/api/v1/users/me", json=edit_payload, headers=user_headers
        )

        assert response.status_code == status.HTTP_200_OK

        updated_data = response.json()
        assert updated_data["name"] == "Updatedname"
        assert updated_data["surname"] == "Updatedsurname"
