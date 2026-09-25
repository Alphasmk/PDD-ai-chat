from aioboto3 import Session
from source.settings.config import get_settings
from functools import lru_cache


@lru_cache
def get_aws_session() -> Session:
    settings = get_settings()
    session = Session(
        aws_access_key_id=settings.storage.access_key_id.get_secret_value(),
        aws_secret_access_key=settings.storage.access_key.get_secret_value(),
        region_name=settings.storage.region_name,
    )
    return session
