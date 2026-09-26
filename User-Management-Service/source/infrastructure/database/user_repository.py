from datetime import datetime, timezone
from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.exc import IntegrityError
from source.application.interfaces import IUserRepository
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


class UserRepository(IUserRepository):
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
            image_s3_path=row.image_s3_path,
            created_at=as_utc(row.created_at),
            updated_at=as_utc(row.updated_at) if row.updated_at is not None else None,
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
            image_s3_path=user.image_s3_path,
            created_at=user.created_at.astimezone(timezone.utc).replace(tzinfo=None),
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
                image_s3_path=user.image_s3_path,
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
        row = await self.session.get(UserORM, user_id.value)
        return self._to_domain(row) if row is not None else None

    async def get_by_email(self, user_email: Email) -> UserEntity | None:
        row = (
            await self.session.execute(
                select(UserORM).where(UserORM.email == user_email.value)
            )
        ).scalar_one_or_none()
        return self._to_domain(row) if row is not None else None

    async def get_by_username(self, username: str) -> UserEntity | None:
        row = (
            await self.session.execute(
                select(UserORM).where(UserORM.username == username)
            )
        ).scalar_one_or_none()
        return self._to_domain(row) if row is not None else None
