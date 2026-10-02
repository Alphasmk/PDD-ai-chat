from abc import ABC, abstractmethod
from collections.abc import Callable
from types import TracebackType
from typing import Self
from source.application.interfaces.repositories import IUserRepository


class IUserUnitOfWork(ABC):
    repository: IUserRepository

    @abstractmethod
    async def __aenter__(self) -> Self: ...

    @abstractmethod
    async def __aexit__(
        self,
        exc_type: type[BaseException] | None,
        exc: BaseException | None,
        traceback: TracebackType | None,
    ) -> None: ...

    @abstractmethod
    async def commit(self) -> None: ...

    @abstractmethod
    async def rollback(self) -> None: ...


UnitOfWorkFactory = Callable[[], IUserUnitOfWork]
