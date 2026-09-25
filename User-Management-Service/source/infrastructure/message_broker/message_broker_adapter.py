import json

from uuid import uuid4
from datetime import datetime, timezone
from aio_pika import Message, DeliveryMode

from source.application.interfaces import IMessagePublisher, IBrokerHandler


class MessagePublisher(IMessagePublisher):
    def __init__(self, handler: IBrokerHandler):
        self.handler = handler

    async def publish_message(
        self, user_email: str, body: str, queue_name: str, dead_letter_queue_name: str
    ) -> None:
        message_body = {
            "subject": user_email,
            "body": f"Link for reset {user_email} password: {body}",
            "publishing_datetime": datetime.now(timezone.utc).isoformat(),
        }

        message = Message(
            body=json.dumps(message_body).encode("utf-8"),
            delivery_mode=DeliveryMode.PERSISTENT,
            message_id=str(uuid4()),
        )

        async with self.handler.get_channel_pool().acquire() as channel:
            exchange_name = await self.handler.get_exchange_name()
            exchange = await channel.get_exchange(exchange_name)

            dlq_queue = await channel.declare_queue(
                dead_letter_queue_name, durable=True
            )
            await dlq_queue.bind(exchange, routing_key=dead_letter_queue_name)

            queue = await channel.declare_queue(
                queue_name,
                durable=True,
                arguments={
                    "x-queue-type": "quorum",
                    "x-delivery-limit": 5,
                    "x-dead-letter-exchange": exchange_name,
                    "x-dead-letter-routing-key": dead_letter_queue_name,
                },
            )

            await queue.bind(exchange, routing_key=queue_name)
            await exchange.publish(message, routing_key=queue_name)
