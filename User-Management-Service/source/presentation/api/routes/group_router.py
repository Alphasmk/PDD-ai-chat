from fastapi_error_map import ErrorAwareRouter
from fastapi import Depends
from typing import List
from uuid import UUID
from source.application.dto import GroupEditDTO, DataFromTokenDTO
from source.presentation.api.schemas.auth import UserResponse
from source.presentation.api.schemas.group import (
    GroupResponse,
    GroupEditData,
    GroupMessage,
)
from source.presentation.exceptions import GROUP_ACTIONS_MAP
from source.application.use_cases.group_use_cases import (
    CreateGroup,
    EditGroup,
    DeleteGroup,
    AddUserToGroup,
    RemoveUserFromGroup,
    GetUsersInGroup,
)

from source.presentation.api.dependencies import (
    get_current_user_from_token,
    get_create_group_use_case,
    get_edit_group_use_case,
    get_delete_group_use_case,
    get_add_user_to_group_use_case,
    get_remove_user_from_group_use_case,
    get_get_users_in_group_use_case,
)

group_router = ErrorAwareRouter(prefix="/api/v1/groups", tags=["Groups"])


@group_router.post("", response_model=GroupResponse, error_map=GROUP_ACTIONS_MAP)
async def create_group(
    group_name: str,
    current_user: DataFromTokenDTO = Depends(get_current_user_from_token),
    use_case: CreateGroup = Depends(get_create_group_use_case),
):
    created_group = await use_case.execute(group_name, current_user)
    return created_group


@group_router.patch(
    "/{group_id}", response_model=GroupResponse, error_map=GROUP_ACTIONS_MAP
)
async def edit_group(
    group_id: UUID,
    data: GroupEditData,
    current_user: DataFromTokenDTO = Depends(get_current_user_from_token),
    use_case: EditGroup = Depends(get_edit_group_use_case),
):
    edit_dto = GroupEditDTO(**data.model_dump())
    edited_group = await use_case.execute(group_id, edit_dto, current_user)
    return edited_group


@group_router.delete(
    "/{group_id}", response_model=GroupResponse, error_map=GROUP_ACTIONS_MAP
)
async def delete_group(
    group_id: UUID,
    current_user: DataFromTokenDTO = Depends(get_current_user_from_token),
    use_case: DeleteGroup = Depends(get_delete_group_use_case),
):
    deleted_group = await use_case.execute(group_id, current_user)
    return deleted_group


@group_router.get(
    "/{group_id}/users", error_map=GROUP_ACTIONS_MAP, response_model=List[UserResponse]
)
async def get_users_in_group(
    group_id: UUID,
    current_user: DataFromTokenDTO = Depends(get_current_user_from_token),
    use_case: GetUsersInGroup = Depends(get_get_users_in_group_use_case),
):
    users = await use_case.execute(group_id, current_user)
    return users


@group_router.post(
    "/{group_id}/users/{user_id}",
    error_map=GROUP_ACTIONS_MAP,
    response_model=GroupMessage,
)
async def add_user_to_group(
    group_id: UUID,
    user_id: UUID,
    current_user: DataFromTokenDTO = Depends(get_current_user_from_token),
    use_case: AddUserToGroup = Depends(get_add_user_to_group_use_case),
):
    await use_case.execute(group_id, user_id, current_user)
    return GroupMessage(message="User added to group successfully")


@group_router.delete(
    "/{group_id}/users/{user_id}",
    error_map=GROUP_ACTIONS_MAP,
    response_model=GroupMessage,
)
async def delete_user_from_group(
    group_id: UUID,
    user_id: UUID,
    current_user: DataFromTokenDTO = Depends(get_current_user_from_token),
    use_case: RemoveUserFromGroup = Depends(get_remove_user_from_group_use_case),
):
    await use_case.execute(group_id, user_id, current_user)
    return GroupMessage(message="User deleted from group successfully")
