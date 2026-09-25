from abc import abstractmethod, ABC


class ITokenProvider(ABC):
    @abstractmethod
    async def create_access_token(self, payload: dict) -> str: ...

    @abstractmethod
    async def create_refresh_token(self, payload: dict) -> str: ...

    @abstractmethod
    async def decode_token(self, token: str) -> dict: ...
