import pytest
from source.application.use_cases import ResetUserPassword
from tests.adapters.broker_service import FakeMessageService


async def test_publishes_existing_request(
    message_publisher: FakeMessageService,
) -> None:
    await ResetUserPassword(message_publisher).execute(
        "alice@example.com", "link", "queue", "dlq"
    )
    assert message_publisher.messages == [("alice@example.com", "link", "queue", "dlq")]


async def test_publisher_failure_propagates(
    message_publisher: FakeMessageService,
) -> None:
    message_publisher.fail = True
    with pytest.raises(RuntimeError, match="publisher unavailable"):
        await ResetUserPassword(message_publisher).execute(
            "alice@example.com", "link", "queue", "dlq"
        )
