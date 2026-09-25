from typing import Type
from fastapi import Depends
from source.application.interfaces import (
    IUserRepository,
    ITokenProvider,
    ITokenBlacklist,
    IMessagePublisher,
    IStorage,
)
from source.domain.interfaces import IPasswordHasher
from source.application.use_cases import (
    RegisterUser,
    LoginUser,
    GetUser,
    GetUsersWithPagination,
    UpdateUser,
    DeleteUser,
    ChangeUserBlockState,
    ChangeUserRole,
    ResetTokens,
    ResetUserPassword,
    GetUserImage,
    SetUserImage,
    DeleteUserImage,
)
from source.presentation.api.dependencies.adapters import (
    get_user_repository,
    get_password_hasher,
    get_token_service,
    get_cache_service,
    get_message_broker_service,
    get_storage,
)


class BaseUserUseCaseFactory:
    def __init__(self, use_case_class: Type):
        self.use_case_class = use_case_class

    async def __call__(self, repo: IUserRepository = Depends(get_user_repository)):
        return self.use_case_class(repo=repo)


class RegisterUserFactory:
    async def __call__(
        self,
        repo: IUserRepository = Depends(get_user_repository),
        hasher: IPasswordHasher = Depends(get_password_hasher),
    ) -> RegisterUser:
        return RegisterUser(repo=repo, hasher=hasher)


class LoginUserFactory:
    async def __call__(
        self,
        repo: IUserRepository = Depends(get_user_repository),
        hasher: IPasswordHasher = Depends(get_password_hasher),
        token_service: ITokenProvider = Depends(get_token_service),
    ) -> LoginUser:
        return LoginUser(repo=repo, hasher=hasher, token_service=token_service)


class ResetTokensFactory:
    async def __call__(
        self,
        repo: IUserRepository = Depends(get_user_repository),
        token_service: ITokenProvider = Depends(get_token_service),
        cache_service: ITokenBlacklist = Depends(get_cache_service),
    ) -> ResetTokens:
        return ResetTokens(
            repo=repo, token_service=token_service, cache_service=cache_service
        )


class ResetPasswordFactory:
    async def __call__(
        self,
        service: IMessagePublisher = Depends(get_message_broker_service),
    ) -> ResetUserPassword:
        return ResetUserPassword(broker_service=service)


class SetUserImageFactory:
    async def __call__(
        self,
        repo: IUserRepository = Depends(get_user_repository),
        service: IStorage = Depends(get_storage),
    ) -> SetUserImage:
        return SetUserImage(repo=repo, storage_service=service)


class GetUserImageFactory:
    async def __call__(
        self,
        repo: IUserRepository = Depends(get_user_repository),
        service: IStorage = Depends(get_storage),
    ) -> GetUserImage:
        return GetUserImage(repo=repo, storage_service=service)


class DeleteUserImageFactory:
    async def __call__(
        self,
        repo: IUserRepository = Depends(get_user_repository),
        service: IStorage = Depends(get_storage),
    ) -> DeleteUserImage:
        return DeleteUserImage(repo=repo, storage_service=service)


get_delete_user_usecase = BaseUserUseCaseFactory(DeleteUser)
get_edit_user_use_case = BaseUserUseCaseFactory(UpdateUser)
get_get_user_use_case = BaseUserUseCaseFactory(GetUser)
get_get_users_with_pagination_use_case = BaseUserUseCaseFactory(GetUsersWithPagination)
get_change_block_state_use_case = BaseUserUseCaseFactory(ChangeUserBlockState)
get_change_user_role_use_case = BaseUserUseCaseFactory(ChangeUserRole)

get_register_user_use_case = RegisterUserFactory()
get_login_user_use_case = LoginUserFactory()
get_reset_tokens_use_case = ResetTokensFactory()
get_reset_user_password_use_case = ResetPasswordFactory()

get_set_user_image_use_case = SetUserImageFactory()
get_get_user_image_use_case = GetUserImageFactory()
get_delete_user_image_use_case = DeleteUserImageFactory()
