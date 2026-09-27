from unittest.mock import AsyncMock
import pytest
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker
from source.application.exceptions.user_exceptions import ServiceUnavailableError
from source.domain.value_objects import ID
from source.infrastructure.database.user_repository import UserRepository
from source.infrastructure.database.session import UserUnitOfWork


@pytest.mark.parametrize("error_type", [ConnectionRefusedError, SQLAlchemyError])
async def test_database_read_failures_have_safe_errors(
    monkeypatch: pytest.MonkeyPatch, error_type: type[Exception]
) -> None:
    async with AsyncSession() as session:
        monkeypatch.setattr(
            session,
            "execute",
            AsyncMock(side_effect=error_type("private connection details")),
        )
        repository = UserRepository(session)
        with pytest.raises(ServiceUnavailableError, match="^service_unavailable$"):
            await repository.get_by_id(ID())
        with pytest.raises(ServiceUnavailableError, match="^service_unavailable$"):
            await repository.list_page(50, 0)


async def test_commit_network_failure_is_safe(monkeypatch: pytest.MonkeyPatch) -> None:
    async with UserUnitOfWork(async_sessionmaker(expire_on_commit=False)) as uow:
        monkeypatch.setattr(
            uow.session,
            "commit",
            AsyncMock(side_effect=ConnectionRefusedError("private connection details")),
        )
        with pytest.raises(ServiceUnavailableError, match="^service_unavailable$"):
            await uow.commit()
