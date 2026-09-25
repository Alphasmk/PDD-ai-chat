from aio_pika import connect_robust, ExchangeType
from aio_pika.abc import AbstractRobustChannel, AbstractRobustConnection
from aio_pika.pool import Pool
from source.settings.config import get_settings
from source.application.interfaces.message_broker_handler import IBrokerHandler
from source.settings.constansts import EXCHANGE_NAME


class BrokerHandler(IBrokerHandler):
    def __init__(self, broker_url: str | None = None):
        self._broker_url = broker_url
        self._connection_pool = Pool(self.get_connection, max_size=2)
        self._channel_pool = Pool(self.get_channel, max_size=10)
        self.exchange_name = EXCHANGE_NAME

    async def get_connection(self) -> AbstractRobustConnection:
        settings = get_settings()
        broker_url = self._broker_url or str(settings.broker.rabbit_url)
        return await connect_robust(broker_url)

    async def get_channel(self) -> AbstractRobustChannel:
        async with self._connection_pool.acquire() as connection:
            return await connection.channel()

    async def connect(self) -> None:
        async with self._channel_pool.acquire() as channel:
            await channel.declare_exchange(
                self.exchange_name, type=ExchangeType.DIRECT, durable=True
            )

    def get_channel_pool(self) -> Pool:
        return self._channel_pool

    async def get_exchange_name(self) -> str:
        return self.exchange_name

    async def close(self) -> None:
        await self._channel_pool.close()
        await self._connection_pool.close()
