from datetime import datetime, timezone
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
        operation_id="operation-event",
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


@pytest.mark.asyncio
async def test_get_events_returns_only_operation_events_in_order(
    repository, db_session, operation
):
    another_operation = Operation(
        operation_id="operation-another",
        amount=Decimal("200.00"),
        currency=Currency.RUB,
    )
    db_session.add(another_operation)
    await db_session.flush()
    occurred_at = datetime(2030, 1, 1, 12, 30, tzinfo=timezone.utc)

    await repository.create(
        {
            "operation_id": operation.operation_id,
            "event_id": 2,
            "event_type": OperationStatus.PROCESSING,
            "from_status": OperationStatus.CREATED,
            "to_status": OperationStatus.PROCESSING,
            "message": "Operation processing started",
            "occurred_at": occurred_at,
        }
    )
    await repository.create(
        {
            "operation_id": operation.operation_id,
            "event_id": 1,
            "event_type": OperationStatus.CREATED,
            "from_status": None,
            "to_status": OperationStatus.CREATED,
            "message": "Operation created",
            "occurred_at": occurred_at,
        }
    )
    await repository.create(
        {
            "operation_id": another_operation.operation_id,
            "event_id": 1,
            "event_type": OperationStatus.CREATED,
            "from_status": None,
            "to_status": OperationStatus.CREATED,
            "message": "Another operation created",
            "occurred_at": occurred_at,
        }
    )

    result = await repository.get_events(operation.operation_id)

    assert [event.event_id for event in result] == [1, 2]
    assert all(event.operation_id == operation.operation_id for event in result)


@pytest.mark.asyncio
async def test_get_events_returns_empty_sequence(repository):
    result = await repository.get_events("missing-operation")

    assert list(result) == []


@pytest.mark.asyncio
async def test_get_next_event_id_returns_one_when_operation_has_no_events(
    repository, operation
):
    result = await repository.get_next_event_id(operation.operation_id)

    assert result == 1


@pytest.mark.asyncio
async def test_get_next_event_id_returns_next_id_only_for_requested_operation(
    repository, db_session, operation
):
    another_operation = Operation(
        operation_id="operation-with-more-events",
        amount=Decimal("200.00"),
        currency=Currency.RUB,
    )
    db_session.add(another_operation)
    await db_session.flush()

    for operation_id, event_id in (
        (operation.operation_id, 1),
        (operation.operation_id, 3),
        (another_operation.operation_id, 10),
    ):
        await repository.create(
            {
                "operation_id": operation_id,
                "event_id": event_id,
                "event_type": OperationStatus.CREATED,
                "from_status": None,
                "to_status": OperationStatus.CREATED,
                "message": "Operation created",
            }
        )

    result = await repository.get_next_event_id(operation.operation_id)

    assert result == 4
