from fastapi import APIRouter

from fastapi import Depends, status, Response, Request
from fastapi.security import OAuth2PasswordRequestForm

from typing import Annotated

from source.application.dto.users_dto import UserCreateDTO, UserReadDTO


from source.presentation.api.schemas.auth import (
    UserSignupRequest,
    UserResponse,
    TokenResponse,
    ResetPasswordResponse,
    ResetPasswordRequest,
)
from source.application.use_cases.user_use_cases import (
    RegisterUser,
    LoginUser,
    ResetTokens,
    ResetUserPassword,
)
from source.presentation.api.dependencies import (
    get_register_user_use_case,
    get_login_user_use_case,
    get_reset_tokens_use_case,
    get_reset_user_password_use_case,
    get_current_user_token,
)

from source.settings.constansts import QUEUE_NAME, DEAD_LETTER_QUEUE_NAME

from source.presentation.api.schemas.base import ErrorResponse

auth_router = APIRouter(
    prefix="/api/v1/auth",
    tags=["Auth"],
    responses={code: {"model": ErrorResponse} for code in (400, 401, 404, 409)},
)


@auth_router.post(
    "/signup",
    response_model=UserResponse,
    status_code=status.HTTP_201_CREATED,
)
async def register_user(
    request: UserSignupRequest,
    use_case: RegisterUser = Depends(get_register_user_use_case),
) -> UserReadDTO:
    """Register a new user"""

    dto = UserCreateDTO(**request.model_dump())

    new_user_dto = await use_case.execute(dto)

    return new_user_dto


@auth_router.post("/login", response_model=TokenResponse)
async def login_for_access_token(
    response: Response,
    form_data: Annotated[OAuth2PasswordRequestForm, Depends()],
    use_case: LoginUser = Depends(get_login_user_use_case),
) -> TokenResponse:
    tokens = await use_case.execute(
        username=form_data.username, password=form_data.password
    )

    response.set_cookie(key="refresh_token", value=tokens.refresh, httponly=True)

    return TokenResponse(
        access_token=tokens.access, refresh_token=tokens.refresh, token_type="bearer"
    )


@auth_router.post("/refresh-token", response_model=TokenResponse)
async def reset_tokens(
    request: Request,
    response: Response,
    token: str = Depends(get_current_user_token),
    use_case: ResetTokens = Depends(get_reset_tokens_use_case),
) -> TokenResponse:
    refresh_token = request.cookies.get("refresh_token")
    tokens = await use_case.execute(refresh_token)
    response.set_cookie(key="refresh_token", value=tokens.refresh, httponly=True)
    return TokenResponse(
        access_token=tokens.access, refresh_token=tokens.refresh, token_type="bearer"
    )


@auth_router.post("/reset-password", response_model=ResetPasswordResponse)
async def reset_password(
    reset_request: ResetPasswordRequest,
    reset_use_case: ResetUserPassword = Depends(get_reset_user_password_use_case),
) -> ResetPasswordResponse:
    reset_link = "link for reset password"
    await reset_use_case.execute(
        reset_request.email, reset_link, QUEUE_NAME, DEAD_LETTER_QUEUE_NAME
    )

    return ResetPasswordResponse(
        message="Password reset link has been sent to your email"
    )
