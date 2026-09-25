from source.settings.separated_configs.base import ConfigBase
from pydantic import EmailStr, SecretStr
from pydantic_settings import SettingsConfigDict


class SuperUserConfig(ConfigBase):
    model_config = SettingsConfigDict(env_prefix="SUPER_ADMIN_")

    username: str
    password: SecretStr
    email: EmailStr
