from source.domain.entities.user import UserEntity
from source.domain.value_objects import Name, Email, PasswordHash
from source.application.dto import DataFromTokenDTO


def make_user(username: str = "alice", image_s3_path: str | None = None) -> UserEntity:
    return UserEntity(
        name=Name("Alice"),
        surname=Name("Smith"),
        username=username,
        email=Email(f"{username}@example.com"),
        password_hash=PasswordHash("hash_Test1234"),
        image_s3_path=image_s3_path,
    )


def subject(user: UserEntity) -> DataFromTokenDTO:
    return DataFromTokenDTO(user_id=user.id.value, email=user.email.value)
