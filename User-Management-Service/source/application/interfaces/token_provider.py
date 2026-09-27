from abc import ABC, abstractmethod
from source.application.dto.token_dto import AccessPayload, RefreshPayload


class ITokenProvider(ABC):
    @abstractmethod
    async def create_access_token(self, payload: AccessPayload) -> str: ...
    @abstractmethod
    async def create_refresh_token(self, payload: RefreshPayload) -> str: ...
    @abstractmethod
    async def decode_token(self, token: str) -> dict[str, str | int]: ...
