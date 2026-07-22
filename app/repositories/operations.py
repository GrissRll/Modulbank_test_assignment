from app.models.operation import Operation as OperationModel, OperationStatus
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession


class OperationRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_operation_by_id(self, operation_id: str) -> OperationModel | None:
        """
        Return an operation by its primary key.
        """
        stmt = select(OperationModel).where(OperationModel.operation_id == operation_id)
        operation = await self.db.scalar(stmt)
        return operation

    async def get_for_update(self, operation_id: str) -> OperationModel | None:

        stmt = (
            select(OperationModel)
            .where(OperationModel.operation_id == operation_id)
            .with_for_update()
        )
        operation = await self.db.scalar(stmt)
        return operation

    async def create(self, operation_data: dict) -> OperationModel:
        """
        Insert query for creating operation on operation data
        """
        operation = OperationModel(**operation_data)
        self.db.add(operation)
        await self.db.flush()
        return operation

    async def update_status(
        self, operation: OperationModel, new_status: OperationStatus
    ) -> OperationModel:
        """
        Change the operation status and flush the changes.
        """
        operation.status = new_status
        await self.db.flush()
        return operation

    async def update_on_callback(
        self,
        operation: OperationModel,
        new_status: OperationStatus,
        provider_payment_id: str,
    ) -> OperationModel:
        """
        Apply the provider result to an operation.
        """
        operation.status = new_status
        operation.provider_payment_id = provider_payment_id
        await self.db.flush()
        return operation
