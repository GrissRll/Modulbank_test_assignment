from datetime import datetime, timezone
from decimal import Decimal

import pytest
from sqlalchemy.exc import IntegrityError

from app.models.operation import Currency, Operation as OperationModel
from app.models.receipt import (
    Receipt as ReceiptModel,
    ReceiptProcessingResult,
    ReceiptResult,
)


def create_operation(
    amount: str = "100.00",
    operation_id: str = "operation-1",
) -> OperationModel:
    return OperationModel(
        operation_id=operation_id,
        amount=Decimal(amount),
        currency=Currency.RUB,
    )


def receipt_data(operation_id: str) -> dict:
    return {
        "operation_id": operation_id,
        "provider_payment_id": "provider-payment-1",
        "result": ReceiptResult.COMPLETED,
        "message": "Payment completed",
        "provider_occurred_at": datetime.now(timezone.utc),
        "processing_result": ReceiptProcessingResult.APPLIED,
        "payload_hash": "a" * 64,
    }


@pytest.mark.asyncio
async def test_create_receipt_success(async_session_maker):
    async with async_session_maker() as session:
        operation = create_operation()
        session.add(operation)
        await session.flush()

        receipt = ReceiptModel(**receipt_data(operation.operation_id))
        session.add(receipt)
        await session.flush()

        assert receipt.id is not None
        assert receipt.operation_id == operation.operation_id
        assert receipt.provider_payment_id == "provider-payment-1"
        assert receipt.result == ReceiptResult.COMPLETED
        assert receipt.message == "Payment completed"
        assert receipt.provider_occurred_at is not None
        assert receipt.processing_result == ReceiptProcessingResult.APPLIED
        assert receipt.payload_hash == "a" * 64
        assert receipt.received_at is not None


@pytest.mark.asyncio
async def test_receipt_received_at_is_generated_by_default(async_session_maker):
    async with async_session_maker() as session:
        operation = create_operation()
        session.add(operation)
        await session.flush()

        receipt = ReceiptModel(**receipt_data(operation.operation_id))
        session.add(receipt)
        await session.flush()

        assert receipt.id is not None
        assert receipt.received_at is not None


@pytest.mark.asyncio
async def test_receipt_requires_existing_operation(async_session_maker):
    async with async_session_maker() as session:
        receipt = ReceiptModel(**receipt_data("operation-missing"))
        session.add(receipt)

        with pytest.raises(IntegrityError):
            await session.flush()


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "required_field",
    [
        "provider_payment_id",
        "result",
        "message",
        "provider_occurred_at",
        "processing_result",
        "payload_hash",
    ],
)
async def test_receipt_required_fields(
    async_session_maker,
    required_field,
):
    async with async_session_maker() as session:
        operation = create_operation()
        session.add(operation)
        await session.flush()

        data = receipt_data(operation.operation_id)
        data.pop(required_field)
        receipt = ReceiptModel(**data)
        session.add(receipt)

        with pytest.raises(IntegrityError):
            await session.flush()


@pytest.mark.asyncio
async def test_multiple_receipts_are_allowed_for_operation(async_session_maker):
    async with async_session_maker() as session:
        operation = create_operation()
        session.add(operation)
        await session.flush()

        first_data = receipt_data(operation.operation_id)
        second_data = receipt_data(operation.operation_id)
        second_data["provider_payment_id"] = "provider-payment-2"
        second_data["payload_hash"] = "b" * 64

        first_receipt = ReceiptModel(**first_data)
        second_receipt = ReceiptModel(**second_data)
        session.add_all([first_receipt, second_receipt])
        await session.flush()

        assert first_receipt.id is not None
        assert second_receipt.id is not None
        assert first_receipt.id != second_receipt.id


@pytest.mark.asyncio
async def test_duplicate_payload_hash_is_allowed_by_database(async_session_maker):
    async with async_session_maker() as session:
        operation = create_operation()
        session.add(operation)
        await session.flush()

        first_data = receipt_data(operation.operation_id)
        second_data = receipt_data(operation.operation_id)
        second_data["provider_payment_id"] = "provider-payment-2"

        first_receipt = ReceiptModel(**first_data)
        second_receipt = ReceiptModel(**second_data)
        session.add_all([first_receipt, second_receipt])
        await session.flush()

        assert first_receipt.payload_hash == second_receipt.payload_hash


@pytest.mark.asyncio
async def test_receipts_are_deleted_with_operation(async_session_maker):
    async with async_session_maker() as session:
        operation = create_operation()
        session.add(operation)
        await session.flush()

        receipt = ReceiptModel(**receipt_data(operation.operation_id))
        session.add(receipt)
        await session.flush()
        receipt_id = receipt.id
        session.expunge(receipt)

        await session.delete(operation)
        await session.flush()

        deleted_receipt = await session.get(ReceiptModel, receipt_id)
        assert deleted_receipt is None
