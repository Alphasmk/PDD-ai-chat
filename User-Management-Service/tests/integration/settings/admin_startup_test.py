import asyncio
import os
import subprocess
from collections.abc import AsyncIterator
from uuid import uuid4
import pytest
import pytest_asyncio
from sqlalchemy import text, select
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from source.infrastructure.database.models import User
from tests.integration.startup_harness import start_runner
from source.infrastructure.database.bootstrap import migrate, INITIALIZATION_LOCK


@pytest_asyncio.fixture
async def startup_database() -> AsyncIterator[tuple[str, str]]:
    url = os.environ.get("UMS_TEST_POSTGRES_URL")
    if not url:
        if os.environ.get("UMS_REQUIRE_POSTGRES") == "1":
            pytest.fail("PostgreSQL required for startup checks")
        pytest.skip("Isolated PostgreSQL required for independent startup processes")
    schema = "ums_test_" + uuid4().hex
    engine = create_async_engine(url)
    async with engine.begin() as connection:
        await connection.execute(text(f'CREATE SCHEMA "{schema}"'))
    try:
        yield url, schema
    finally:
        async with engine.begin() as connection:
            await connection.execute(text(f'DROP SCHEMA "{schema}" CASCADE'))
        await engine.dispose()


def initial() -> dict[str, str]:
    return {
        "SUPERADMIN_USERNAME": "owner",
        "SUPERADMIN_EMAIL": "owner@example.com",
        "SUPERADMIN_PASSWORD": "StartupTest1234",
        "SUPERADMIN_NAME": "Alice",
        "SUPERADMIN_SURNAME": "Smith",
    }


async def run_startup(
    url: str, schema: str, settings: dict[str, str]
) -> tuple[int, str]:
    process = start_runner(url, schema, settings)
    try:
        stdout, stderr = await asyncio.to_thread(process.communicate, timeout=20)
    finally:
        if process.poll() is None:
            process.kill()
            process.wait()
    assert process.returncode is not None
    return process.returncode, stdout + stderr


async def test_parallel_and_three_restarts(startup_database: tuple[str, str]) -> None:
    url, schema = startup_database
    results = await asyncio.gather(
        run_startup(url, schema, initial()), run_startup(url, schema, initial())
    )
    assert all(code == 0 for code, _ in results)
    engine = create_async_engine(
        url, connect_args={"server_settings": {"search_path": schema}}
    )
    try:
        async with AsyncSession(engine) as session:
            first = (await session.execute(select(User))).scalar_one()
            snapshot = (
                first.id,
                first.password_hash,
                first.username,
                first.role_id,
                first.is_superadmin,
            )
        for _ in range(3):
            code, output = await run_startup(
                url, schema, {key: "" for key in initial()}
            )
            assert code == 0 and "initial settings are not applied" in output
            async with AsyncSession(engine) as session:
                owner = (await session.execute(select(User))).scalar_one()
                assert (
                    owner.id,
                    owner.password_hash,
                    owner.username,
                    owner.role_id,
                    owner.is_superadmin,
                ) == snapshot
        changed = initial()
        changed["SUPERADMIN_USERNAME"] = "different"
        changed["SUPERADMIN_PASSWORD"] = "invalid"
        code, output = await run_startup(url, schema, changed)
        assert (
            code == 0
            and "initial settings are not applied" in output
            and "invalid" not in output
        )
        async with AsyncSession(engine) as session:
            owner = (await session.execute(select(User))).scalar_one()
            owner.username = "renamed"
            await session.commit()
        assert (await run_startup(url, schema, initial()))[0] == 0
        async with AsyncSession(engine) as session:
            owner = (await session.execute(select(User))).scalar_one()
            assert (
                owner.username == "renamed"
                and owner.id == snapshot[0]
                and owner.password_hash == snapshot[1]
            )
    finally:
        await engine.dispose()


async def test_failure_then_recovery(startup_database: tuple[str, str]) -> None:
    url, schema = startup_database
    code, output = await run_startup(url, schema, {key: "" for key in initial()})
    assert code != 0 and "missing_initial_data" in output
    settings = initial()
    settings["SUPERADMIN_PASSWORD"] = "do-not-print"
    code, output = await run_startup(url, schema, settings)
    assert (
        code != 0 and "invalid_initial_data" in output and "do-not-print" not in output
    )
    assert (await run_startup(url, schema, initial()))[0] == 0


async def test_identity_conflict_does_not_promote(
    startup_database: tuple[str, str],
) -> None:
    url, schema = startup_database
    engine = create_async_engine(
        url, connect_args={"server_settings": {"search_path": schema}}
    )
    try:
        async with engine.begin() as connection:
            await connection.run_sync(migrate)
        async with AsyncSession(engine) as session:
            session.add(
                User(
                    name="Alice",
                    surname="Smith",
                    username="owner",
                    email="ordinary@example.com",
                    password_hash="test",
                )
            )
            await session.commit()
        code, output = await run_startup(url, schema, initial())
        assert (
            code != 0
            and "identity_conflict" in output
            and "StartupTest1234" not in output
        )
        async with AsyncSession(engine) as session:
            user = (await session.execute(select(User))).scalar_one()
            assert user.role_id == 1 and not user.is_superadmin
    finally:
        await engine.dispose()


