"""Entity class definition"""

from typing import Self
from dataclasses import dataclass, field
from source.domain.value_objects import ID


@dataclass(frozen=True, kw_only=True)
class Entity:
    """Base class for project Entities"""

    id: ID = field(default_factory=ID)

    def __new__(cls, *_args: object, **_kwargs: object) -> Self:
        if cls is Entity:
            raise TypeError("Base Entity cannot be instantiated directly.")
        return object.__new__(cls)
