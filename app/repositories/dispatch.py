from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.dispatch import PaymentDispatch as DispatchModel
from datetime import datetime


class PaymentDispatchRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def create(self, dispatch_data: dict) -> DispatchModel:
        """
        Create a payment dispatch and flush it to the database.
        """
        dispatch_payment = DispatchModel(**dispatch_data)
        self.db.add(dispatch_payment)
        await self.db.flush()
        return dispatch_payment

    async def get_by_operation_id(self, operation_id: str) -> DispatchModel | None:
        """
        Return a payment dispatch by operation ID.
        """
        stmt = select(DispatchModel).where(DispatchModel.operation_id == operation_id)
        dispatch_payment = await self.db.scalar(stmt)
        return dispatch_payment

    async def update_attempt_count(
        self, dispatch_payment: DispatchModel, time: datetime, error_description: str
    ) -> DispatchModel:
        """
        Record a failed provider request and schedule the next attempt.
        """
        dispatch_payment.attempt_count += 1
        dispatch_payment.next_attempt_at = time
        dispatch_payment.last_error = error_description
        await self.db.flush()
        return dispatch_payment
