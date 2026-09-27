from dataclasses import dataclass
from source.domain.value_objects.user_role import UserRole


@dataclass(frozen=True, slots=True, kw_only=True)
class RoleEntity:
    id: int
    value: UserRole
    label: str

    def __post_init__(self) -> None:
        if self.id != self.value.storage_id:
            raise ValueError("Role identifier does not match its value")
