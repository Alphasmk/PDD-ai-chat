from source.domain.entities.user import UserEntity as User
from source.application.dto import UserReadDTO, GroupReadDTO
from source.domain.entities.group import GroupEntity as Group


class UseCaseBase:
    def _to_group_read_dto(self, group: Group) -> GroupReadDTO:
        return GroupReadDTO(
            id=group.id.value, name=group.name, created_at=group.created_at
        )

    def _to_user_read_dto(self, user: User) -> UserReadDTO:
        return UserReadDTO(
            id=user.id.value,
            name=user.name.value,
            username=user.username,
            surname=user.surname.value,
            email=user.email.value,
            phone_number=user.phone_number,
            group_id=user.group_id,
            is_blocked=user.is_blocked,
            role=user.role,
            created_at=user.created_at,
            updated_at=user.updated_at,
        )
