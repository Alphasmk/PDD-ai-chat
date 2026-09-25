"""Message broker publisher class interface"""

from abc import abstractmethod, ABC


class IMessagePublisher(ABC):
    """Interface for message broker publisher"""

    @abstractmethod
    async def publish_message(
        self, user_email: str, body: str, queue_name: str, dead_letter_queue_name: str
    ) -> None:
        """Publish a message to the specified queue"""
