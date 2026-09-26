from uuid import uuid4
from source.application.interfaces import IStorage
from source.application.exceptions import (
    UploadImageError,
    ImageReceivingError,
    DeleteImageError,
)


class FakeStorage(IStorage):
    def __init__(self) -> None:
        self.objects: dict[str, bytes] = {}
        self.signed: list[str] = []
        self.deleted: list[str] = []
        self.fail_upload = False
        self.fail_sign = False
        self.fail_delete = False

    async def upload_image(self, image: bytes, extension: str) -> str:
        if self.fail_upload:
            raise UploadImageError()
        path = f"user_images/{uuid4()}{extension}"
        self.objects[path] = image
        return path

    async def delete_image(self, path: str) -> None:
        if self.fail_delete:
            raise DeleteImageError()
        self.deleted.append(path)
        self.objects.pop(path, None)

    async def get_image_url(self, path: str, expires_in: int = 3600) -> str:
        if self.fail_sign:
            raise ImageReceivingError()
        self.signed.append(path)
        return f"https://storage.example/{path}?expires={expires_in}"
