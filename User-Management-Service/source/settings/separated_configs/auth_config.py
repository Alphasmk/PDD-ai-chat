from source.settings.separated_configs.base import ConfigBase
from pydantic import SecretStr


class AuthConfig(ConfigBase):
    secret_key: SecretStr
    algorithm: str
    access_token_expire_minutes: int
    refresh_token_expire_days: int

    @property
    def auth_data(self) -> dict:
        return {
            "secret_key": self.secret_key,
            "algorithm": self.algorithm,
        }
