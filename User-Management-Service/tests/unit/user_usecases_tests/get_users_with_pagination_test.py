import pytest
import asyncio
from source.domain.value_objects import ID, Email, PasswordHash, Name
from source.domain.entities.user import UserEntity
from source.domain.enums.user_role import UserRole
from source.application.use_cases import GetUsersWithPagination
from source.application.dto import UserPaginationDTO, DataFromTokenDTO
from source.application.exceptions import (
    ActionNotAllowedError,
    InvalidSortFieldError,
)


@pytest.mark.asyncio
class TestGetUsersWithPagination:
    async def test_success(self, repository):
        use_case = GetUsersWithPagination(repo=repository)
        generated_users = []
        for i in range(5):
            existing_user = UserEntity(
                id=ID(),
                name=Name("testname"),
                surname=Name("testsurname"),
                username=f"testusername{i}",
                password_hash=PasswordHash("hash_test1234"),
                email=Email(f"test{i}@test.com"),
                role=UserRole.USER,
            )
            generated_users.append(existing_user)
            await repository.add(existing_user)
            await asyncio.sleep(0.001)
        params = UserPaginationDTO(limit=2, page=2, order_by="asc")
        current_user = DataFromTokenDTO(
            user_id=ID().value,
            email="current@current.com",
            role=UserRole.ADMIN,
        )
        list_of_users = await use_case.execute(params=params, current_user=current_user)
        assert list_of_users is not None
        assert len(list_of_users) == 2
        assert list_of_users[0].id == generated_users[2].id.value
        assert list_of_users[1].id == generated_users[3].id.value

    async def test_current_user_have_no_access(self, repository):
        use_case = GetUsersWithPagination(repo=repository)
        current_user = DataFromTokenDTO(
            user_id=ID().value,
            email="current@current.com",
            role=UserRole.USER,
        )
        params = UserPaginationDTO(limit=2, page=2, order_by="asc")
        with pytest.raises(ActionNotAllowedError):
            await use_case.execute(params=params, current_user=current_user)

    async def test_invalid_sort_by_field(self, repository):
        use_case = GetUsersWithPagination(repo=repository)
        current_user = DataFromTokenDTO(
            user_id=ID().value,
            email="current@current.com",
            role=UserRole.ADMIN,
        )
        params = UserPaginationDTO(limit=2, page=2, sort_by="invalid")
        with pytest.raises(InvalidSortFieldError):
            await use_case.execute(params=params, current_user=current_user)

    async def test_moderator_get_users(self, repository):
        use_case = GetUsersWithPagination(repo=repository)
        group_id = ID().value
        generated_users = []

        for i in range(3):
            existing_user = UserEntity(
                id=ID(),
                name=Name("testname"),
                surname=Name("testsurname"),
                username=f"testusername{i}",
                password_hash=PasswordHash("hash_test1234"),
                email=Email(f"test{i}@test.com"),
                role=UserRole.USER,
                group_id=group_id,
            )
            generated_users.append(existing_user)
            await repository.add(existing_user)
            await asyncio.sleep(0.001)

        for i in range(3, 5):
            existing_user = UserEntity(
                id=ID(),
                name=Name("testname"),
                surname=Name("testsurname"),
                username=f"testusername{i}",
                password_hash=PasswordHash("hash_test1234"),
                email=Email(f"test{i}@test.com"),
                role=UserRole.USER,
            )
            generated_users.append(existing_user)
            await repository.add(existing_user)
            await asyncio.sleep(0.001)

        current_user = DataFromTokenDTO(
            user_id=ID().value,
            email="current@current.com",
            role=UserRole.MODERATOR,
            group_id=group_id,
        )

        params = UserPaginationDTO(limit=10, page=1)

        list_of_users = await use_case.execute(params=params, current_user=current_user)

        assert len(list_of_users) == 3

        for user in list_of_users:
            assert user.group_id == group_id
