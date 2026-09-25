from abc import abstractmethod, ABC
from aio_pika.pool import Pool
from aio_pika.abc import AbstractRobustChannel, AbstractRobustConnection


class IBrokerHandler(ABC):
    @abstractmethod
    async def get_connection(self) -> AbstractRobustConnection: ...

    @abstractmethod
    async def get_channel(self) -> AbstractRobustChannel: ...

    @abstractmethod
    async def connect(self) -> None: ...

    @abstractmethod
    def get_channel_pool(self) -> Pool: ...

    @abstractmethod
    async def get_exchange_name(self) -> str: ...

    @abstractmethod
    async def close(self) -> None: ...
