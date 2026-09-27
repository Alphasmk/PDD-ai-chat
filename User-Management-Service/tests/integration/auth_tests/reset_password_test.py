from httpx import AsyncClient
from tests.adapters.broker_service import FakeMessageService
from tests.integration.conftest import response_data
from source.settings.constansts import QUEUE_NAME, DEAD_LETTER_QUEUE_NAME


async def test_reset_publishes(
    client: AsyncClient, publisher: FakeMessageService
) -> None:
    response = await client.post(
        "/api/v1/auth/reset-password", json={"email": "alice@example.com"}
    )
    assert response.status_code == 200 and set(response_data(response)) == {"message"}
    assert publisher.messages == [
        (
            "alice@example.com",
            "link for reset password",
            QUEUE_NAME,
            DEAD_LETTER_QUEUE_NAME,
        )
    ]


async def test_invalid_reset(
    client: AsyncClient, publisher: FakeMessageService
) -> None:
    assert (
        await client.post("/api/v1/auth/reset-password", json={"email": "bad"})
    ).status_code == 422
    assert not publisher.messages
