from dataclasses import dataclass
from source.application.dto import DataFromTokenDTO
from source.application.interfaces import IUserRepository
from source.application.interfaces.roles import IRoleRepository
from source.application.use_cases.user_use_cases import require_user
from source.domain.value_objects.user_role import UserRole


@dataclass(frozen=True, kw_only=True)
class RoleDTO:
    value: UserRole
    label: str


class ListRoles:
    def __init__(self, repository: IUserRepository, roles: IRoleRepository) -> None:
        self.repository = repository
        self.roles = roles

    async def execute(self, actor: DataFromTokenDTO) -> list[RoleDTO]:
        await require_user(self.repository, actor)
        return [
            RoleDTO(value=role.value, label=role.label)
            for role in await self.roles.list_all()
        ]
