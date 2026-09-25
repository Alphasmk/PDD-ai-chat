from uuid import UUID

from dataclasses import replace, asdict, fields

from typing import List
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
    UserPaginationDTO,
    UserRoleChangeDTO,
    TokenDTO,
    DataFromTokenDTO,
)
from source.domain.interfaces.password_hasher import IPasswordHasher
from source.domain.entities.user import UserEntity as User
from source.domain.enums.user_role import UserRole
from source.domain.value_objects import ID, Name, Email, RawPassword
from source.domain.exceptions import (
    UserBlockedError,
    UserDeleteNotAllowedError,
    CannotBlockAdminError,
    AdminRegularAssignError,
    RoleIsUnassignableOrChangable,
    AdminCannotChangeAdminsRoleError,
)

from source.application.exceptions import (
    InvalidCredentialsError,
    UserNotFoundError,
    InvalidTokenError,
    MissingTokenError,
    TokenRevokedError,
    ActionNotAllowedError,
    UserEditNotAllowedError,
    UserGetInfoNotAllowed,
    ModeratorGetInfoNotAllowed,
    InvalidSortFieldError,
    CannotChangeImageError,
    UploadImageError,
    UserHasNoImageError,
    ImageReceivingError,
    CannotDeleteImageError,
)


class RegisterUser(UseCaseBase):
    def __init__(self, repo: IUserRepository, hasher: IPasswordHasher) -> None:
        self.repo = repo
        self.hasher = hasher

    async def execute(self, data: UserCreateDTO) -> UserReadDTO | None:
        hashed_password = await self.hasher.hash(RawPassword(data.password))

        user = User(
            name=Name(data.name),
            surname=Name(data.surname),
            username=data.username,
            password_hash=hashed_password,
            email=Email(data.email),
            image_s3_path=data.image_s3_path,
            phone_number=data.phone_number,
        )

        saved_user = await self.repo.add(user)

        if not saved_user:
            return None

        return self._to_user_read_dto(saved_user)


class UpdateUser(UseCaseBase):
    def __init__(self, repo: IUserRepository) -> None:
        self.repo = repo

    async def execute(
        self, user_id: UUID, current_user: DataFromTokenDTO, data: UpdateUserDTO
    ) -> UserReadDTO | None:
        existing_user = await self.repo.get_by_id(ID(user_id))
        if not existing_user:
            raise UserNotFoundError()

        is_admin = current_user.role in (UserRole.ADMIN, UserRole.SUPER_ADMIN)
        is_self_edit = str(user_id) == str(current_user.user_id)

        if not (is_admin or is_self_edit):
            raise ActionNotAllowedError(
                "You can only edit your own account or be an admin"
            )

        if existing_user.role == UserRole.SUPER_ADMIN and not is_self_edit:
            raise UserEditNotAllowedError()

        if not existing_user:
            return None

        update_data = {
            key: value for key, value in asdict(data).items() if value is not None
        }

        if not update_data:
            return self._to_user_read_dto(existing_user)

        if "name" in update_data:
            update_data["name"] = Name(update_data["name"])
        if "surname" in update_data:
            update_data["surname"] = Name(update_data["surname"])
        if "email" in update_data:
            update_data["email"] = Email(update_data["email"])

        updated_user_entity = replace(existing_user, **update_data)

        saved_user = await self.repo.update(updated_user_entity)

        if not saved_user:
            return None

        return self._to_user_read_dto(saved_user)


class DeleteUser(UseCaseBase):
    def __init__(self, repo: IUserRepository) -> None:
        self.repo = repo

    async def execute(
        self, user_id: UUID, current_user: DataFromTokenDTO
    ) -> UserReadDTO:
        user_to_delete = await self.repo.get_by_id(ID(user_id))
        if not user_to_delete:
            raise UserNotFoundError()
        if user_to_delete.role == UserRole.SUPER_ADMIN:
            raise UserDeleteNotAllowedError()

        is_admin = current_user.role in (UserRole.ADMIN, UserRole.SUPER_ADMIN)
        is_self_delete = str(user_id) == str(current_user.user_id)

        if not (is_admin or is_self_delete):
            raise ActionNotAllowedError(
                "You can only delete your own account or be an admin"
            )

        await self.repo.delete(user_to_delete)

        return self._to_user_read_dto(user_to_delete)


class LoginUser(UseCaseBase):
    def __init__(
        self,
        repo: IUserRepository,
        hasher: IPasswordHasher,
        token_service: ITokenProvider,
    ) -> None:
        self.repo = repo
        self.hasher = hasher
        self.token_service = token_service

    async def execute(self, username: str, password: str) -> TokenDTO:
        user = await self.repo.get_by_username(username)
        if not user or not await self.hasher.verify(password, user.password_hash.value):
            raise InvalidCredentialsError()
        if user.is_blocked:
            raise UserBlockedError(user.username)
        access_payload = {
            "sub": str(user.id.value),
            "email": user.email.value,
            "role": user.role.value,
            "group_id": str(user.group_id) if user.group_id else "",
        }
        access_token = await self.token_service.create_access_token(access_payload)
        refresh_payload = {"sub": str(user.id.value)}
        refresh_token = await self.token_service.create_refresh_token(refresh_payload)
        return TokenDTO(access=access_token, refresh=refresh_token)


