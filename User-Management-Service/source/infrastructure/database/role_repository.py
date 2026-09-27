from sqlalchemy import select
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncSession
from source.application.interfaces.roles import IRoleRepository
from source.application.exceptions.user_exceptions import ServiceUnavailableError
from source.domain.entities.role import RoleEntity
from source.domain.value_objects.user_role import UserRole
from source.infrastructure.database.models.roles import Role


class RoleRepository(IRoleRepository):
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def list_all(self) -> list[RoleEntity]:
        try:
            rows = (
                (
                    await self.session.execute(
                        select(Role)
                        .order_by(Role.id)
                        .execution_options(populate_existing=True)
                    )
                )
                .scalars()
                .all()
            )
        except (SQLAlchemyError, OSError) as error:
            raise ServiceUnavailableError() from error
        return [
            RoleEntity(id=row.id, value=UserRole(row.value), label=row.label)
            for row in rows
        ]
