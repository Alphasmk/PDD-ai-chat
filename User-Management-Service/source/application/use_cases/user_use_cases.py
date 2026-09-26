from dataclasses import replace
from uuid import UUID
from source.application.use_cases.base import UseCaseBase
from source.application.interfaces import (
    ITokenProvider,
    ITokenBlacklist,
    IUserRepository,
    IMessagePublisher,
    IStorage,
)
from source.application.dto import (
    UserCreateDTO,
    UserReadDTO,
    UpdateUserDTO,
    TokenDTO,
    DataFromTokenDTO,
)
from source.domain.interfaces import IPasswordHasher
from source.domain.entities.user import UserEntity as User
from source.domain.value_objects import ID, Name, Email, RawPassword
from source.application.exceptions import (
    InvalidCredentialsError,
    UserNotFoundError,
    InvalidTokenError,
    MissingTokenError,
    TokenRevokedError,
    UploadImageError,
    UserHasNoImageError,
    ImageReceivingError,
)


def token_subject(payload: dict[str, str | int]) -> UUID:
    subject = payload.get("sub")
    if not isinstance(subject, str):
        raise InvalidTokenError()
    try:
        return UUID(subject)
    except ValueError as error:
        raise InvalidTokenError() from error


async def require_user(repo: IUserRepository, subject: DataFromTokenDTO) -> User:
    user = await repo.get_by_id(ID(subject.user_id))
    if user is None:
        raise UserNotFoundError()
    return user


async def issue_tokens(provider: ITokenProvider, user: User) -> TokenDTO:
    return TokenDTO(
        access=await provider.create_access_token(
            {"sub": str(user.id.value), "email": user.email.value}
        ),
        refresh=await provider.create_refresh_token({"sub": str(user.id.value)}),
    )


class RegisterUser(UseCaseBase):
    def __init__(self, repo: IUserRepository, hasher: IPasswordHasher) -> None:
        self.repo = repo
        self.hasher = hasher

    async def execute(self, data: UserCreateDTO) -> UserReadDTO:
        name, surname, email = Name(data.name), Name(data.surname), Email(data.email)
        password = await self.hasher.hash(RawPassword(data.password))
        user = User(
            name=name,
            surname=surname,
            username=data.username,
            password_hash=password,
            email=email,
            phone_number=data.phone_number,
        )
        return self._to_user_read_dto(await self.repo.add(user))


class UpdateUser(UseCaseBase):
    def __init__(self, repo: IUserRepository) -> None:
        self.repo = repo

    async def execute(
        self, current_user: DataFromTokenDTO, data: UpdateUserDTO
    ) -> UserReadDTO:
        user = await require_user(self.repo, current_user)
        if all(
            value is None
            for value in (
                data.name,
                data.surname,
                data.username,
                data.email,
                data.phone_number,
            )
        ):
            return self._to_user_read_dto(user)
        updated = replace(
            user,
            name=Name(data.name) if data.name is not None else user.name,
            surname=Name(data.surname) if data.surname is not None else user.surname,
            email=Email(data.email) if data.email is not None else user.email,
            username=data.username if data.username is not None else user.username,
            phone_number=data.phone_number
            if data.phone_number is not None
            else user.phone_number,
        )
        saved = await self.repo.update(updated)
        if saved is None:
            raise UserNotFoundError()
        return self._to_user_read_dto(saved)


class DeleteUser(UseCaseBase):
    def __init__(self, repo: IUserRepository) -> None:
        self.repo = repo

    async def execute(self, current_user: DataFromTokenDTO) -> UserReadDTO:
        user = await require_user(self.repo, current_user)
        await self.repo.delete(user)
        return self._to_user_read_dto(user)


class LoginUser(UseCaseBase):
    def __init__(
        self,
        repo: IUserRepository,
        hasher: IPasswordHasher,
        token_service: ITokenProvider,
    ) -> None:
        self.repo, self.hasher, self.token_service = repo, hasher, token_service

    async def execute(self, username: str, password: str) -> TokenDTO:
        user = await self.repo.get_by_username(username)
        if user is None or not await self.hasher.verify(
            password, user.password_hash.value
        ):
            raise InvalidCredentialsError()
        return await issue_tokens(self.token_service, user)


