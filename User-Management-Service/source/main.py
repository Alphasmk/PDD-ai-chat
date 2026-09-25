"""Main entry point for the User Management Service"""

import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI

from source.settings.config import get_settings
from source.presentation.api.routes.auth_router import auth_router
from source.presentation.api.routes.user_router import user_router
from source.presentation.api.routes.group_router import group_router
from source.infrastructure.message_broker import BrokerHandler
from source.presentation.api.schemas.healtcheck import HealthcheckResponse
from source.infrastructure.database import get_database
from source.infrastructure.cache import get_cache_database


@asynccontextmanager
async def lifespan(app: FastAPI):
    try:
        settings = get_settings()
        logging.basicConfig(
            level=settings.logging.level, format=settings.logging.format
        )

        app.state.database = get_database()
        await app.state.database.init_db(str(settings.database.postgres_url))

        app.state.cache = get_cache_database()
        await app.state.cache.init_db(str(settings.cache.redis_url))

        reset_password_publisher = BrokerHandler()
        await reset_password_publisher.connect()
        app.state.broker = reset_password_publisher

        yield

        await app.state.database.close()

        await app.state.cache.close()

        await reset_password_publisher.close()

    except Exception as e:
        logging.exception(f"Error during application startup: {e}")
        raise

    finally:
        logging.info("Application shutdown complete")


app = FastAPI(lifespan=lifespan)
app.include_router(auth_router)
app.include_router(user_router)
app.include_router(group_router)


@app.get("/healthcheck", tags=["Health"], response_model=HealthcheckResponse)
async def health_check():
    """Health check endpoint"""
    return HealthcheckResponse()
