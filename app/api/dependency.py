from fastapi import Request, Depends
from typing import AsyncGenerator
from sqlalchemy.ext.asyncio import AsyncSession

from app.repositories.operations import OperationRepository
from app.repositories.receipt import ReceiptRepository
from app.repositories.operation_event import OperationEventRepository
from app.repositories.dispatch import PaymentDispatchRepository
from app.services.operation_service import OperationService


async def get_session(request: Request) -> AsyncGenerator[AsyncSession, None]:
    session_maker = request.app.state.async_session_maker

    async with session_maker() as session:
        yield session


def get_operation_repository(
    db: AsyncSession = Depends(get_session),
) -> OperationRepository:
    return OperationRepository(db=db)


def get_receipt_repository(
    db: AsyncSession = Depends(get_session),
) -> ReceiptRepository:
    return ReceiptRepository(db=db)


def get_event_repository(
    db: AsyncSession = Depends(get_session),
) -> OperationEventRepository:
    return OperationEventRepository(db=db)


def get_dispatch_repository(
    db: AsyncSession = Depends(get_session),
) -> PaymentDispatchRepository:
    return PaymentDispatchRepository(db=db)


def get_operation_service(
    db: AsyncSession = Depends(get_session),
    operation_repository: OperationRepository = Depends(get_operation_repository),
    dispatch_repository: PaymentDispatchRepository = Depends(get_dispatch_repository),
    event_repository: OperationEventRepository = Depends(get_event_repository),
) -> OperationService:
    return OperationService(
        db=db,
        operation_repo=operation_repository,
        dispatch_repo=dispatch_repository,
        event_repo=event_repository,
    )
