import pytest
from httpx import AsyncClient
from fastapi import status
from sqlalchemy import select
from source.domain.value_objects import ID
from source.domain.enums.user_role import UserRole
from source.presentation.api.schemas.auth import UserSignupRequest
from source.infrastructure.database.models import User


@pytest.mark.asyncio(loop_scope="session")
class TestChangeUserRole:
    async def test_change_role_success(
        self, client: AsyncClient, auth_headers, override_db_session_dependency
    ):
        admin_headers = await auth_headers(role="admin")

        unique_id = str(ID().value)[:8]
        signup_payload = UserSignupRequest(
            name="test",
            surname="test",
            username=f"role_target_{unique_id}",
            password="Test1234",
            email=f"role_target_{unique_id}@email.com",
        )
        signup_response = await client.post(
            "/api/v1/auth/signup", json=signup_payload.model_dump()
        )
        target_user_id = signup_response.json()["id"]

        payload = {"role": UserRole.MODERATOR}

        response = await client.post(
            f"/api/v1/users/change_role/{target_user_id}",
            json=payload,
            headers=admin_headers,
        )

        assert response.status_code == status.HTTP_200_OK

        db_session = override_db_session_dependency

        query = select(User).where(User.id == target_user_id)
        result = await db_session.execute(query)
        user_in_db = result.scalar_one_or_none()
        assert user_in_db is not None
        assert user_in_db.role == UserRole.MODERATOR
