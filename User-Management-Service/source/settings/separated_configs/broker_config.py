from pydantic import SecretStr, AmqpDsn
from pydantic_core import MultiHostUrl
from pydantic_settings import SettingsConfigDict
from source.settings.separated_configs.base import ConfigBase


class BrokerConfig(ConfigBase):
    model_config = SettingsConfigDict(env_prefix="BROKER_")

    host: str
    port: int
    user: str
    password: SecretStr

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
