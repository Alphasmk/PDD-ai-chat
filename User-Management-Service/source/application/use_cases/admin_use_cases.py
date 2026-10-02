from uuid import UUID
from source.application.dto import DataFromTokenDTO
from source.application.dto.admin_dto import ChangeRoleDTO, UserPageDTO, AdminUserDTO
from source.application.interfaces import IUserRepository
from source.application.interfaces.unit_of_work import UnitOfWorkFactory
from source.application.use_cases.user_use_cases import require_user
from source.application.exceptions import UserNotFoundError
from source.application.exceptions.user_exceptions import access_error
from source.domain.exceptions.user_access_exceptions import (
    Forbidden,
    UserBlocked,
    ProtectedAccount,
    InvalidTargetState,
)
from source.domain.policies.user_access import require_superadmin, require_admin
from source.domain.value_objects import ID
from source.domain.value_objects.user_role import UserRole


class ChangeUserRole:
    def __init__(self, factory: UnitOfWorkFactory) -> None:
        self.factory = factory

    async def execute(
        self, actor: DataFromTokenDTO, target_id: UUID, role: UserRole
    ) -> ChangeRoleDTO:
        async with self.factory() as uow:
            try:
                require_superadmin(await require_user(uow.repository, actor))
                target = await uow.repository.get_for_update(ID(target_id))
                if target is None:
                    raise UserNotFoundError()
                changed = target.change_role(role)
                if changed is not target:
                    changed = await uow.repository.set_role(changed)
                await uow.commit()
                return ChangeRoleDTO(
                    id=changed.id.value,
                    role=changed.role,
                    is_blocked=changed.is_blocked,
                    is_superadmin=changed.is_superadmin,
                )
            except (
                Forbidden,
                UserBlocked,
                ProtectedAccount,
                InvalidTargetState,
            ) as error:
                raise access_error(error) from error


class ListUsers:
    def __init__(self, repository: IUserRepository) -> None:
        self.repository = repository

    async def execute(
        self, actor: DataFromTokenDTO, limit: int, offset: int
    ) -> UserPageDTO:
        try:
            require_admin(await require_user(self.repository, actor))
        except (Forbidden, UserBlocked) as error:
            raise access_error(error) from error
        return UserPageDTO(
            items=[
                AdminUserDTO.from_user(user)
                for user in await self.repository.list_page(limit, offset)
            ],
            limit=limit,
            offset=offset,
        )


class BlockUser:
    def __init__(self, factory: UnitOfWorkFactory) -> None:
        self.factory = factory

    async def execute(self, actor: DataFromTokenDTO, target_id: UUID) -> ChangeRoleDTO:
        async with self.factory() as uow:
            try:
                require_admin(await require_user(uow.repository, actor))
                target = await uow.repository.get_for_update(ID(target_id))
                if target is None:
                    raise UserNotFoundError()
                changed = target.block()
                if changed is not target:
                    changed = await uow.repository.set_blocked(changed)
                await uow.commit()
                return ChangeRoleDTO(
                    id=changed.id.value,
                    role=changed.role,
                    is_blocked=changed.is_blocked,
                    is_superadmin=changed.is_superadmin,
                )
            except (
                Forbidden,
                UserBlocked,
                ProtectedAccount,
                InvalidTargetState,
            ) as error:
                raise access_error(error) from error
