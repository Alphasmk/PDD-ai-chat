import pytest
from httpx import AsyncClient
from fastapi import status
from sqlalchemy import select
from source.infrastructure.database.models import Group


@pytest.mark.asyncio(loop_scope="session")
class TestCreateGroup:
    async def test_success(
        self, client: AsyncClient, override_db_session_dependency, auth_headers
    ):
        group_name = "NewGroup"

        user_headers = await auth_headers(role="admin")

        response = await client.post(
            "/api/v1/groups", params={"group_name": group_name}, headers=user_headers
        )

        assert response.status_code == status.HTTP_200_OK
        response_data = response.json()
        assert "id" in response_data
        assert response_data["name"] == group_name

        db_session = override_db_session_dependency
        query = select(Group).where(Group.id == response_data["id"])
        result = await db_session.execute(query)
        group_in_db = result.scalar_one_or_none()

        assert group_in_db is not None
        assert group_in_db.name == group_name
