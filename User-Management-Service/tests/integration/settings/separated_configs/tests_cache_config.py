from pydantic import RedisDsn, SecretStr
from pydantic_core import MultiHostUrl
from pydantic_settings import SettingsConfigDict
from tests.integration.settings.separated_configs.base import ConfigBase


class CacheConfig(ConfigBase):
    model_config = SettingsConfigDict(**ConfigBase.get_config_with_prefix("REDIS_"))

    password: SecretStr
    port: int
    host: str

    @property
    def redis_url(self) -> RedisDsn:
        return RedisDsn(
            str(
                MultiHostUrl.build(
                    scheme="redis",
                    host=self.host,
                    port=self.port,
                    password=self.password.get_secret_value(),
                    path="/0",
                )
            )
        )
