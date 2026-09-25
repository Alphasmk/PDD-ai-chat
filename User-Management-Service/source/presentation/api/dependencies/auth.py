from fastapi import Depends
from fastapi.security import OAuth2PasswordBearer
from source.application.interfaces import IUserRepository, ITokenProvider
from source.application.use_cases import GetCurrentUserFromToken, GetCurrentUserFromDB
from source.presentation.api.dependencies.adapters import (
    get_user_repository,
    get_token_service,
)
from source.application.dto import DataFromTokenDTO
from source.presentation.api.schemas.auth import UserResponse

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/auth/login")


async def get_current_user_token(token: str = Depends(oauth2_scheme)) -> str:
    return token


async def get_current_user_from_token(
    token: str = Depends(get_current_user_token),
    token_service: ITokenProvider = Depends(get_token_service),
) -> DataFromTokenDTO:
    service = GetCurrentUserFromToken(token_service=token_service)
    current_user = await service.execute(token=token)

    return DataFromTokenDTO(
        user_id=current_user.user_id,
        email=current_user.email,
        role=current_user.role,
        group_id=current_user.group_id,
    )


async def get_current_user_from_db(
    repo: IUserRepository = Depends(get_user_repository),
    token: str = Depends(get_current_user_token),
    token_service: ITokenProvider = Depends(get_token_service),
) -> UserResponse:
    service = GetCurrentUserFromDB(repo=repo, token_service=token_service)
    current_user = await service.execute(token=token)

    return UserResponse(
        id=current_user.id,
        name=current_user.name,
        surname=current_user.surname,
        username=current_user.username,
        email=current_user.email,
        phone_number=current_user.phone_number,
        role=current_user.role,
        is_blocked=current_user.is_blocked,
        image_s3_path=current_user.image_s3_path,
        group_id=current_user.group_id,
        created_at=current_user.created_at,
        updated_at=current_user.updated_at,
    )
