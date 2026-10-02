from src.settings.separated_configs.base import ConfigBase
from pydantic import SecretStr

class AuthConfig(ConfigBase):
    secret_key: SecretStr
    algorithm: str