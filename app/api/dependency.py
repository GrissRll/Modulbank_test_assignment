from fastapi import Request
from typing import AsyncGenerator
from sqlalchemy.ext.asyncio import AsyncSession


async def get_session(request: Request) -> AsyncGenerator[AsyncSession, None]:
    session_maker = request.app.state.async_session_maker

    async with session_maker() as session:
        yield session
