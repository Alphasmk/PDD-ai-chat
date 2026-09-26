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
    UpdateUser,
    DeleteUser,
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


async def get_edit_user_use_case(
    repo: IUserRepository = Depends(get_user_repository),
) -> UpdateUser:
    return UpdateUser(repo)


async def get_delete_user_usecase(
    repo: IUserRepository = Depends(get_user_repository),
) -> DeleteUser:
    return DeleteUser(repo)


async def get_register_user_use_case(
    repo: IUserRepository = Depends(get_user_repository),
    hasher: IPasswordHasher = Depends(get_password_hasher),
) -> RegisterUser:
    return RegisterUser(repo, hasher)


async def get_login_user_use_case(
    repo: IUserRepository = Depends(get_user_repository),
    hasher: IPasswordHasher = Depends(get_password_hasher),
    token_service: ITokenProvider = Depends(get_token_service),
) -> LoginUser:
    return LoginUser(repo, hasher, token_service)


async def get_reset_tokens_use_case(
    repo: IUserRepository = Depends(get_user_repository),
    token_service: ITokenProvider = Depends(get_token_service),
    cache_service: ITokenBlacklist = Depends(get_cache_service),
) -> ResetTokens:
    return ResetTokens(repo, token_service, cache_service)


async def get_reset_user_password_use_case(
    service: IMessagePublisher = Depends(get_message_broker_service),
) -> ResetUserPassword:
    return ResetUserPassword(service)


async def get_set_user_image_use_case(
    repo: IUserRepository = Depends(get_user_repository),
    service: IStorage = Depends(get_storage),
) -> SetUserImage:
    return SetUserImage(repo, service)


async def get_get_user_image_use_case(
    repo: IUserRepository = Depends(get_user_repository),
    service: IStorage = Depends(get_storage),
) -> GetUserImage:
    return GetUserImage(repo, service)


async def get_delete_user_image_use_case(
    repo: IUserRepository = Depends(get_user_repository),
    service: IStorage = Depends(get_storage),
) -> DeleteUserImage:
    return DeleteUserImage(repo, service)
