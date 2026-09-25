import mimetypes
import logging
from source.application.interfaces import IStorage
from aioboto3 import Session
from botocore.config import Config
from botocore.exceptions import ClientError, BotoCoreError
from source.domain.value_objects import ID
from source.application.exceptions import UploadImageError, DeleteImageError


class Storage(IStorage):
    def __init__(self, session: Session, bucket_name: str) -> None:
        self.session = session
        self.bucket_name = bucket_name

    async def upload_image(self, image: bytes, extension: str) -> str:
        image_id = ID()

        clean_ext = extension.lstrip(".").lower()

        image_path = f"user_images/{image_id.value}.{clean_ext}"

        content_type = mimetypes.types_map.get(f".{clean_ext}", f"image/{clean_ext}")

        try:
            async with self.session.client("s3") as s3:
                await s3.put_object(
                    Bucket=self.bucket_name,
                    Key=image_path,
                    Body=image,
                    ContentType=content_type,
                )
            return image_path
        except (ClientError, BotoCoreError) as e:
            logging.error(f"Error when uploading an image {image_path}: {str(e)}")
            raise UploadImageError() from e

    async def get_image_url(self, path: str, expires_in: int = 3600) -> str | None:
        async with self.session.client(
            "s3",
            config=Config(signature_version="s3v4", s3={"addressing_style": "virtual"}),
        ) as s3:
            url = await s3.generate_presigned_url(
                ClientMethod="get_object",
                Params={"Bucket": self.bucket_name, "Key": path},
                ExpiresIn=expires_in,
            )
            return url

    async def delete_image(self, path: str) -> None:
        try:
            async with self.session.client("s3") as s3:
                await s3.delete_object(Bucket=self.bucket_name, Key=path)
        except (ClientError, BotoCoreError) as e:
            logging.error(f"Error when deleting an image {path}: {str(e)}")
            raise DeleteImageError() from e
