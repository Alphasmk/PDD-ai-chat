from types import TracebackType
from typing import Self
from source.application.interfaces.unit_of_work import IUserUnitOfWork
from source.application.exceptions.user_exceptions import ServiceUnavailableError
from tests.adapters.user_repository import FakeUserRepository


class FakeUnitOfWork(IUserUnitOfWork):
    repository: FakeUserRepository

    def __init__(
        self, repository: FakeUserRepository, fail_commit: bool = False
    ) -> None:
        self.repository = repository
        self.fail_commit = fail_commit
        self.committed = False

    async def __aenter__(self) -> Self:
        self.before = self.repository.users.copy()
        return self

    async def __aexit__(
        self,
        exc_type: type[BaseException] | None,
        exc: BaseException | None,
        traceback: TracebackType | None,
    ) -> None:
        if not self.committed:
            await self.rollback()

    async def commit(self) -> None:
        if self.fail_commit:
            raise ServiceUnavailableError()
        self.committed = True

    async def rollback(self) -> None:
        self.repository.users = self.before.copy()
