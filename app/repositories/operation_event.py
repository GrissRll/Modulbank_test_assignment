from collections.abc import Sequence
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.operation_event import OperationEvent as EventModel


class OperationEventRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def create(self, event_data: dict) -> EventModel:
        """
        Create a payment event and flush it to the database.
        """
        event = EventModel(**event_data)
        self.db.add(event)
        await self.db.flush()
        return event

    async def get_events(self, operation_id: str) -> Sequence[EventModel]:

        stmt = (
            select(EventModel)
            .where(EventModel.operation_id == operation_id)
            .order_by(EventModel.occurred_at, EventModel.event_id)
        )

        events = (await self.db.scalars(stmt)).all()

        return events

    async def get_next_event_id(self, operation_id: str):
        stmt = select(func.coalesce(func.max(EventModel.event_id), 0) + 1).where(
            EventModel.operation_id == operation_id
        )

        result = await self.db.scalar(stmt)

        return int(result)