class GetCurrentUserFromDB(UseCaseBase):
    def __init__(self, repo: IUserRepository, token_service: ITokenProvider) -> None:
        self.token_service = token_service
        self.repo = repo

    async def execute(self, token: str) -> UserReadDTO:
        decoded_token = await self.token_service.decode_token(token)
        user_id = decoded_token.get("sub")
        if not user_id:
            raise UserNotFoundError()
        user = await self.repo.get_by_id(ID(user_id))
        if not user:
            raise UserNotFoundError()
        return self._to_user_read_dto(user)


class GetCurrentUserFromToken(UseCaseBase):
    def __init__(self, token_service: ITokenProvider) -> None:
        self.token_service = token_service

    async def execute(self, token: str) -> DataFromTokenDTO:
        decoded_token = await self.token_service.decode_token(token)

        user_id = decoded_token.get("sub")
        user_email = decoded_token.get("email")
        user_role = decoded_token.get("role")

        if not user_id or not user_email or not user_role:
            raise UserNotFoundError()

        user_group_id = decoded_token.get("group_id")

        return DataFromTokenDTO(
            user_id=UUID(str(user_id)),
            email=str(user_email),
            role=str(user_role),
            group_id=UUID(str(user_group_id)) if user_group_id else None,
        )


class ResetTokens(UseCaseBase):
    def __init__(
        self,
        repo: IUserRepository,
        token_service: ITokenProvider,
        cache_service: ITokenBlacklist,
    ) -> None:
        self.repo = repo
        self.token_service = token_service
        self.cache_service = cache_service

    async def execute(self, refresh_token: str | None) -> TokenDTO:
        if not refresh_token:
            raise MissingTokenError()

        decoded_token = await self.token_service.decode_token(refresh_token)
        user_id = decoded_token.get("sub")
        exp = decoded_token.get("exp")
        if user_id is None or exp is None:
            raise InvalidTokenError()

        user = await self.repo.get_by_id(ID(user_id))

        if user:
            if await self.cache_service.is_blacklisted(str(user_id), refresh_token):
                raise TokenRevokedError()

            await self.cache_service.add(
                user_id=str(user_id), refresh_token=refresh_token, exp=exp
            )

            access_payload = {
                "sub": str(user.id.value),
                "email": user.email.value,
                "role": user.role.value,
                "group_id": user.group_id,
            }
            access_token = await self.token_service.create_access_token(access_payload)
            refresh_payload = {"sub": str(user.id.value)}
            refresh_token = await self.token_service.create_refresh_token(
                refresh_payload
            )
            return TokenDTO(access=access_token, refresh=refresh_token)
        else:
            raise UserNotFoundError()


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


class GetUser(UseCaseBase):
    def __init__(self, repo: IUserRepository) -> None:
        self.repo = repo

    async def execute(
        self, user_id: UUID, current_user: DataFromTokenDTO
    ) -> UserReadDTO:
        existing_user = await self.repo.get_by_id(ID(user_id))
        if not existing_user:
            raise UserNotFoundError()

        is_admin = current_user.role in (UserRole.ADMIN, UserRole.SUPER_ADMIN)

        is_user_from_group = (
            current_user.role == UserRole.MODERATOR
            and existing_user.group_id
            and current_user.group_id == existing_user.group_id
        )

        if not (is_admin or is_user_from_group):
            if current_user.role == UserRole.MODERATOR:
                raise ModeratorGetInfoNotAllowed()
            raise UserGetInfoNotAllowed()

        return self._to_user_read_dto(existing_user)


class GetUsersWithPagination(UseCaseBase):
    def __init__(self, repo: IUserRepository) -> None:
        self.repo = repo

    async def execute(
        self, params: UserPaginationDTO, current_user: DataFromTokenDTO
    ) -> List[UserReadDTO]:
        if current_user.role == UserRole.USER:
            raise ActionNotAllowedError("You cannot get info about users")

        if params.sort_by:
            valid_fields = {f.name for f in fields(User)}
            if params.sort_by not in valid_fields:
                raise InvalidSortFieldError()
        if current_user.role == UserRole.MODERATOR:
            params = replace(params, group=current_user.group_id)

        users = await self.repo.get_users(params)
        return [self._to_user_read_dto(user) for user in users]


