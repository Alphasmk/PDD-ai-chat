import pytest
from httpx import AsyncClient
from fastapi import status
from sqlalchemy import select
from source.infrastructure.database.models import User
from source.presentation.api.schemas.auth import UserSignupRequest


@pytest.mark.asyncio(loop_scope="session")
class TestResetTokens:
    async def test_success(
        self,
        client: AsyncClient,
        override_redis_session_dependency,
        override_db_session_dependency,
    ):
        signup_payload = UserSignupRequest(
            name="testuser",
            surname="testuser",
            username="testuser",
            password="Test1234",
            email="test_email@email.com",
        )
        await client.post("/api/v1/auth/signup", json=signup_payload.model_dump())

        login_payload = {
            "username": signup_payload.username,
            "password": signup_payload.password,
        }

        login_response = await client.post("/api/v1/auth/login", data=login_payload)

        assert login_response.status_code == 200

        login_data = login_response.json()
        access_token = login_data["access_token"]
        refresh_token = login_data["refresh_token"]

        assert "refresh_token" in login_response.cookies

        headers = {"Authorization": f"Bearer {access_token}"}

        reset_response = await client.post(
            "/api/v1/auth/refresh-token", headers=headers
        )

        assert reset_response.status_code == status.HTTP_200_OK

        query = select(User).where(User.email == signup_payload.email)
        db_session = override_db_session_dependency
        result = await db_session.execute(query)
        user_in_db = result.scalar_one_or_none()

        cache_session = override_redis_session_dependency

        cache_key = f"blacklist:tokens:{user_in_db.id}:{refresh_token}"
        token_exists = await cache_session.exists(cache_key)
        assert token_exists == 1
