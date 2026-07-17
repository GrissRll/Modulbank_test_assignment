from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.api.dependency import get_session

router = APIRouter(prefix="/health", tags=["health"])


@router.get("/live", status_code=200)
async def live():
    return {"app_status": "healthy"}


@router.get("/ready", status_code=200)
async def ready(db: AsyncSession = Depends(get_session)):
    await db.execute(select(1))
    return {"db_status": "connected"}
