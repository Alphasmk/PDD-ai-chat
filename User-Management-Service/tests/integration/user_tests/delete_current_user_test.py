import pytest
from httpx import AsyncClient
from fastapi import status
from sqlalchemy import select
from source.infrastructure.database.models import User


@pytest.mark.asyncio(loop_scope="session")
class TestDeleteCurrentUser:
    async def test_success(
        self, client: AsyncClient, auth_headers, override_db_session_dependency
    ):
        headers = await auth_headers()

        await client.get("/api/v1/users/me", headers=headers)

        delete_response = await client.delete("/api/v1/users/me", headers=headers)

        assert delete_response.status_code == status.HTTP_200_OK

        deleted_user_id = delete_response.json()["id"]

        db_session = override_db_session_dependency

        query = select(User).where(User.id == deleted_user_id)
        result = await db_session.execute(query)
        user_in_db = result.scalar_one_or_none()

        assert user_in_db is None
