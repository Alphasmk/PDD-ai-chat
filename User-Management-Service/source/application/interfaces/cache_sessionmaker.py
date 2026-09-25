from abc import ABC, abstractmethod


class ICacheSessionmaker(ABC):
    @abstractmethod
    async def init_db(self, db_url: str) -> None: ...

    @abstractmethod
    async def get_session(self): ...

    @abstractmethod
    async def close(self) -> None: ...
