from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List
from source.application.interfaces import IGroupRepository
from source.domain.entities.user import UserEntity
from source.domain.entities.group import GroupEntity
from source.infrastructure.database.models import User as UserORM, Group as GroupORM
from source.application.dto import GroupEditDTO
from source.domain.value_objects import ID, Email, Name, PasswordHash


class GroupRepository(IGroupRepository):
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    def _to_domain(self, group_orm: GroupORM) -> GroupEntity:
        return GroupEntity(
            id=ID(group_orm.id), name=group_orm.name, created_at=group_orm.created_at
        )

    def _user_to_domain(self, user_orm: UserORM) -> UserEntity:
        return UserEntity(
            id=ID(user_orm.id),
            name=Name.from_trusted(user_orm.name),
            surname=Name.from_trusted(user_orm.surname),
            username=user_orm.username,
            password_hash=PasswordHash(user_orm.password_hash),
            email=Email.from_trusted(user_orm.email),
            is_blocked=user_orm.is_blocked,
            group_id=user_orm.group_id,
            phone_number=user_orm.phone_number,
            image_s3_path=user_orm.image_s3_path,
            role=user_orm.role,
        )

    async def get_by_id(self, group_id: ID) -> GroupEntity | None:
        group = await self.session.get(GroupORM, group_id.value)
        if not group:
            return None
        return self._to_domain(group)

    async def get_by_name(self, name: str) -> GroupEntity | None:
        query = select(GroupORM).where(GroupORM.name == name)
        result = await self.session.execute(query)
        group_orm = result.unique().scalar_one_or_none()

        if group_orm:
            return self._to_domain(group_orm)
        return None

    async def add(self, group: GroupEntity) -> GroupEntity | None:
        group_orm = GroupORM(id=group.id.value, name=group.name)
        self.session.add(group_orm)
        await self.session.flush()

        return self._to_domain(group_orm)

    async def update(self, group_id: ID, data: GroupEditDTO) -> GroupEntity | None:
        group_orm = await self.session.get(GroupORM, group_id.value)
        if not group_orm:
            return None

        if data.name is not None:
            group_orm.name = data.name

        await self.session.flush()
        return self._to_domain(group_orm)

    async def delete(self, group_id: ID) -> GroupEntity | None:
        group_orm = await self.session.get(GroupORM, group_id.value)

        if not group_orm:
            return None

        await self.session.delete(group_orm)
        await self.session.flush()
        return self._to_domain(group_orm)

    async def add_user_to_group(self, group_id: ID, user_id: ID) -> None:
        user_orm = await self.session.get(UserORM, user_id.value)

        if user_orm:
            user_orm.group_id = group_id.value
            await self.session.flush()

    async def is_user_in_group(self, group_id: ID, user_id: ID) -> bool | None:
        user_orm = await self.session.get(UserORM, user_id.value)

        if not user_orm:
            return None

        return user_orm.group_id == group_id.value and user_orm.group_id is not None

    async def delete_user_from_group(self, group_id: ID, user_id: ID) -> None:
        user_orm = await self.session.get(UserORM, user_id.value)

        if user_orm and user_orm.group_id == group_id.value:
            user_orm.group_id = None
            await self.session.flush()

    async def get_users_in_group(self, group_id: ID) -> List[UserEntity]:
        query = select(UserORM).where(UserORM.group_id == group_id.value)

        result = await self.session.execute(query)
        users_orm = result.scalars().all()

        if not users_orm:
            return []

        return [self._user_to_domain(user) for user in users_orm]
