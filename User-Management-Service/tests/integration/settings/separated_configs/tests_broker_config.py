from pydantic import AmqpDsn, SecretStr
from pydantic_core import MultiHostUrl
from pydantic_settings import SettingsConfigDict
from tests.integration.settings.separated_configs.base import ConfigBase


class BrokerConfig(ConfigBase):
    model_config = SettingsConfigDict(**ConfigBase.get_config_with_prefix("BROKER_"))

    host: str
    password: SecretStr
    port: int
    user: str

    @property
    def rabbit_url(self) -> AmqpDsn:
        return AmqpDsn(
            str(
                MultiHostUrl.build(
                    scheme="amqp",
                    username=self.user,
                    password=self.password.get_secret_value(),
                    host=self.host,
                    port=self.port,
                    path="/",
                )
            )
        )
