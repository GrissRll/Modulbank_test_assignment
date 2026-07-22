from collections.abc import Sequence
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.repositories.operations import OperationRepository
from app.repositories.dispatch import PaymentDispatchRepository
from app.repositories.operation_event import OperationEventRepository

from app.schemas.operation_schemas import OperationSchema
from app.models.operation import Operation as OperationModel, OperationStatus
from app.models.operation_event import OperationEvent as EventModel
from app.exceptions.units.operation_exception import (
    OperationExistingError,
    OperationNotFoundError,
)


class OperationService:

    def __init__(
        self,
        db: AsyncSession,
        operation_repo: OperationRepository,
        dispatch_repo: PaymentDispatchRepository,
        event_repo: OperationEventRepository,
    ):
        self.db = db
        self.operation_repo = operation_repo
        self.dispatch_repo = dispatch_repo
        self.event_repo = event_repo

    async def register_operation(
        self, operation_data: OperationSchema
    ) -> OperationModel:
        existing_operation = await self.operation_repo.get_operation_by_id(
            operation_data.operation_id
        )
        if existing_operation is not None:
            raise OperationExistingError()
        try:

            operation = await self.operation_repo.create(operation_data.model_dump())

            event_data = {
                "operation_id": operation.operation_id,
                "event_id": 1,
                "event_type": OperationStatus.CREATED,
                "from_status": None,
                "to_status": OperationStatus.CREATED,
                "message": "Operation created.",
            }
            await self.event_repo.create(event_data)

            await self.db.commit()
        except IntegrityError as exc:
            await self.db.rollback()
            raise OperationExistingError() from exc
        return operation

    async def get_operation_by_id(self, operation_id: str) -> OperationModel:

        existing_operation = await self.operation_repo.get_operation_by_id(operation_id)

        if existing_operation is None:
            raise OperationNotFoundError

        return existing_operation

    async def get_events_by_operation_id(
        self, operation_id: str
    ) -> Sequence[EventModel]:
        existing_operation = await self.operation_repo.get_operation_by_id(operation_id)

        if existing_operation is None:
            raise OperationNotFoundError

        events = await self.event_repo.get_events(operation_id=operation_id)

        return events
