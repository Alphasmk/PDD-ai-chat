import json
import pytest
from httpx import AsyncClient
from source.main import app
from tests.integration.conftest import account, response_data


@pytest.mark.parametrize(
    "method,path",
    [
        ("POST", "/groups"),
        ("GET", "/groups"),
        ("GET", "/groups/{group}"),
        ("PATCH", "/groups/{group}"),
        ("DELETE", "/groups/{group}"),
        ("POST", "/groups/{group}/users/{user}"),
        ("DELETE", "/groups/{group}/users/{user}"),
        ("GET", "/groups/{group}/users"),
        ("POST", "/groups/create"),
        ("PATCH", "/groups/edit/{group}"),
        ("DELETE", "/groups/delete/{group}"),
        ("POST", "/groups/add_user/{group}/{user}"),
        ("DELETE", "/groups/delete_user/{group}/{user}"),
        ("GET", "/groups/get_users/{group}"),
    ],
)
async def test_removed_groups_no_side_effects(
    client: AsyncClient, method: str, path: str
) -> None:
    alice = await account(client)
    before = response_data(await client.get("/api/v1/users/me", headers=alice.headers))
    target = "/api/v1" + path.format(group=alice.id, user=alice.id)
    response = await client.request(
        method, target, headers=alice.headers, json={"name": "legacy"}
    )
    assert response.status_code == 404
    assert (
        response_data(await client.get("/api/v1/users/me", headers=alice.headers))
        == before
    )


def test_no_group_api_or_schema() -> None:
    document = json.dumps(app.openapi()).lower()
    assert "group" not in document
