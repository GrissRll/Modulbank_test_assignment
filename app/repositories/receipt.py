from sqlalchemy import select, Sequence
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.receipt import Receipt as ReceiptModel



class ReceiptRepository:
    def __init__(self, db: AsyncSession):
        self.db = db


    async def create(self, receipt_data: dict) -> ReceiptModel:
        """
        Create receipt for operation by callback_data.
        """
        event = ReceiptModel(**receipt_data)
        self.db.add(event)
        await self.db.flush()
        return event

    async def get_by_operation_and_payload_hash(
        self,
        operation_id: str,
        payload_hash: str,
    ) -> ReceiptModel | None:
        """
        Return a previously received callback receipt.
        """
        stmt = select(ReceiptModel).where(
            ReceiptModel.operation_id == operation_id,
            ReceiptModel.payload_hash == payload_hash,
        )
        return await self.db.scalar(stmt)