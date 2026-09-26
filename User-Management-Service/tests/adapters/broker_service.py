from source.application.interfaces import IMessagePublisher


class FakeMessageService(IMessagePublisher):
    def __init__(self) -> None:
        self.messages: list[tuple[str, str, str, str]] = []
        self.fail = False

    async def publish_message(
        self, user_email: str, body: str, queue_name: str, dead_letter_queue_name: str
    ) -> None:
        if self.fail:
            raise RuntimeError("publisher unavailable")
        self.messages.append((user_email, body, queue_name, dead_letter_queue_name))
