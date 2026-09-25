from sqlalchemy import select, or_, asc, desc, update
from sqlalchemy.orm import raiseload
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.exc import IntegrityError

from typing import List

from source.application.interfaces import IUserRepository
from source.domain.entities.user import UserEntity
from source.infrastructure.database.models import User as UserORM
from source.application.dto.users_dto import UserPaginationDTO
from source.domain.enums.user_role import UserRole
from source.domain.value_objects import ID, Email, Name, PasswordHash
from source.application.exceptions import (
    UsernameTakenError,
    EmailTakenError,
    PhoneNumberTaken,
)


class UserRepository(IUserRepository):
    def __init__(self, session: AsyncSession):
        self.session = session

    def _to_domain(self, user_orm: UserORM) -> UserEntity:
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

    def _parse_user_error(self, user: UserEntity, e: IntegrityError) -> None:
        error_message = str(e.orig)
        if "ix_users_email" in error_message or "users_email_key" in error_message:
            raise EmailTakenError(user.email.value) from e
        if (
            "ix_users_username" in error_message
            or "users_username_key" in error_message
        ):
            raise UsernameTakenError(user.username) from e
        if (
            "ix_users_phone_number" in error_message
            or "users_phone_number_key" in error_message
        ) and user.phone_number:
            raise PhoneNumberTaken(user.phone_number) from e

    async def add(self, user: UserEntity) -> UserEntity | None:
        user_orm = UserORM(
            id=user.id.value,
            name=user.name.value,
            surname=user.surname.value,
            username=user.username,
            password_hash=user.password_hash.value,
            email=user.email.value,
            phone_number=user.phone_number,
            is_blocked=user.is_blocked,
            group_id=user.group_id,
            image_s3_path=user.image_s3_path,
            role=user.role,
        )

        try:
            self.session.add(user_orm)
            await self.session.flush()
            return self._to_domain(user_orm)
        except IntegrityError as e:
            self._parse_user_error(user, e)
            raise e

    async def update(self, user: UserEntity) -> UserEntity | None:
        values = {
            "name": user.name.value,
            "surname": user.surname.value,
            "username": user.username,
            "email": user.email.value,
            "phone_number": user.phone_number,
            "image_s3_path": user.image_s3_path,
            "group_id": user.group_id,
            "is_blocked": user.is_blocked,
        }
        stmt = (
            update(UserORM)
            .where(UserORM.id == user.id.value)
            .values(**values)
            .returning(UserORM)
        )
        result = await self.session.execute(stmt)
        row = result.scalar_one_or_none()
        return self._to_domain(row) if row else None

    async def delete(self, user: UserEntity) -> None:
        user_orm = await self.session.get(UserORM, user.id.value)
        await self.session.delete(user_orm)

    async def get_by_id(self, user_id: ID) -> UserEntity | None:
        user_orm = await self.session.get(UserORM, user_id.value)
        if not user_orm:
            return None

        return self._to_domain(user_orm)

    async def get_by_email(self, user_email: Email) -> UserEntity | None:
        query = select(UserORM).where(UserORM.email == user_email.value)
        result = await self.session.execute(query)
        user_orm = result.scalar_one_or_none()

        if not user_orm:
            return None

        return self._to_domain(user_orm)

    async def get_by_username(self, username: str) -> UserEntity | None:
        query = select(UserORM).where(UserORM.username == username)
        result = await self.session.execute(query)
        user_orm = result.scalar_one_or_none()

        if not user_orm:
            return None

        return self._to_domain(user_orm)

    async def get_users(self, params: UserPaginationDTO) -> List[UserEntity]:
        offset = (params.page - 1) * params.limit

        query = select(UserORM).options(raiseload(UserORM.group))
        if params.group:
            query = query.where(UserORM.group_id == params.group)
        if params.filter_by_name:
            query = query.where(
                or_(
                    UserORM.name.ilike(f"%{params.filter_by_name}%"),
                    UserORM.surname.ilike(f"%{params.filter_by_name}%"),
                )
            )
        if params.sort_by:
            sort_by = getattr(UserORM, params.sort_by, UserORM.created_at)
            if params.order_by == "desc":
                query = query.order_by(desc(sort_by))
            else:
                query = query.order_by(asc(sort_by))

        query = query.limit(params.limit).offset(offset)

        result = await self.session.execute(query)
        users = result.scalars().all()
        return [self._to_domain(user) for user in users]

    async def change_block_state(self, user_id: ID) -> bool | None:
        stmt = (
            update(UserORM)
            .where(UserORM.id == user_id.value)
            .values(is_blocked=~UserORM.is_blocked)
            .returning(UserORM.is_blocked)
        )
        result = await self.session.execute(stmt)
        row = result.scalar_one_or_none()
        return row

    async def change_role(self, user_id: ID, role: UserRole) -> None:
        stmt = (
            update(UserORM)
            .where(UserORM.id == user_id.value)
            .values(role=role)
            .returning(UserORM.role)
        )
        await self.session.execute(stmt)
