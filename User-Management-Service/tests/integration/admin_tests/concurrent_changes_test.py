import asyncio
from dataclasses import replace
from uuid import UUID
import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncEngine, AsyncSession, async_sessionmaker
from source.application.use_cases.admin_use_cases import ChangeUserRole, BlockUser
from source.application.use_cases.user_use_cases import DeleteUser
from source.application.dto import DataFromTokenDTO
from source.application.exceptions import UserNotFoundError
from source.application.exceptions.user_exceptions import (
    InvalidTargetStateError,
    UserBlockedError,
)
from source.domain.value_objects import ID, Name
from source.domain.value_objects.user_role import UserRole
from source.domain.entities.user import UserEntity
from source.infrastructure.database.user_repository import UserRepository
from source.infrastructure.database.session import UserUnitOfWork
from tests.integration.conftest import seeded_account, Account


def actor(account: Account) -> DataFromTokenDTO:
    return DataFromTokenDTO(user_id=UUID(account.id), email="unused@example.com")


class BarrierRepository(UserRepository):
    def __init__(self, session: AsyncSession, barrier: asyncio.Barrier) -> None:
        super().__init__(session)
        self.barrier = barrier

    async def get_for_update(self, user_id: ID) -> "UserEntity | None":
        await self.barrier.wait()
        return await super().get_for_update(user_id)


class BarrierUnitOfWork(UserUnitOfWork):
    def __init__(
        self, maker: async_sessionmaker[AsyncSession], barrier: asyncio.Barrier
    ) -> None:
        super().__init__(maker)
        self.barrier = barrier

    async def __aenter__(self) -> "BarrierUnitOfWork":
        await super().__aenter__()
        self.repository = BarrierRepository(self.session, self.barrier)
        return self


def postgres_only(engine: AsyncEngine) -> None:
    if engine.dialect.name != "postgresql":
        pytest.skip("PostgreSQL row locking is required; SQLite is not evidence")


async def test_promotion_block_race(client: AsyncClient, engine: AsyncEngine) -> None:
    postgres_only(engine)
    owner = await seeded_account(
        client, engine, "owner", UserRole.ADMIN, is_superadmin=True
    )
    admin = await seeded_account(client, engine, "admin", UserRole.ADMIN)
    user = await seeded_account(client, engine, "target")
    maker = async_sessionmaker(engine, expire_on_commit=False)
    barrier = asyncio.Barrier(2)

    def factory() -> BarrierUnitOfWork:
        return BarrierUnitOfWork(maker, barrier)

    results = await asyncio.wait_for(
        asyncio.gather(
            ChangeUserRole(factory).execute(
                actor(owner), UUID(user.id), UserRole.ADMIN
            ),
            BlockUser(factory).execute(actor(admin), UUID(user.id)),
            return_exceptions=True,
        ),
        timeout=10,
    )
    assert sum(isinstance(result, InvalidTargetStateError) for result in results) == 1
    async with maker() as session:
        final = await UserRepository(session).get_by_id(ID(UUID(user.id)))
        assert final is not None
        assert (final.role is UserRole.ADMIN and not final.is_blocked) or (
            final.role is UserRole.USER and final.is_blocked
        )


async def test_delete_block_race(client: AsyncClient, engine: AsyncEngine) -> None:
    postgres_only(engine)
    admin = await seeded_account(client, engine, "admin", UserRole.ADMIN)
    user = await seeded_account(client, engine, "target")
    maker = async_sessionmaker(engine, expire_on_commit=False)
    barrier = asyncio.Barrier(2)

    def factory() -> BarrierUnitOfWork:
        return BarrierUnitOfWork(maker, barrier)

    results = await asyncio.wait_for(
        asyncio.gather(
            DeleteUser(factory).execute(actor(user)),
            BlockUser(factory).execute(actor(admin), UUID(user.id)),
            return_exceptions=True,
        ),
        timeout=10,
    )
    assert (
        sum(
            isinstance(result, (UserNotFoundError, UserBlockedError))
            for result in results
        )
        == 1
    )


async def test_two_blocks_and_stale_profile(
    client: AsyncClient, engine: AsyncEngine
) -> None:
    postgres_only(engine)
    owner = await seeded_account(
        client, engine, "owner", UserRole.ADMIN, is_superadmin=True
    )
    user = await seeded_account(client, engine, "target")
    maker = async_sessionmaker(engine, expire_on_commit=False)
    async with maker() as stale_session:
        repo = UserRepository(stale_session)
        stale = await repo.get_by_id(ID(UUID(user.id)))
        assert stale is not None
        await ChangeUserRole(lambda: UserUnitOfWork(maker)).execute(
            actor(owner), UUID(user.id), UserRole.ADMIN
        )
        fresh = await repo.get_for_update(stale.id)
        assert fresh is not None and fresh.role is UserRole.ADMIN
        saved = await repo.update(replace(stale, name=Name("Jane")))
        await stale_session.commit()
        assert (
            saved is not None
            and saved.role is UserRole.ADMIN
            and saved.name.value == "Jane"
        )
    await ChangeUserRole(lambda: UserUnitOfWork(maker)).execute(
        actor(owner), UUID(user.id), UserRole.USER
    )
    barrier = asyncio.Barrier(2)

    def factory() -> BarrierUnitOfWork:
        return BarrierUnitOfWork(maker, barrier)

    results = await asyncio.wait_for(
        asyncio.gather(
            BlockUser(factory).execute(actor(owner), UUID(user.id)),
            BlockUser(factory).execute(actor(owner), UUID(user.id)),
        ),
        timeout=10,
    )
    assert all(result.is_blocked for result in results)
