from uuid import UUID
from fastapi import APIRouter, Depends, Query
from source.application.dto import DataFromTokenDTO
from source.application.dto.admin_dto import ChangeRoleDTO, UserPageDTO
from source.application.use_cases.admin_use_cases import (
    ChangeUserRole,
    BlockUser,
    ListUsers,
)
from source.domain.value_objects.user_role import UserRole
from source.presentation.api.dependencies.auth import get_current_user_from_token
from source.presentation.api.dependencies.admin_deps import (
    get_change_role,
    get_block_user,
    get_list_users,
)
from source.presentation.api.routes.admin_route import AdminRoute
from source.presentation.api.schemas.admin import (
    ChangeRoleRequest,
    ChangeRoleResponse,
    UserPageResponse,
)
from source.presentation.api.schemas.base import ErrorResponse

admin_router = APIRouter(
    prefix="/api/v1/users",
    tags=["Administration"],
    route_class=AdminRoute,
    responses={
        code: {"model": ErrorResponse} for code in (401, 403, 404, 409, 422, 503)
    },
)


@admin_router.patch("/{user_id}/role", response_model=ChangeRoleResponse)
async def change_role(
    user_id: UUID,
    body: ChangeRoleRequest,
    actor: DataFromTokenDTO = Depends(get_current_user_from_token),
    usecase: ChangeUserRole = Depends(get_change_role),
) -> ChangeRoleDTO:
    return await usecase.execute(actor, user_id, UserRole(body.role))


@admin_router.get("", response_model=UserPageResponse)
async def list_users(
    limit: int = Query(50, ge=1, le=100),
    offset: int = Query(0, ge=0),
    actor: DataFromTokenDTO = Depends(get_current_user_from_token),
    usecase: ListUsers = Depends(get_list_users),
) -> UserPageDTO:
    return await usecase.execute(actor, limit, offset)


@admin_router.post("/{user_id}/block", response_model=ChangeRoleResponse)
async def block_user(
    user_id: UUID,
    actor: DataFromTokenDTO = Depends(get_current_user_from_token),
    usecase: BlockUser = Depends(get_block_user),
) -> ChangeRoleDTO:
    return await usecase.execute(actor, user_id)
