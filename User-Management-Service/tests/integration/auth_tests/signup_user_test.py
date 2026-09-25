import pytest
from httpx import AsyncClient
from fastapi import status
from sqlalchemy import select
from source.infrastructure.database.models import User
from source.presentation.api.schemas.auth import UserSignupRequest


@pytest.mark.asyncio(loop_scope="session")
class TestSignupUser:
    async def test_success(self, client: AsyncClient, override_db_session_dependency):
        signup_payload = UserSignupRequest(
            name="testuser",
            surname="testuser",
            username="testuser",
            password="Test1234",
            email="test_email@email.com",
        )

        response = await client.post(
            "/api/v1/auth/signup", json=signup_payload.model_dump()
        )

        assert response.status_code == status.HTTP_201_CREATED

        response_data = response.json()
        assert response_data["email"] == signup_payload.email
        assert response_data["username"] == signup_payload.username
        assert "id" in response_data

        db_session = override_db_session_dependency

        query = select(User).where(User.email == signup_payload.email)
        result = await db_session.execute(query)
        user_in_db = result.scalar_one_or_none()

        assert user_in_db is not None
        assert user_in_db.username == signup_payload.username

        assert user_in_db.password_hash != signup_payload.password
