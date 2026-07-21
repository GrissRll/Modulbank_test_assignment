from datetime import datetime, timezone
from decimal import Decimal

import pytest
import pytest_asyncio

from app.models.operation import Currency, Operation
from app.models.receipt import Receipt, ReceiptProcessingResult, ReceiptResult
from app.repositories.receipt import ReceiptRepository


@pytest_asyncio.fixture
async def db_session(async_session_maker):
    async with async_session_maker() as session:
        yield session
        await session.rollback()


@pytest.fixture
def repository(db_session):
    return ReceiptRepository(db=db_session)


@pytest_asyncio.fixture
async def operation(db_session):
    operation = Operation(
        amount=Decimal("100.00"),
        currency=Currency.RUB,
        description="Order payment",
    )
    db_session.add(operation)
    await db_session.flush()
    return operation


@pytest.fixture
def receipt_data(operation):
    return {
        "operation_id": operation.operation_id,
        "provider_payment_id": "provider-payment-1",
        "result": ReceiptResult.COMPLETED,
        "message": "Payment completed",
        "provider_occurred_at": datetime(2030, 1, 1, 12, 30, tzinfo=timezone.utc),
        "processing_result": ReceiptProcessingResult.APPLIED,
        "payload_hash": "a" * 64,
    }


@pytest_asyncio.fixture
async def receipt(repository, receipt_data):
    return await repository.create(receipt_data)


@pytest.mark.asyncio
async def test_create_persists_and_returns_receipt(
    repository, db_session, receipt_data
):
    result = await repository.create(receipt_data)
    receipt_id = result.id
    db_session.expunge(result)

    persisted_receipt = await db_session.get(Receipt, receipt_id)

    assert persisted_receipt is not None
    assert persisted_receipt.operation_id == receipt_data["operation_id"]
    assert persisted_receipt.provider_payment_id == "provider-payment-1"
    assert persisted_receipt.result == ReceiptResult.COMPLETED
    assert persisted_receipt.message == "Payment completed"
    assert persisted_receipt.provider_occurred_at == receipt_data["provider_occurred_at"]
    assert persisted_receipt.processing_result == ReceiptProcessingResult.APPLIED
    assert persisted_receipt.payload_hash == "a" * 64
    assert persisted_receipt.received_at is not None


@pytest.mark.asyncio
async def test_get_by_operation_and_payload_hash_returns_receipt(
    repository, receipt
):
    result = await repository.get_by_operation_and_payload_hash(
        operation_id=receipt.operation_id,
        payload_hash=receipt.payload_hash,
    )

    assert result is receipt
    assert result.id == receipt.id


@pytest.mark.asyncio
async def test_get_returns_none_for_different_operation(repository, receipt):
    result = await repository.get_by_operation_and_payload_hash(
        operation_id="missing-operation",
        payload_hash=receipt.payload_hash,
    )

    assert result is None


@pytest.mark.asyncio
async def test_get_returns_none_for_different_payload_hash(repository, receipt):
    result = await repository.get_by_operation_and_payload_hash(
        operation_id=receipt.operation_id,
        payload_hash="b" * 64,
    )

    assert result is None
