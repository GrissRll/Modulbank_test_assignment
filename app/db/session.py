from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)


def create_engine_and_session_maker(
    db_url: str,
) -> tuple[AsyncEngine, async_sessionmaker[AsyncSession]]:
    async_engine = create_async_engine(url=db_url, echo=False)
    async_session_maker = async_sessionmaker(
        bind=async_engine,
        class_=AsyncSession,
        expire_on_commit=False,
    )
    return async_engine, async_session_maker
