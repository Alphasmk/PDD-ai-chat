import os

from fastapi_error_map import ErrorAwareRouter

from uuid import UUID

from typing import List, Annotated, Optional, Literal

from fastapi import Depends, Query, UploadFile, HTTPException, status

from source.presentation.exceptions import AUTH_ERROR_MAP, USER_ACTIONS_MAP

from source.presentation.api.schemas.user import (
    UserDeleteResponse,
    UserEditResponse,
    UserEditRequest,
    UserPaginationRequest,
    MessageResponse,
    ChangeRoleRequest,
    ImageResponse,
    ImageUploadResponse,
)

from source.presentation.api.dependencies import (
    get_current_user_from_db,
    get_current_user_from_token,
    get_edit_user_use_case,
    get_delete_user_usecase,
    get_get_user_use_case,
    get_get_users_with_pagination_use_case,
    get_change_block_state_use_case,
    get_change_user_role_use_case,
    get_set_user_image_use_case,
    get_get_user_image_use_case,
    get_delete_user_image_use_case,
)

from source.application.use_cases import (
    DeleteUser,
    UpdateUser,
    GetUser,
    GetUsersWithPagination,
    ChangeUserBlockState,
    ChangeUserRole,
    SetUserImage,
    GetUserImage,
    DeleteUserImage,
)

from source.presentation.api.schemas.auth import UserResponse

from source.application.dto import (
    UpdateUserDTO,
    UserPaginationDTO,
    UserRoleChangeDTO,
    DataFromTokenDTO,
)

from source.settings.constansts import MAX_FILE_SIZE, ALLOWED_MIME_TYPES

user_router = ErrorAwareRouter(prefix="/api/v1/users", tags=["Users"])


@user_router.get("/me", error_map=AUTH_ERROR_MAP, response_model=UserResponse)
async def get_current(
    current_user: UserResponse = Depends(get_current_user_from_db),
):
    return current_user


@user_router.patch("/me", error_map=USER_ACTIONS_MAP, response_model=UserEditResponse)
async def edit_current_user(
    data: UserEditRequest,
    current_user: DataFromTokenDTO = Depends(get_current_user_from_token),
    use_case: UpdateUser = Depends(get_edit_user_use_case),
):
    update_dto = UpdateUserDTO(**data.model_dump(exclude_unset=True))
    edited_user = await use_case.execute(current_user.user_id, current_user, update_dto)
    return edited_user


@user_router.post(
    "/me/image", error_map=USER_ACTIONS_MAP, response_model=ImageUploadResponse
)
async def set_user_me_image(
    image: UploadFile,
    current_user: DataFromTokenDTO = Depends(get_current_user_from_token),
    use_case: SetUserImage = Depends(get_set_user_image_use_case),
):
    if image.content_type not in ALLOWED_MIME_TYPES:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"MIME type {image.content_type} is not allowed.",
        )
    if image.size > MAX_FILE_SIZE:
        raise HTTPException(
            status_code=status.HTTP_413_CONTENT_TOO_LARGE,
            detail=f"Max file size: {MAX_FILE_SIZE // (1024 * 1024)} MB",
        )
    image_extension = os.path.splitext(image.filename)[1]
    image_bytes = await image.read()
    path = await use_case.execute(
        image_bytes,
        image_extension,
        current_user.user_id,
        current_user,
    )
    return ImageUploadResponse(image_s3_path=path)


@user_router.get("/me/image", error_map=USER_ACTIONS_MAP, response_model=ImageResponse)
async def get_user_me_image(
    current_user: DataFromTokenDTO = Depends(get_current_user_from_token),
    use_case: GetUserImage = Depends(get_get_user_image_use_case),
):
    url = await use_case.execute(user_id=current_user.user_id)
    return ImageResponse(image_url=url)


@user_router.delete("/me/image", error_map=USER_ACTIONS_MAP)
async def delete_user_me_image(
    current_user: DataFromTokenDTO = Depends(get_current_user_from_token),
    use_case: DeleteUserImage = Depends(get_delete_user_image_use_case),
):
    await use_case.execute(current_user.user_id, current_user)


@user_router.delete(
    "/me", error_map=USER_ACTIONS_MAP, response_model=UserDeleteResponse
)
async def delete_current_user(
    current_user: DataFromTokenDTO = Depends(get_current_user_from_token),
    use_case: DeleteUser = Depends(get_delete_user_usecase),
):
    deleted_user = await use_case.execute(current_user.user_id, current_user)
    return deleted_user


@user_router.get("/{user_id}", response_model=UserResponse, error_map=USER_ACTIONS_MAP)
async def get_user_by_id(
    user_id: UUID,
    current_user: DataFromTokenDTO = Depends(get_current_user_from_token),
    use_case: GetUser = Depends(get_get_user_use_case),
):
    user = await use_case.execute(user_id, current_user)
    return user


