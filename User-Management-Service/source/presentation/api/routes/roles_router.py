from fastapi import APIRouter, Depends
from source.application.dto import DataFromTokenDTO
from source.application.interfaces import IUserRepository
from source.application.interfaces.roles import IRoleRepository
from source.application.use_cases.role_use_cases import ListRoles
from source.presentation.api.dependencies.auth import get_current_user_from_token
from source.presentation.api.dependencies.adapters import (
    get_user_repository,
    get_role_repository,
)
from source.presentation.api.schemas.roles import RolesResponse, RoleResponse
from source.presentation.api.schemas.base import ErrorResponse

roles_router = APIRouter(
    prefix="/api/v1/roles",
    tags=["Roles"],
    responses={code: {"model": ErrorResponse} for code in (401, 403, 503)},
)


async def get_list_roles(
    repo: IUserRepository = Depends(get_user_repository),
    roles: IRoleRepository = Depends(get_role_repository),
) -> ListRoles:
    return ListRoles(repo, roles)


@roles_router.get("", response_model=RolesResponse)
async def list_roles(
    actor: DataFromTokenDTO = Depends(get_current_user_from_token),
    usecase: ListRoles = Depends(get_list_roles),
) -> RolesResponse:
    return RolesResponse(
        items=[
            RoleResponse(value=item.value, label=item.label)
            for item in await usecase.execute(actor)
        ]
    )