async def test_lock_timeout(startup_database: tuple[str, str]) -> None:
    url, schema = startup_database
    engine = create_async_engine(url)
    try:
        async with engine.connect() as connection:
            await connection.execute(
                text("SELECT pg_advisory_lock(:key)"), {"key": INITIALIZATION_LOCK}
            )
            try:
                settings = initial() | {"UMS_INITIALIZE_LOCK_TIMEOUT": "0.2"}
                code, output = await run_startup(url, schema, settings)
                assert code != 0 and "initialization_timeout" in output
            finally:
                await connection.execute(
                    text("SELECT pg_advisory_unlock(:key)"),
                    {"key": INITIALIZATION_LOCK},
                )
    finally:
        await engine.dispose()


async def test_unavailable_database_has_safe_diagnostics() -> None:
    url = "postgresql+asyncpg://unused:never-print-this@127.0.0.1:1/disposable"
    code, output = await run_startup(url, "ums_test_unavailable", initial())
    assert code != 0 and "database_unavailable" in output
    assert "never-print-this" not in output and "StartupTest1234" not in output


async def test_interrupted_insert_rolls_back_and_recovers(
    startup_database: tuple[str, str],
) -> None:
    url, schema = startup_database
    process = start_runner(
        url, schema, initial(), module="tests.integration.interrupted_startup"
    )
    try:
        output, _ = await asyncio.to_thread(process.communicate, timeout=20)
    finally:
        if process.poll() is None:
            process.kill()
            process.wait()
    assert process.returncode == 17 and "before_bootstrap_commit" in output
    engine = create_async_engine(
        url, connect_args={"server_settings": {"search_path": schema}}
    )
    try:
        async with AsyncSession(engine) as session:
            assert (await session.execute(select(User))).scalars().all() == []
        assert (await run_startup(url, schema, initial()))[0] == 0
        async with AsyncSession(engine) as session:
            owner = (await session.execute(select(User))).scalar_one()
            assert owner.role_id == 2 and owner.is_superadmin
    finally:
        await engine.dispose()


@pytest.mark.parametrize(
    "scenario, category",
    [
        ("missing", "missing_initial_data"),
        ("invalid", "invalid_initial_data"),
        ("conflict", "identity_conflict"),
        ("unavailable", "database_unavailable"),
        ("timeout", "initialization_timeout"),
    ],
)
async def test_container_entrypoint_does_not_exec_after_failure(
    startup_database: tuple[str, str], scenario: str, category: str
) -> None:
    docker = os.environ.get("UMS_TEST_DOCKER")
    project = os.environ.get("UMS_TEST_COMPOSE_PROJECT")
    env_file = os.environ.get("UMS_TEST_COMPOSE_ENV_FILE", ".env.test")
    if not docker or not project:
        pytest.skip(
            "Explicit disposable Compose project and Docker path required for entrypoint checks"
        )
    if not project.startswith("ums-"):
        pytest.fail(
            "Entrypoint checks require an explicitly named disposable ums- project"
        )
    url, schema = startup_database
    engine = create_async_engine(
        url, connect_args={"server_settings": {"search_path": schema}}
    )
    settings = initial() | {"UMS_INITIALIZE_SCHEMA": schema}
    if scenario == "missing":
        settings["SUPERADMIN_PASSWORD"] = ""
    elif scenario == "invalid":
        settings["SUPERADMIN_PASSWORD"] = "do-not-print"
    elif scenario == "unavailable":
        settings["UMS_INITIALIZE_DATABASE_URL"] = (
            "postgresql+asyncpg://unused:never-print@127.0.0.1:1/disposable"
        )
    elif scenario == "timeout":
        settings["UMS_INITIALIZE_LOCK_TIMEOUT"] = "0.2"
    elif scenario == "conflict":
        async with engine.begin() as connection:
            await connection.run_sync(migrate)
        async with AsyncSession(engine) as session:
            session.add(
                User(
                    name="Alice",
                    surname="Smith",
                    username="owner",
                    email="ordinary@example.com",
                    password_hash="test",
                )
            )
            await session.commit()
    try:
        async with engine.connect() as lock_connection:
            if scenario == "timeout":
                await lock_connection.execute(
                    text("SELECT pg_advisory_lock(:key)"), {"key": INITIALIZATION_LOCK}
                )
            try:
                command = [
                    docker,
                    "compose",
                    "--env-file",
                    env_file,
                    "-p",
                    project,
                    "-f",
                    "docker-compose.test.yaml",
                    "--profile",
                    "startup",
                    "run",
                    "--rm",
                    "--no-deps",
                ]
                for key, value in settings.items():
                    command.extend(["-e", f"{key}={value}"])
                command.extend(
                    ["app_test", "python", "-c", "print('HTTP_WOULD_START')"]
                )
                result = await asyncio.to_thread(
                    subprocess.run,
                    command,
                    capture_output=True,
                    text=True,
                    timeout=30,
                    creationflags=subprocess.CREATE_NO_WINDOW if os.name == "nt" else 0,
                )
                output = result.stdout + result.stderr
                assert result.returncode != 0 and category in output
                assert (
                    "HTTP_WOULD_START" not in output
                    and "do-not-print" not in output
                    and "never-print" not in output
                )
            finally:
                if scenario == "timeout":
                    await lock_connection.execute(
                        text("SELECT pg_advisory_unlock(:key)"),
                        {"key": INITIALIZATION_LOCK},
                    )
    finally:
        await engine.dispose()
