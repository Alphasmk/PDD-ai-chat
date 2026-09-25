from abc import abstractmethod, ABC


class IStorage(ABC):
    @abstractmethod
    async def upload_image(self, image: bytes, extension: str) -> str: ...

    @abstractmethod
    async def get_image_url(self, path: str, expires_in: int) -> str | None: ...

    @abstractmethod
    async def delete_image(self, path: str) -> None: ...