class ChangeUserBlockState(UseCaseBase):
    def __init__(self, repo: IUserRepository):
        self.repo = repo

    async def execute(self, user_id: UUID, current_user: DataFromTokenDTO) -> bool:
        existing_user = await self.repo.get_by_id(ID(user_id))
        if not existing_user:
            raise UserNotFoundError()
        if (
            current_user.role == UserRole.USER
            or current_user.role == UserRole.MODERATOR
        ):
            raise ActionNotAllowedError("You cannot block users")

        if (
            existing_user.role == UserRole.ADMIN
            or existing_user.role == UserRole.SUPER_ADMIN
        ):
            raise CannotBlockAdminError()

        result = await self.repo.change_block_state(ID(user_id))

        if result is None:
            raise UserNotFoundError()

        return result


class ChangeUserRole(UseCaseBase):
    def __init__(self, repo: IUserRepository):
        self.repo = repo

    async def execute(
        self, user_id: UUID, role: UserRoleChangeDTO, current_user: DataFromTokenDTO
    ) -> None:
        if (
            current_user.role == UserRole.USER
            or current_user.role == UserRole.MODERATOR
        ):
            raise ActionNotAllowedError("You cannot change user roles")
        existing_user = await self.repo.get_by_id(ID(user_id))
        if not existing_user:
            raise UserNotFoundError()
        if existing_user.role.is_changable and role.role.is_assignable:
            if current_user.role == UserRole.ADMIN:
                if existing_user.role == UserRole.ADMIN:
                    raise AdminCannotChangeAdminsRoleError()
                if role.role == UserRole.ADMIN:
                    raise AdminRegularAssignError()
            await self.repo.change_role(ID(user_id), role.role)
        else:
            raise RoleIsUnassignableOrChangable()


class CreateSuperUser(UseCaseBase):
    def __init__(self, repo: IUserRepository, hasher: IPasswordHasher):
        self.repo = repo
        self.hasher = hasher

    async def execute(self, username: str, password: str, email: str) -> None:
        existing_user = await self.repo.get_by_username(username)
        if existing_user:
            return

        hashed_password = await self.hasher.hash(RawPassword(password))
        super_admin = User(
            name=Name("admin"),
            surname=Name("admin"),
            username=username,
            password_hash=hashed_password,
            email=Email(email),
            role=UserRole.SUPER_ADMIN,
        )
        await self.repo.add(super_admin)


class SetUserImage(UseCaseBase):
    def __init__(self, repo: IUserRepository, storage_service: IStorage) -> None:
        self.repo = repo
        self.storage_service = storage_service

    async def execute(
        self,
        image: bytes,
        image_extension: str,
        user_id_to_set: UUID,
        current_user: DataFromTokenDTO,
    ) -> str:

        can_change = (current_user.user_id == user_id_to_set) or (
            current_user.role in (UserRole.ADMIN, UserRole.SUPER_ADMIN)
        )
        if not can_change:
            raise CannotChangeImageError()

        existing_user = await self.repo.get_by_id(ID(user_id_to_set))
        if not existing_user:
            raise UserNotFoundError()

        old_image_path = existing_user.image_s3_path
        new_image_path = await self.storage_service.upload_image(image, image_extension)

        if not new_image_path:
            raise UploadImageError()

        user_to_update = replace(existing_user, image_s3_path=new_image_path)
        await self.repo.update(user_to_update)

        if old_image_path:
            await self.storage_service.delete_image(old_image_path)

        return new_image_path


class GetUserImage(UseCaseBase):
    def __init__(self, repo: IUserRepository, storage_service: IStorage) -> None:
        self.repo = repo
        self.storage_service = storage_service

    async def execute(self, user_id: UUID) -> str:
        existing_user = await self.repo.get_by_id((ID(user_id)))
        if not existing_user:
            raise UserNotFoundError()

        if not existing_user.image_s3_path:
            raise UserHasNoImageError(existing_user.username)

        url = await self.storage_service.get_image_url(
            existing_user.image_s3_path, expires_in=3600
        )

        if not url:
            raise ImageReceivingError()

        return url


class DeleteUserImage(UseCaseBase):
    def __init__(self, repo: IUserRepository, storage_service: IStorage) -> None:
        self.repo = repo
        self.storage_service = storage_service

    async def execute(self, user_id: UUID, current_user: DataFromTokenDTO) -> None:
        can_delete = (current_user.user_id == user_id) or (
            current_user.role in (UserRole.ADMIN, UserRole.SUPER_ADMIN)
        )
        if not can_delete:
            raise CannotDeleteImageError()

        existing_user = await self.repo.get_by_id((ID(user_id)))
        if not existing_user:
            raise UserNotFoundError()

        if not existing_user.image_s3_path:
            raise UserHasNoImageError(existing_user.username)

        user_to_update = replace(existing_user, image_s3_path=None)

        await self.repo.update(user_to_update)

        await self.storage_service.delete_image(existing_user.image_s3_path)
