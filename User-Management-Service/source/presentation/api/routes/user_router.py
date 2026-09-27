from fastapi import APIRouter
from fastapi import Depends
from source.presentation.api.schemas.user import (
    UserDeleteResponse,
    UserEditResponse,
    UserEditRequest,
)
from source.presentation.api.schemas.auth import UserResponse
from source.presentation.api.dependencies import (
    get_current_user_from_db,
    get_current_user_from_token,
    get_edit_user_use_case,
    get_delete_user_usecase,
)
from source.application.use_cases import (
    DeleteUser,
    UpdateUser,
)
from source.application.dto import UpdateUserDTO, DataFromTokenDTO, UserReadDTO

from source.presentation.api.schemas.base import ErrorResponse

user_router = APIRouter(
    prefix="/api/v1/users",
    tags=["Users"],
    responses={
        code: {"model": ErrorResponse} for code in (400, 401, 403, 404, 409, 503)
    },
)


@user_router.get("/me", response_model=UserResponse)
async def get_current(
    current_user: UserReadDTO = Depends(get_current_user_from_db),
) -> UserReadDTO:
    return current_user


@user_router.patch("/me", response_model=UserEditResponse)
async def edit_current_user(
    data: UserEditRequest,
    current_user: DataFromTokenDTO = Depends(get_current_user_from_token),
    use_case: UpdateUser = Depends(get_edit_user_use_case),
) -> UserReadDTO:
    dto = UpdateUserDTO(
        name=data.name,
        surname=data.surname,
        username=data.username,
        email=data.email,
        phone_number=data.phone_number,
    )
    return await use_case.execute(current_user, dto)


@user_router.delete("/me", response_model=UserDeleteResponse)
async def delete_current_user(
    current_user: DataFromTokenDTO = Depends(get_current_user_from_token),
    use_case: DeleteUser = Depends(get_delete_user_usecase),
) -> UserReadDTO:
    return await use_case.execute(current_user)
