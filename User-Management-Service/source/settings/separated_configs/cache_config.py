from pydantic import RedisDsn, SecretStr
from pydantic_core import MultiHostUrl
from pydantic_settings import SettingsConfigDict
from source.settings.separated_configs.base import ConfigBase


class CacheConfig(ConfigBase):
    model_config = SettingsConfigDict(env_prefix="REDIS_")

    password: SecretStr
    port: int

    @property
    def redis_url(self) -> RedisDsn:
        return RedisDsn(
            str(
                MultiHostUrl.build(
                    scheme="redis",
                    host="redis",
                    port=self.port,
                    password=self.password.get_secret_value(),
                    path="/0",
                )
            )
        )