@user_router.patch(
    "/{user_id}", error_map=USER_ACTIONS_MAP, response_model=UserEditResponse
)
async def edit_user_by_id(
    user_id: UUID,
    data: UserEditRequest,
    current_user: DataFromTokenDTO = Depends(get_current_user_from_token),
    use_case: UpdateUser = Depends(get_edit_user_use_case),
):
    update_dto = UpdateUserDTO(**data.model_dump(exclude_unset=True))
    edited_user = await use_case.execute(user_id, current_user, update_dto)
    return edited_user


@user_router.delete(
    "/{user_id}", error_map=USER_ACTIONS_MAP, response_model=UserDeleteResponse
)
async def delete_user_by_id(
    user_id: UUID,
    current_user: DataFromTokenDTO = Depends(get_current_user_from_token),
    use_case: DeleteUser = Depends(get_delete_user_usecase),
):
    deleted_user = await use_case.execute(user_id, current_user)
    return deleted_user


@user_router.get("", error_map=USER_ACTIONS_MAP, response_model=List[UserResponse])
async def get_users(
    limit: Annotated[int, Query(ge=1, le=100)],
    page: Annotated[int, Query(ge=1)],
    filter_by_name: Optional[str] = Query(None),
    sort_by: Optional[str] = Query(None),
    order_by: Literal["asc", "desc"] = Query("asc"),
    current_user: DataFromTokenDTO = Depends(get_current_user_from_token),
    use_case: GetUsersWithPagination = Depends(get_get_users_with_pagination_use_case),
):
    params = UserPaginationRequest(
        limit=limit,
        page=page,
        filter_by_name=filter_by_name,
        sort_by=sort_by,
        order_by=order_by,
    )
    pagination_dto = UserPaginationDTO(**params.model_dump())
    users = await use_case.execute(pagination_dto, current_user)
    return users


@user_router.post(
    "/change_block_state/{user_id}",
    error_map=USER_ACTIONS_MAP,
    response_model=MessageResponse,
)
async def change_block(
    user_id: UUID,
    current_user: DataFromTokenDTO = Depends(get_current_user_from_token),
    use_case: ChangeUserBlockState = Depends(get_change_block_state_use_case),
):
    result = await use_case.execute(user_id, current_user)
    if result:
        message = "User successfully blocked"
    else:
        message = "User successfully unlocked"

    return MessageResponse(message=message)


@user_router.post(
    "/change_role/{user_id}", error_map=USER_ACTIONS_MAP, response_model=MessageResponse
)
async def change_role(
    user_id: UUID,
    role: ChangeRoleRequest,
    current_user: DataFromTokenDTO = Depends(get_current_user_from_token),
    use_case: ChangeUserRole = Depends(get_change_user_role_use_case),
):
    role_dto = UserRoleChangeDTO(**role.model_dump())
    await use_case.execute(user_id, role_dto, current_user)
    return MessageResponse(
        message=f"The user's role was successfully changed to {role.role}"
    )


@user_router.post(
    "/{user_id}/image", error_map=USER_ACTIONS_MAP, response_model=ImageUploadResponse
)
async def set_user_image(
    user_id: UUID,
    image: UploadFile,
    current_user: DataFromTokenDTO = Depends(get_current_user_from_token),
    use_case: SetUserImage = Depends(get_set_user_image_use_case),
):
    if image.content_type not in ALLOWED_MIME_TYPES:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"MIME type {image.content_type} is not allowed.",
        )
    if image.size > MAX_FILE_SIZE:
        raise HTTPException(
            status_code=status.HTTP_413_CONTENT_TOO_LARGE,
            detail=f"Max file size: {MAX_FILE_SIZE // (1024 * 1024)} MB",
        )
    image_extension = os.path.splitext(image.filename)[1]
    image_bytes = await image.read()
    path = await use_case.execute(
        image_bytes,
        image_extension,
        user_id,
        current_user,
    )
    return ImageUploadResponse(image_s3_path=path)


@user_router.get(
    "/{user_id}/image", error_map=USER_ACTIONS_MAP, response_model=ImageResponse
)
async def get_user_image(
    user_id: UUID, use_case: GetUserImage = Depends(get_get_user_image_use_case)
):
    url = await use_case.execute(user_id=user_id)
    return ImageResponse(image_url=url)


@user_router.delete("/{user_id}/image", error_map=USER_ACTIONS_MAP)
async def delete_user_image(
    user_id: UUID,
    current_user: DataFromTokenDTO = Depends(get_current_user_from_token),
    use_case: DeleteUserImage = Depends(get_delete_user_image_use_case),
):
    await use_case.execute(user_id, current_user)
