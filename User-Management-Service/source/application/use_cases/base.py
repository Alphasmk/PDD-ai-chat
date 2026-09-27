from source.domain.entities.user import UserEntity as User
from source.application.dto import UserReadDTO


class UseCaseBase:
    def _to_user_read_dto(self, user: User) -> UserReadDTO:
        return UserReadDTO(
            id=user.id.value,
            name=user.name.value,
            surname=user.surname.value,
            username=user.username,
            email=user.email.value,
            phone_number=user.phone_number,
            created_at=user.created_at,
            updated_at=user.updated_at,
            role=user.role,
            is_blocked=user.is_blocked,
            is_superadmin=user.is_superadmin,
        )
