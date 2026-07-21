from decimal import Decimal

import pytest
import pytest_asyncio

from app.models.operation import Currency, Operation, OperationStatus
from app.models.operation_event import OperationEvent
from app.repositories.operation_event import OperationEventRepository


@pytest_asyncio.fixture
async def db_session(async_session_maker):
    async with async_session_maker() as session:
        yield session
        await session.rollback()


@pytest.fixture
def repository(db_session):
    return OperationEventRepository(db=db_session)


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


@pytest.mark.asyncio
async def test_create_persists_and_returns_initial_event(
    repository, db_session, operation
):
    result = await repository.create(
        {
            "operation_id": operation.operation_id,
            "event_id": 1,
            "event_type": OperationStatus.CREATED,
            "from_status": None,
            "to_status": OperationStatus.CREATED,
            "message": "Operation created",
        }
    )
    event_db_id = result.id
    db_session.expunge(result)

    persisted_event = await db_session.get(OperationEvent, event_db_id)

    assert persisted_event is not None
    assert persisted_event.operation_id == operation.operation_id
    assert persisted_event.event_id == 1
    assert persisted_event.event_type == OperationStatus.CREATED
    assert persisted_event.from_status is None
    assert persisted_event.to_status == OperationStatus.CREATED
    assert persisted_event.message == "Operation created"
    assert persisted_event.occurred_at is not None


@pytest.mark.asyncio
async def test_create_persists_status_transition(repository, db_session, operation):
    result = await repository.create(
        {
            "operation_id": operation.operation_id,
            "event_id": 2,
            "event_type": OperationStatus.PROCESSING,
            "from_status": OperationStatus.CREATED,
            "to_status": OperationStatus.PROCESSING,
            "message": "Operation processing started",
        }
    )
    event_db_id = result.id
    db_session.expunge(result)

    persisted_event = await db_session.get(OperationEvent, event_db_id)

    assert result.id == event_db_id
    assert persisted_event is not None
    assert persisted_event.event_type == OperationStatus.PROCESSING
    assert persisted_event.from_status == OperationStatus.CREATED
    assert persisted_event.to_status == OperationStatus.PROCESSING
    assert persisted_event.message == "Operation processing started"
