from abc import abstractmethod, ABC


class ITokenBlacklist(ABC):
    @abstractmethod
    async def add(self, user_id: str, refresh_token: str, exp: int) -> None: ...

    @abstractmethod
    async def is_blacklisted(self, user_id: str, refresh_token: str) -> bool: ...
