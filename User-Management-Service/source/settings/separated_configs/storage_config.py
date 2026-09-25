from pydantic import SecretStr
from pydantic_settings import SettingsConfigDict
from source.settings.separated_configs.base import ConfigBase


class StorageConfig(ConfigBase):
    model_config = SettingsConfigDict(env_prefix="AWS_")

    access_key_id: SecretStr
    access_key: SecretStr
    region_name: str
    bucket_name: str
