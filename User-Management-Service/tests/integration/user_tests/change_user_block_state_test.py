import pytest
from httpx import AsyncClient
from fastapi import status
from source.domain.value_objects import ID
from source.presentation.api.schemas.auth import UserSignupRequest


@pytest.mark.asyncio(loop_scope="session")
class TestChangeUserBlockState:
    async def test_toggle_block_state_success(self, client: AsyncClient, auth_headers):
        admin_headers = await auth_headers(role="admin")

        unique_id = str(ID().value)[:8]
        signup_payload = UserSignupRequest(
            name="test",
            surname="test",
            username=f"block_target_{unique_id}",
            password="Test1234",
            email=f"block_target_{unique_id}@email.com",
        )
        signup_response = await client.post(
            "/api/v1/auth/signup", json=signup_payload.model_dump()
        )
        target_user_id = signup_response.json()["id"]
        block_response = await client.post(
            f"/api/v1/users/change_block_state/{target_user_id}", headers=admin_headers
        )

        assert block_response.status_code == status.HTTP_200_OK
        block_data = block_response.json()

        assert block_data["message"] == "User successfully blocked"

        unblock_response = await client.post(
            f"/api/v1/users/change_block_state/{target_user_id}", headers=admin_headers
        )

        assert unblock_response.status_code == status.HTTP_200_OK
        unblock_data = unblock_response.json()

        assert unblock_data["message"] == "User successfully unlocked"
