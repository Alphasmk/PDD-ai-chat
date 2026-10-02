from datetime import datetime, timezone
from sqlalchemy import select, update, Select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.exc import IntegrityError, SQLAlchemyError
from source.application.interfaces import IUserRepository
from source.application.interfaces.bootstrap import IBootstrapRepository
from source.application.exceptions.user_exceptions import ServiceUnavailableError
from source.domain.value_objects.user_role import UserRole
from source.domain.entities.user import UserEntity
from source.infrastructure.database.models import User as UserORM
from source.domain.value_objects import ID, Email, Name, PasswordHash
from source.application.exceptions import (
    UsernameTakenError,
    EmailTakenError,
    PhoneNumberTaken,
)


def as_utc(value: datetime) -> datetime:
    # The retained PostgreSQL columns store naive UTC timestamps.
    return (
        value.replace(tzinfo=timezone.utc)
        if value.tzinfo is None
        else value.astimezone(timezone.utc)
    )


class UserRepository(IUserRepository, IBootstrapRepository):
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    def _to_domain(self, row: UserORM) -> UserEntity:
        return UserEntity(
            id=ID(row.id),
            name=Name.from_trusted(row.name),
            surname=Name.from_trusted(row.surname),
            username=row.username,
            password_hash=PasswordHash(row.password_hash),
            email=Email.from_trusted(row.email),
            phone_number=row.phone_number,
            created_at=as_utc(row.created_at),
            updated_at=as_utc(row.updated_at) if row.updated_at is not None else None,
            role=UserRole.from_storage_id(row.role_id),
            is_blocked=row.is_blocked,
            is_superadmin=row.is_superadmin,
        )

    def _parse_user_error(self, user: UserEntity, error: IntegrityError) -> None:
        message = str(error.orig)
        if (
            "users.email" in message
            or "ix_users_email" in message
            or "users_email_key" in message
        ):
            raise EmailTakenError(user.email.value) from error
        if (
            "users.username" in message
            or "ix_users_username" in message
            or "users_username_key" in message
        ):
            raise UsernameTakenError(user.username) from error
        if (
            "users.phone_number" in message
            or "ix_users_phone_number" in message
            or "users_phone_number_key" in message
        ) and user.phone_number is not None:
            raise PhoneNumberTaken(user.phone_number) from error

    async def add(self, user: UserEntity) -> UserEntity:
        row = UserORM(
            id=user.id.value,
            name=user.name.value,
            surname=user.surname.value,
            username=user.username,
            password_hash=user.password_hash.value,
            email=user.email.value,
            phone_number=user.phone_number,
            created_at=user.created_at.astimezone(timezone.utc).replace(tzinfo=None),
            role_id=user.role.storage_id,
            is_blocked=user.is_blocked,
            is_superadmin=user.is_superadmin,
        )
        try:
            self.session.add(row)
            await self.session.flush()
        except IntegrityError as error:
            await self.session.rollback()
            self._parse_user_error(user, error)
            raise
        return self._to_domain(row)

    async def update(self, user: UserEntity) -> UserEntity | None:
        statement = (
            update(UserORM)
            .where(UserORM.id == user.id.value)
            .values(
                name=user.name.value,
                surname=user.surname.value,
                username=user.username,
                email=user.email.value,
                phone_number=user.phone_number,
            )
            .returning(UserORM)
            .execution_options(populate_existing=True)
        )
        try:
            row = (await self.session.execute(statement)).scalar_one_or_none()
        except IntegrityError as error:
            await self.session.rollback()
            self._parse_user_error(user, error)
            raise
        return self._to_domain(row) if row is not None else None

    async def delete(self, user: UserEntity) -> None:
        row = await self.session.get(UserORM, user.id.value)
        if row is not None:
            await self.session.delete(row)
            await self.session.flush()

    async def get_by_id(self, user_id: ID) -> UserEntity | None:
        return await self._read(select(UserORM).where(UserORM.id == user_id.value))

    async def _read(self, statement: Select[tuple[UserORM]]) -> UserEntity | None:
        try:
            row = (
                await self.session.execute(
                    statement.execution_options(populate_existing=True)
                )
            ).scalar_one_or_none()
        except (SQLAlchemyError, OSError) as error:
            raise ServiceUnavailableError() from error
        return self._to_domain(row) if row is not None else None

    async def get_for_update(self, user_id: ID) -> UserEntity | None:
        return await self._read(
            select(UserORM).where(UserORM.id == user_id.value).with_for_update()
        )

    async def get_superadmin(self) -> UserEntity | None:
        return await self._read(select(UserORM).where(UserORM.is_superadmin.is_(True)))

    async def list_page(self, limit: int, offset: int) -> list[UserEntity]:
        try:
            rows = (
                (
                    await self.session.execute(
                        select(UserORM)
                        .order_by(UserORM.created_at, UserORM.id)
                        .limit(limit)
                        .offset(offset)
                        .execution_options(populate_existing=True)
                    )
                )
                .scalars()
                .all()
            )
        except (SQLAlchemyError, OSError) as error:
            raise ServiceUnavailableError() from error
        return [self._to_domain(row) for row in rows]

    async def set_role(self, user: UserEntity) -> UserEntity:
        row = (
            await self.session.execute(
                update(UserORM)
                .where(UserORM.id == user.id.value)
                .values(
                    role_id=user.role.storage_id,
                    updated_at=as_utc(user.updated_at).replace(tzinfo=None)
                    if user.updated_at
                    else None,
                )
                .returning(UserORM)
                .execution_options(populate_existing=True)
            )
        ).scalar_one()
        return self._to_domain(row)

    async def set_blocked(self, user: UserEntity) -> UserEntity:
        row = (
            await self.session.execute(
                update(UserORM)
                .where(UserORM.id == user.id.value)
                .values(
                    is_blocked=user.is_blocked,
                    updated_at=as_utc(user.updated_at).replace(tzinfo=None)
                    if user.updated_at
                    else None,
                )
                .returning(UserORM)
                .execution_options(populate_existing=True)
            )
        ).scalar_one()
        return self._to_domain(row)

    async def get_by_email(self, user_email: Email) -> UserEntity | None:
        return await self._read(
            select(UserORM).where(UserORM.email == user_email.value)
        )

    async def get_by_username(self, username: str) -> UserEntity | None:
        return await self._read(select(UserORM).where(UserORM.username == username))
