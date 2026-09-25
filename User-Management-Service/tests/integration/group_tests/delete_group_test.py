import pytest
from httpx import AsyncClient
from fastapi import status
from sqlalchemy import select
from source.infrastructure.database.models import Group


@pytest.mark.asyncio(loop_scope="session")
class TestDeleteGroup:
    async def test_success(
        self, client: AsyncClient, override_db_session_dependency, auth_headers
    ):

        group_name = "NewGroup"

        user_headers = await auth_headers(role="admin")

        create_response = await client.post(
            "/api/v1/groups", params={"group_name": group_name}, headers=user_headers
        )
        group_id = create_response.json()["id"]

        response = await client.delete(
            f"/api/v1/groups/{group_id}", headers=user_headers
        )

        assert response.status_code == status.HTTP_200_OK
        response_data = response.json()
        assert response_data["id"] == group_id

        db_session = override_db_session_dependency
        query = select(Group).where(Group.id == group_id)
        result = await db_session.execute(query)
        group_in_db = result.scalar_one_or_none()

        assert group_in_db is None
