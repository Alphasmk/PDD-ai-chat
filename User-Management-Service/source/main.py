"""Main entry point for the User Management Service."""

import logging
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from fastapi import FastAPI
from source.settings.config import get_settings
from source.presentation.api.routes.auth_router import auth_router
from source.presentation.api.routes.user_router import user_router
from source.presentation.api.routes.roles_router import roles_router
from source.presentation.api.routes.admin_router import admin_router
from source.infrastructure.message_broker import BrokerHandler
from source.presentation.api.schemas.healtcheck import HealthcheckResponse
from source.infrastructure.database import get_database
from source.infrastructure.cache import get_cache_database
from source.presentation.exceptions import application_error_handler
from source.application.exceptions.base import ApplicationException
from source.domain.exceptions.base import DomainTypeError


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    settings = get_settings()
    logging.basicConfig(level=settings.logging.level, format=settings.logging.format)
    database, cache, broker = get_database(), get_cache_database(), BrokerHandler()
    try:
        await database.init_db(str(settings.database.postgres_url))
        await cache.init_db(str(settings.cache.redis_url))
        await broker.connect()
        app.state.database, app.state.cache, app.state.broker = database, cache, broker
        yield
    finally:
        await database.close()
        await cache.close()
        await broker.close()
        logging.info("Application shutdown complete")


app = FastAPI(lifespan=lifespan)
app.add_exception_handler(ApplicationException, application_error_handler)
app.add_exception_handler(DomainTypeError, application_error_handler)
app.include_router(auth_router)
app.include_router(user_router)
app.include_router(roles_router)
app.include_router(admin_router)


@app.get("/healthcheck", tags=["Health"], response_model=HealthcheckResponse)
async def health_check() -> HealthcheckResponse:
    return HealthcheckResponse()
