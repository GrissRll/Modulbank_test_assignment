from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.api.dependency import get_session

router = APIRouter(prefix="/health", tags=["health"])


@router.get("/live", status_code=200)
async def live() -> dict[str, str]:
    return {"app_status": "healthy"}


@router.get("/ready", status_code=200)
async def ready(db: AsyncSession = Depends(get_session)) -> dict[str, str]:
    try:
        await db.execute(select(1))
    except Exception as exc:
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail= {
            "app_status": "not ready",
            "database": "unavailable"
        }) from exc
    return {
            "app_status": "ready",
            "database": "available"
        }

