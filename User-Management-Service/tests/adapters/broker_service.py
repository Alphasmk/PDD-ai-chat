from source.application.interfaces import IMessagePublisher
from datetime import datetime, timezone


class FakeMessageService(IMessagePublisher):
    def __init__(self):
        self.messages = []

    async def publish_message(
        self, user_email, body, queue_name, dead_letter_queue_name
    ):
        message = {
            "subject": user_email,
            "body": f"Link for reset {user_email} password: {body}",
            "publishing_datetime": datetime.now(timezone.utc).isoformat(),
        }
        self.messages.append(message)

    async def get_messages(self):
        return self.messages
