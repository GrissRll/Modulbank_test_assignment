import os

from fastapi import FastAPI
from httpx import ASGITransport, AsyncClient
from sqlalchemy import Sequence
from sqlalchemy.exc import OperationalError
from sqlalchemy.ext.asyncio import (
    create_async_engine,
    async_sessionmaker,
    AsyncSession,
)
import pytest_asyncio
from unittest.mock import AsyncMock

from app.main import create_app
from app.api.dependency import get_session
from app.db.base import Base
import app.models


@pytest_asyncio.fixture
async def test_engine():
    database_url = os.environ["TEST_DATABASE_URL"]
    async_engine = create_async_engine(url=database_url, echo=False)
    operation_id_seq = Sequence("operation_id_seq", metadata=Base.metadata)
    async with async_engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    try:
        yield async_engine
    finally:
        async with async_engine.begin() as conn:
            await conn.run_sync(Base.metadata.drop_all)
        await async_engine.dispose()


@pytest_asyncio.fixture
async def async_session_maker(test_engine):
    return async_sessionmaker(
        bind=test_engine, class_=AsyncSession, expire_on_commit=False
    )


@pytest_asyncio.fixture
async def app_test(async_session_maker):
    async def _get_session():
        async with async_session_maker() as session:
            try:
                yield session
            finally:
                await session.rollback()

    test_app = create_app()
    test_app.dependency_overrides[get_session] = _get_session

    try:
        yield test_app
    finally:
        test_app.dependency_overrides.clear()


@pytest_asyncio.fixture(scope="function")
async def client(app_test: FastAPI):
    transport = ASGITransport(app=app_test)
    async with AsyncClient(transport=transport, base_url="http://testserver") as c:
        yield c


@pytest_asyncio.fixture
async def broken_db():
    app = create_app()

    broken_session = AsyncMock()
    broken_session.execute.side_effect = OperationalError(
        statement="SELECT 1",
        params=None,
        orig=ConnectionError("Database is unavailable"),
    )

    async def override_get_db():
        yield broken_session

    app.dependency_overrides[get_session] = override_get_db

    yield app, broken_session

    app.dependency_overrides.clear()
