from pydantic import PostgresDsn, SecretStr
from pydantic_core import MultiHostUrl
from pydantic_settings import SettingsConfigDict
from tests.integration.settings.separated_configs.base import ConfigBase


class DatabaseConfig(ConfigBase):
    model_config = SettingsConfigDict(**ConfigBase.get_config_with_prefix("POSTGRES_"))

    host: str
    port: int
    user: str
    password: SecretStr
    name: str

    @property
    def postgres_url(self) -> PostgresDsn:
        return PostgresDsn(
            str(
                MultiHostUrl.build(
                    scheme="postgresql+asyncpg",
                    username=self.user,
                    password=self.password.get_secret_value(),
                    host=self.host,
                    port=self.port,
                    path=self.name,
                )
            )
        )
