from decimal import Decimal

import pytest
import pytest_asyncio

from app.models.operation import Currency, Operation, OperationStatus
from app.repositories.operations import OperationRepository


@pytest_asyncio.fixture
async def db_session(async_session_maker):
    async with async_session_maker() as session:
        yield session
        await session.rollback()


@pytest.fixture
def repository(db_session):
    return OperationRepository(db=db_session)


@pytest_asyncio.fixture
async def operation(db_session):
    operation = Operation(
        operation_id="operation-existing",
        amount=Decimal("100.00"),
        currency=Currency.RUB,
        description="Order payment",
    )
    db_session.add(operation)
    await db_session.flush()
    return operation


@pytest.mark.asyncio
async def test_get_operation_by_id_returns_operation(repository, operation):
    result = await repository.get_operation_by_id(operation.operation_id)

    assert result is operation
    assert result.operation_id == operation.operation_id


@pytest.mark.asyncio
async def test_get_operation_by_id_returns_none_when_operation_does_not_exist(
    repository,
):
    result = await repository.get_operation_by_id("missing-operation")

    assert result is None


@pytest.mark.asyncio
async def test_create_persists_and_returns_operation(repository, db_session):
    operation_data = {
        "operation_id": "operation-created",
        "amount": Decimal("250.50"),
        "currency": Currency.RUB,
        "description": "Invoice payment",
    }

    result = await repository.create(operation_data)
    operation_id = result.operation_id
    db_session.expunge(result)

    persisted_operation = await db_session.get(Operation, operation_id)

    assert result.operation_id is not None
    assert persisted_operation is not None
    assert persisted_operation.amount == Decimal("250.50")
    assert persisted_operation.currency == Currency.RUB
    assert persisted_operation.description == "Invoice payment"
    assert persisted_operation.status == OperationStatus.CREATED


@pytest.mark.asyncio
async def test_update_status_persists_and_returns_operation(
    repository, db_session, operation
):
    result = await repository.update_status(operation, OperationStatus.PROCESSING)
    await db_session.refresh(operation)

    assert result is operation
    assert operation.status == OperationStatus.PROCESSING


@pytest.mark.asyncio
async def test_update_on_callback_persists_changes(
    repository, db_session, operation
):
    result = await repository.update_on_callback(
        operation=operation,
        new_status=OperationStatus.COMPLETED,
        provider_payment_id="payment-123",
    )
    await db_session.refresh(operation)

    assert result is operation
    assert operation.status == OperationStatus.COMPLETED
    assert operation.provider_payment_id == "payment-123"
