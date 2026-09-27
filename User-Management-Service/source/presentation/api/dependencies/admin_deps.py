from fastapi import Depends
from source.application.interfaces.unit_of_work import UnitOfWorkFactory
from source.application.use_cases.admin_use_cases import (
    ChangeUserRole,
    BlockUser,
    ListUsers,
)
from source.application.interfaces import IUserRepository
from source.presentation.api.dependencies.adapters import (
    get_unit_of_work_factory,
    get_user_repository,
)


async def get_change_role(
    factory: UnitOfWorkFactory = Depends(get_unit_of_work_factory),
) -> ChangeUserRole:
    return ChangeUserRole(factory)


async def get_block_user(
    factory: UnitOfWorkFactory = Depends(get_unit_of_work_factory),
) -> BlockUser:
    return BlockUser(factory)


async def get_list_users(
    repo: IUserRepository = Depends(get_user_repository),
) -> ListUsers:
    return ListUsers(repo)
