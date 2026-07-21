from sqlalchemy import select, Sequence
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.operation_event import OperationEvent as EventModel
from app.models.operation import OperationStatus


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
