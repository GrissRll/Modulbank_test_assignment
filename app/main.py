from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from fastapi import FastAPI

from app.core.config import get_settings
from app.db.session import create_engine_and_session_maker
from app.api.routes.health import router as health_router
from app.exceptions.handler_registration import handlers_registration


@asynccontextmanager
async def lifespan(application: FastAPI) -> AsyncIterator[None]:
    settings = get_settings()
    application.state.settings = settings
    engine, async_session_maker = create_engine_and_session_maker(settings.database_url)

    application.state.async_session_maker = async_session_maker

    try:
        yield
    finally:
        await engine.dispose()


def create_app() -> FastAPI:
    application = FastAPI(
        title="Payment Service",
        lifespan=lifespan,
    )

    handlers_registration(application)

    application.include_router(health_router)

    @application.get("/")
    async def index():
        return {"message": "application worked"}

    return application


app = create_app()
