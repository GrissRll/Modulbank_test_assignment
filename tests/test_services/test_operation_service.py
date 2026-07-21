from decimal import Decimal
from unittest.mock import AsyncMock

import pytest
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.exceptions.units.operation_exception import (
    OperationExistingError,
    OperationNotFoundError,
)
from app.models.operation import Currency, Operation, OperationStatus
from app.repositories.dispatch import PaymentDispatchRepository
from app.repositories.operation_event import OperationEventRepository
from app.repositories.operations import OperationRepository
from app.schemas.operation_schemas import OperationSchema
from app.services.operation_service import OperationService


@pytest.fixture
def db_session():
    return AsyncMock(spec=AsyncSession)


@pytest.fixture
def operation_repository():
    return AsyncMock(spec=OperationRepository)


@pytest.fixture
def dispatch_repository():
    return AsyncMock(spec=PaymentDispatchRepository)


@pytest.fixture
def event_repository():
    return AsyncMock(spec=OperationEventRepository)


@pytest.fixture
def service(
    db_session,
    operation_repository,
    dispatch_repository,
    event_repository,
):
    return OperationService(
        db=db_session,
        operation_repo=operation_repository,
        dispatch_repo=dispatch_repository,
        event_repo=event_repository,
    )


@pytest.fixture
def operation_data():
    return OperationSchema(
        operation_id="operation-1",
        amount=Decimal("100.00"),
        currency=Currency.RUB,
        description="Order payment",
    )


@pytest.mark.asyncio
async def test_register_operation_creates_commits_and_returns_operation(
    service, db_session, operation_repository, operation_data
):
    operation = Operation(
        operation_id=operation_data.operation_id,
        amount=operation_data.amount,
        currency=operation_data.currency,
        description=operation_data.description,
        status=OperationStatus.CREATED,
    )
    operation_repository.get_operation_by_id.return_value = None
    operation_repository.create.return_value = operation

    result = await service.register_operation(operation_data)

    assert result is operation
    operation_repository.get_operation_by_id.assert_awaited_once_with("operation-1")
    operation_repository.create.assert_awaited_once_with(operation_data.model_dump())
    db_session.commit.assert_awaited_once_with()
    db_session.rollback.assert_not_awaited()


@pytest.mark.asyncio
async def test_register_operation_raises_when_operation_already_exists(
    service, db_session, operation_repository, operation_data
):
    operation_repository.get_operation_by_id.return_value = Operation(
        operation_id="operation-1",
        amount=Decimal("100.00"),
        currency=Currency.RUB,
    )

    with pytest.raises(OperationExistingError):
        await service.register_operation(operation_data)

    operation_repository.create.assert_not_awaited()
    db_session.commit.assert_not_awaited()
    db_session.rollback.assert_not_awaited()


@pytest.mark.asyncio
async def test_register_operation_rolls_back_integrity_error(
    service, db_session, operation_repository, operation_data
):
    integrity_error = IntegrityError(
        statement="INSERT INTO operations ...",
        params=None,
        orig=Exception("duplicate key"),
    )
    operation_repository.get_operation_by_id.return_value = None
    operation_repository.create.side_effect = integrity_error

    with pytest.raises(OperationExistingError) as exc_info:
        await service.register_operation(operation_data)

    assert exc_info.value.__cause__ is integrity_error
    db_session.rollback.assert_awaited_once_with()
    db_session.commit.assert_not_awaited()


@pytest.mark.asyncio
async def test_get_operation_by_id_returns_operation(
    service, operation_repository
):
    operation = Operation(
        operation_id="operation-1",
        amount=Decimal("100.00"),
        currency=Currency.RUB,
        status=OperationStatus.CREATED,
    )
    operation_repository.get_operation_by_id.return_value = operation

    result = await service.get_operation_by_id("operation-1")

    assert result is operation
    operation_repository.get_operation_by_id.assert_awaited_once_with("operation-1")


@pytest.mark.asyncio
async def test_get_operation_by_id_raises_when_operation_does_not_exist(
    service, operation_repository
):
    operation_repository.get_operation_by_id.return_value = None

    with pytest.raises(OperationNotFoundError):
        await service.get_operation_by_id("missing-operation")

    operation_repository.get_operation_by_id.assert_awaited_once_with(
        "missing-operation"
    )
