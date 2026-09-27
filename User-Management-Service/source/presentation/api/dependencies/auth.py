from fastapi import Depends
from fastapi.security import OAuth2PasswordBearer
from source.application.interfaces import IUserRepository, ITokenProvider
from source.application.use_cases import GetCurrentUserFromToken, GetCurrentUserFromDB
from source.presentation.api.dependencies.adapters import (
    get_user_repository,
    get_token_service,
)
from source.application.dto import DataFromTokenDTO, UserReadDTO

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/auth/login")


async def get_current_user_token(token: str = Depends(oauth2_scheme)) -> str:
    return token


async def get_current_user_from_token(
    token: str = Depends(get_current_user_token),
    token_service: ITokenProvider = Depends(get_token_service),
    repo: IUserRepository = Depends(get_user_repository),
) -> DataFromTokenDTO:
    return await GetCurrentUserFromToken(repo, token_service).execute(token)


async def get_current_user_from_db(
    repo: IUserRepository = Depends(get_user_repository),
    token: str = Depends(get_current_user_token),
    token_service: ITokenProvider = Depends(get_token_service),
) -> UserReadDTO:
    return await GetCurrentUserFromDB(repo, token_service).execute(token)