class GetCurrentUserFromToken:
    def __init__(self, repo: IUserRepository, token_service: ITokenProvider) -> None:
        self.repo, self.token_service = repo, token_service

    async def execute(self, token: str) -> DataFromTokenDTO:
        payload = await self.token_service.decode_token(token)
        subject = token_subject(payload)
        if not isinstance(payload.get("email"), str) or "jti" in payload:
            raise InvalidTokenError()
        user = await self.repo.get_by_id(ID(subject))
        if user is None:
            raise UserNotFoundError()
        return DataFromTokenDTO(user_id=user.id.value, email=user.email.value)


class GetCurrentUserFromDB(UseCaseBase):
    def __init__(self, repo: IUserRepository, token_service: ITokenProvider) -> None:
        self.repo, self.token_service = repo, token_service

    async def execute(self, token: str) -> UserReadDTO:
        subject = await GetCurrentUserFromToken(self.repo, self.token_service).execute(
            token
        )
        return self._to_user_read_dto(await require_user(self.repo, subject))


class ResetTokens:
    def __init__(
        self,
        repo: IUserRepository,
        token_service: ITokenProvider,
        cache_service: ITokenBlacklist,
    ) -> None:
        self.repo, self.token_service, self.cache_service = (
            repo,
            token_service,
            cache_service,
        )

    async def execute(self, refresh_token: str | None) -> TokenDTO:
        if not refresh_token:
            raise MissingTokenError()
        payload = await self.token_service.decode_token(refresh_token)
        subject = token_subject(payload)
        exp = payload.get("exp")
        if (
            not isinstance(exp, int)
            or not isinstance(payload.get("jti"), str)
            or "email" in payload
        ):
            raise InvalidTokenError()
        user = await self.repo.get_by_id(ID(subject))
        if user is None:
            raise UserNotFoundError()
        if await self.cache_service.is_blacklisted(str(subject), refresh_token):
            raise TokenRevokedError()
        tokens = await issue_tokens(self.token_service, user)
        await self.cache_service.add(str(subject), refresh_token, exp)
        return tokens


class ResetUserPassword:
    def __init__(self, broker_service: IMessagePublisher) -> None:
        self.broker_service = broker_service

    async def execute(
        self, user_email: str, body: str, queue_name: str, dlq_name: str
    ) -> None:
        await self.broker_service.publish_message(
            user_email=user_email,
            body=body,
            queue_name=queue_name,
            dead_letter_queue_name=dlq_name,
        )


class SetUserImage:
    def __init__(self, repo: IUserRepository, storage_service: IStorage) -> None:
        self.repo, self.storage_service = repo, storage_service

    async def execute(
        self, image: bytes, image_extension: str, current_user: DataFromTokenDTO
    ) -> str:
        user = await require_user(self.repo, current_user)
        path = await self.storage_service.upload_image(image, image_extension)
        if not path:
            raise UploadImageError()
        saved = await self.repo.update(replace(user, image_s3_path=path))
        if saved is None:
            raise UserNotFoundError()
        if user.image_s3_path:
            await self.storage_service.delete_image(user.image_s3_path)
        return path


class GetUserImage:
    def __init__(self, repo: IUserRepository, storage_service: IStorage) -> None:
        self.repo, self.storage_service = repo, storage_service

    async def execute(self, current_user: DataFromTokenDTO) -> str:
        user = await require_user(self.repo, current_user)
        if not user.image_s3_path:
            raise UserHasNoImageError(user.username)
        url = await self.storage_service.get_image_url(
            user.image_s3_path, expires_in=3600
        )
        if not url:
            raise ImageReceivingError()
        return url


class DeleteUserImage:
    def __init__(self, repo: IUserRepository, storage_service: IStorage) -> None:
        self.repo, self.storage_service = repo, storage_service

    async def execute(self, current_user: DataFromTokenDTO) -> None:
        user = await require_user(self.repo, current_user)
        if not user.image_s3_path:
            raise UserHasNoImageError(user.username)
        saved = await self.repo.update(replace(user, image_s3_path=None))
        if saved is None:
            raise UserNotFoundError()
        await self.storage_service.delete_image(user.image_s3_path)
