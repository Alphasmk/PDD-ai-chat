from fastapi import APIRouter
from fastapi import Depends, UploadFile, HTTPException, status
from source.presentation.api.schemas.user import (
    UserDeleteResponse,
    UserEditResponse,
    UserEditRequest,
    ImageResponse,
    ImageUploadResponse,
)
from source.presentation.api.schemas.auth import UserResponse
from source.presentation.api.dependencies import (
    get_current_user_from_db,
    get_current_user_from_token,
    get_edit_user_use_case,
    get_delete_user_usecase,
    get_set_user_image_use_case,
    get_get_user_image_use_case,
    get_delete_user_image_use_case,
)
from source.application.use_cases import (
    DeleteUser,
    UpdateUser,
    SetUserImage,
    GetUserImage,
    DeleteUserImage,
)
from source.application.dto import UpdateUserDTO, DataFromTokenDTO, UserReadDTO
from source.settings.constansts import MAX_FILE_SIZE, ALLOWED_MIME_TYPES

from source.presentation.api.schemas.base import ErrorResponse

user_router = APIRouter(
    prefix="/api/v1/users",
    tags=["Users"],
    responses={code: {"model": ErrorResponse} for code in (400, 401, 404, 409)},
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


@user_router.post(
    "/me/image",
    response_model=ImageUploadResponse,
    responses={413: {"description": "Image exceeds 5 MiB"}},
)
async def set_user_me_image(
    image: UploadFile,
    current_user: DataFromTokenDTO = Depends(get_current_user_from_token),
    use_case: SetUserImage = Depends(get_set_user_image_use_case),
) -> ImageUploadResponse:
    if image.content_type not in ALLOWED_MIME_TYPES:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"MIME type {image.content_type} is not allowed.",
        )
    if image.size is not None and image.size > MAX_FILE_SIZE:
        raise HTTPException(
            status_code=status.HTTP_413_CONTENT_TOO_LARGE, detail="Max file size: 5 MB"
        )
    image_bytes = await image.read(MAX_FILE_SIZE + 1)
    if len(image_bytes) > MAX_FILE_SIZE:
        raise HTTPException(
            status_code=status.HTTP_413_CONTENT_TOO_LARGE, detail="Max file size: 5 MB"
        )
    extension = {"image/jpeg": ".jpg", "image/png": ".png", "image/webp": ".webp"}[
        image.content_type
    ]
    path = await use_case.execute(image_bytes, extension, current_user)
    return ImageUploadResponse(image_s3_path=path)


@user_router.get("/me/image", response_model=ImageResponse)
async def get_user_me_image(
    current_user: DataFromTokenDTO = Depends(get_current_user_from_token),
    use_case: GetUserImage = Depends(get_get_user_image_use_case),
) -> ImageResponse:
    return ImageResponse(image_url=await use_case.execute(current_user))


@user_router.delete("/me/image")
async def delete_user_me_image(
    current_user: DataFromTokenDTO = Depends(get_current_user_from_token),
    use_case: DeleteUserImage = Depends(get_delete_user_image_use_case),
) -> None:
    await use_case.execute(current_user)
