from pydantic import SecretStr, ValidationError
from source.settings.separated_configs.base import ConfigBase
from source.application.use_cases.bootstrap_use_case import (
    BootstrapData,
    InitializationError,
)


class BootstrapConfig(ConfigBase):
    superadmin_username: str | None = None
    superadmin_email: str | None = None
    superadmin_password: SecretStr | None = None
    superadmin_name: str | None = None
    superadmin_surname: str | None = None

    def to_data(self) -> BootstrapData:
        username, email, password, name, surname = (
            self.superadmin_username,
            self.superadmin_email,
            self.superadmin_password,
            self.superadmin_name,
            self.superadmin_surname,
        )
        if (
            not username
            or not email
            or password is None
            or not password.get_secret_value()
            or not name
            or not surname
        ):
            raise InitializationError("missing_initial_data")
        return BootstrapData(
            username=username,
            email=email,
            password=password.get_secret_value(),
            name=name,
            surname=surname,
        )


def load_bootstrap_data() -> BootstrapData:
    try:
        return BootstrapConfig().to_data()
    except ValidationError as error:
        raise InitializationError("invalid_initial_data") from error
