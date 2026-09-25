import pytest
from httpx import AsyncClient
from fastapi import status
from source.domain.value_objects import ID
from source.presentation.api.schemas.auth import UserSignupRequest


@pytest.mark.asyncio(loop_scope="session")
class TestGetUsersInGroup:
    async def test_success(self, client: AsyncClient, auth_headers):

        admin_headers = await auth_headers(role="admin")

        group_response = await client.post(
            "/api/v1/groups",
            params={"group_name": "Get Users Group"},
            headers=admin_headers,
        )
        group_id = group_response.json()["id"]

        unique_id = str(ID().value)[:8]
        signup_payload = UserSignupRequest(
            name="user",
            surname="user",
            username=f"user__{unique_id}",
            password="Test1234",
            email=f"user_{unique_id}@email.com",
        )
        signup_response = await client.post(
            "/api/v1/auth/signup", json=signup_payload.model_dump()
        )
        target_user_id = signup_response.json()["id"]

        await client.post(
            f"/api/v1/groups/{group_id}/users/{target_user_id}", headers=admin_headers
        )

        get_response = await client.get(
            f"/api/v1/groups/{group_id}/users", headers=admin_headers
        )
        assert get_response.status_code == status.HTTP_200_OK
        users_list = get_response.json()
        assert isinstance(users_list, list)
        found_target_user = next(
            (user for user in users_list if user["id"] == target_user_id), None
        )
        assert found_target_user is not None
        assert found_target_user["username"] == signup_payload.username
