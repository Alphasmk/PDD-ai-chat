import asyncio
import logging

from source.settings.config import get_settings
from source.infrastructure.database import get_database
from source.presentation.api.dependencies import create_super_user_factory


async def main():
    settings = get_settings()

    db = get_database()
    await db.init_db(str(settings.database.postgres_url))

    try:
        async for session in db.get_session():
            use_case = create_super_user_factory(session)
            await use_case.execute(
                settings.super_user.username,
                settings.super_user.password.get_secret_value(),
                settings.super_user.email,
            )

        logging.info("Superuser created successfully")
    except Exception as e:
        logging.error(f"Error when creating superuser: {e}")
    finally:
        await db.close()


if __name__ == "__main__":
    asyncio.run(main())
