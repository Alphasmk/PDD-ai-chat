from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncEngine, AsyncSession, async_sessionmaker
from sqlalchemy import select
from uuid import UUID
from source.main import app
from source.infrastructure.database.models import User
from source.infrastructure.database.session import UserUnitOfWork
from source.presentation.api.dependencies.adapters import (
    get_unit_of_work_factory,
    get_user_repository,
)
from source.application.interfaces import IUserRepository
from source.application.exceptions.user_exceptions import ServiceUnavailableError
from source.domain.value_objects.user_role import UserRole
from tests.integration.conftest import seeded_account
from tests.adapters.user_repository import FakeUserRepository
from source.domain.entities.user import UserEntity
from source.domain.value_objects import ID


async def test_all_preexisting_sessions_are_blocked(
    client: AsyncClient, engine: AsyncEngine
) -> None:
    owner = await seeded_account(
        client, engine, "owner", UserRole.ADMIN, is_superadmin=True
    )
    user = await seeded_account(client, engine, "alice")
    other = await seeded_account(client, engine, "other")
    sessions: list[tuple[str, str]] = [(user.access, user.refresh)]
    for _ in range(2):
        data = (
            await client.post(
                "/api/v1/auth/login", data={"username": "alice", "password": "Test1234"}
            )
        ).json()
        sessions.append((data["access_token"], data["refresh_token"]))
    assert (
        await client.post(f"/api/v1/users/{user.id}/block", headers=owner.headers)
    ).status_code == 200
    for access, refresh in sessions:
        headers = {"Authorization": f"Bearer {access}"}
        for method, path, payload in (
            ("GET", "/users/me", None),
            ("PATCH", "/users/me", {"name": "Jane"}),
            ("DELETE", "/users/me", None),
            ("GET", "/roles", None),
            ("GET", "/users", None),
        ):
            response = await client.request(
                method, "/api/v1" + path, headers=headers, json=payload
            )
            assert response.status_code == 403 and response.json() == {
                "error": "user_blocked"
            }
        client.cookies.clear()
        client.cookies.set("refresh_token", refresh)
        assert (
            await client.post("/api/v1/auth/refresh-token", headers=headers)
        ).status_code == 403
    assert (
        await client.post(
            "/api/v1/auth/login", data={"username": "alice", "password": "wrong"}
        )
    ).status_code == 401
    assert (
        await client.post(
            "/api/v1/auth/login", data={"username": "alice", "password": "Test1234"}
        )
    ).status_code == 403
    assert (
        await client.post(
            "/api/v1/auth/reset-password", json={"email": "alice@example.com"}
        )
    ).status_code == 200
    assert (
        await client.get("/api/v1/users/me", headers=user.headers)
    ).status_code == 403
    assert (
        await client.get("/api/v1/users/me", headers=other.headers)
    ).status_code == 200
    async with AsyncSession(engine) as session:
        stored = (
            await session.execute(select(User).where(User.id == UUID(user.id)))
        ).scalar_one()
        assert stored.is_blocked and stored.role_id == 1 and stored.name == "Alice"


class FailingCommit(UserUnitOfWork):
    async def commit(self) -> None:
        raise ServiceUnavailableError()


async def test_failed_commit_never_confirms_mutation(
    client: AsyncClient, engine: AsyncEngine
) -> None:
    owner = await seeded_account(
        client, engine, "owner", UserRole.ADMIN, is_superadmin=True
    )
    user = await seeded_account(client, engine, "alice")
    maker = async_sessionmaker(engine, expire_on_commit=False)
    app.dependency_overrides[get_unit_of_work_factory] = lambda: (
        lambda: FailingCommit(maker)
    )
    for method, path, headers, payload in (
        ("POST", f"/users/{user.id}/block", owner.headers, None),
        ("PATCH", f"/users/{user.id}/role", owner.headers, {"role": "admin"}),
        ("DELETE", "/users/me", user.headers, None),
    ):
        response = await client.request(
            method, "/api/v1" + path, headers=headers, json=payload
        )
        assert response.status_code == 503 and response.json() == {
            "error": "service_unavailable"
        }
    own = (await client.get("/api/v1/users/me", headers=user.headers)).json()
    assert own["username"] == "alice"
    async with maker() as session:
        stored = await session.get_one(User, UUID(user.id))
        assert stored.role_id == 1 and not stored.is_blocked


class UnavailableRepository(FakeUserRepository):
    async def get_by_id(self, user_id: "ID") -> "UserEntity | None":
        raise ServiceUnavailableError()


async def test_unavailable_current_state_is_fail_closed(
    client: AsyncClient, engine: AsyncEngine
) -> None:
    owner = await seeded_account(
        client, engine, "owner", UserRole.ADMIN, is_superadmin=True
    )

    def unavailable() -> IUserRepository:
        return UnavailableRepository()

    app.dependency_overrides[get_user_repository] = unavailable
    for path in ("/api/v1/roles", "/api/v1/users", "/api/v1/users/me"):
        response = await client.get(path, headers=owner.headers)
        assert response.status_code == 503 and response.json() == {
            "error": "service_unavailable"
        }
