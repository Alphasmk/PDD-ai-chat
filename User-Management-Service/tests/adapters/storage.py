from source.application.interfaces import IStorage


class FakeStorage(IStorage):
    async def upload_image(self, image: bytes, extension: str) -> str:
        return f"avatars/uuid.{extension}"

    async def delete_image(self, path: str) -> None:
        pass

    async def get_image_url(self, path: str, expires_in: int = 3600) -> str:
        return f"https://s3.com/{path}"
