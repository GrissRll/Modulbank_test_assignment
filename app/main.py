from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from fastapi import FastAPI

from app.core.config import get_settings


@asynccontextmanager
async def lifespan(application: FastAPI) -> AsyncIterator[None]:
    settings = get_settings()
    application.state.settings = settings

    yield


app = FastAPI(title="Payment Service", lifespan=lifespan)


@app.get("/")
async def index():
    return {"message": "application worked"}
