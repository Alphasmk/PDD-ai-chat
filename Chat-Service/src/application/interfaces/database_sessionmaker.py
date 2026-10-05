from abc import abstractmethod, ABC
from sqlalchemy.ext.asyncio import AsyncEngine


class IDatabaseSessionmaker(ABC):
    @abstractmethod
    async def init_db(self, db_url: str) -> None: ...

    @abstractmethod
    async def get_session(self): ...

    @abstractmethod
    async def close(self) -> None: ...

    @abstractmethod
    async def get_engine(self) -> AsyncEngine | None: ...