from decimal import Decimal

import pytest
from sqlalchemy.exc import IntegrityError

from app.models.operation import Currency, Operation as OperationModel, OperationStatus
from app.models.operation_event import OperationEvent as OperationEventModel


def create_operation(amount: str = "100.00") -> OperationModel:
    return OperationModel(
        amount=Decimal(amount),
        currency=Currency.RUB,
    )


def create_event(
    operation_id: str,
    event_id: int = 1,
    message: str = "Operation created",
) -> OperationEventModel:
    return OperationEventModel(
        operation_id=operation_id,
        event_id=event_id,
        event_type=OperationStatus.CREATED,
        from_status=None,
        to_status=OperationStatus.CREATED,
        message=message,
    )


@pytest.mark.asyncio
async def test_create_operation_event_success(async_session_maker):
    async with async_session_maker() as session:
        operation = create_operation()
        session.add(operation)
        await session.flush()

        event = create_event(operation.operation_id)
        session.add(event)
        await session.flush()

        assert event.id is not None
        assert event.operation_id == operation.operation_id
        assert event.event_id == 1
        assert event.event_type == OperationStatus.CREATED
        assert event.from_status is None
        assert event.to_status == OperationStatus.CREATED
        assert event.message == "Operation created"
        assert event.occurred_at is not None


@pytest.mark.asyncio
async def test_operation_event_allows_optional_statuses(async_session_maker):
    async with async_session_maker() as session:
        operation = create_operation()
        session.add(operation)
        await session.flush()

        event = OperationEventModel(
            operation_id=operation.operation_id,
            event_id=1,
            event_type=OperationStatus.CREATED,
            from_status=None,
            to_status=None,
            message="Operation event without transition",
        )
        session.add(event)
        await session.flush()

        assert event.from_status is None
        assert event.to_status is None


@pytest.mark.asyncio
async def test_operation_event_requires_existing_operation(async_session_maker):
    async with async_session_maker() as session:
        event = create_event("operation-missing")
        session.add(event)

        with pytest.raises(IntegrityError):
            await session.flush()


@pytest.mark.asyncio
async def test_operation_event_id_is_unique_within_operation(async_session_maker):
    async with async_session_maker() as session:
        operation = create_operation()
        session.add(operation)
        await session.flush()

        first_event = create_event(operation.operation_id, event_id=1)
        session.add(first_event)
        await session.flush()

        duplicate_event = create_event(
            operation.operation_id,
            event_id=1,
            message="Duplicate event",
        )
        session.add(duplicate_event)

        with pytest.raises(IntegrityError):
            await session.flush()


@pytest.mark.asyncio
async def test_same_event_id_is_allowed_for_different_operations(
    async_session_maker,
):
    async with async_session_maker() as session:
        first_operation = create_operation("100.00")
        second_operation = create_operation("200.00")
        session.add_all([first_operation, second_operation])
        await session.flush()

        first_event = create_event(first_operation.operation_id, event_id=1)
        second_event = create_event(second_operation.operation_id, event_id=1)
        session.add_all([first_event, second_event])
        await session.flush()

        assert first_event.id is not None
        assert second_event.id is not None


@pytest.mark.asyncio
@pytest.mark.parametrize("event_id", [0, -1])
async def test_operation_event_id_must_be_positive(
    async_session_maker,
    event_id,
):
    async with async_session_maker() as session:
        operation = create_operation()
        session.add(operation)
        await session.flush()

        event = create_event(operation.operation_id, event_id=event_id)
        session.add(event)

        with pytest.raises(IntegrityError):
            await session.flush()


@pytest.mark.asyncio
async def test_operation_event_type_is_required(async_session_maker):
    async with async_session_maker() as session:
        operation = create_operation()
        session.add(operation)
        await session.flush()

        event = OperationEventModel(
            operation_id=operation.operation_id,
            event_id=1,
            event_type=None,
            message="Missing event type",
        )
        session.add(event)

        with pytest.raises(IntegrityError):
            await session.flush()


@pytest.mark.asyncio
async def test_operation_event_message_is_required(async_session_maker):
    async with async_session_maker() as session:
        operation = create_operation()
        session.add(operation)
        await session.flush()

        event = OperationEventModel(
            operation_id=operation.operation_id,
            event_id=1,
            event_type=OperationStatus.CREATED,
            message=None,
        )
        session.add(event)

        with pytest.raises(IntegrityError):
            await session.flush()


@pytest.mark.asyncio
async def test_operation_events_are_deleted_with_operation(async_session_maker):
    async with async_session_maker() as session:
        operation = create_operation()
        session.add(operation)
        await session.flush()

        event = create_event(operation.operation_id)
        session.add(event)
        await session.flush()
        event_id = event.id
        session.expunge(event)

        await session.delete(operation)
        await session.flush()

        deleted_event = await session.get(OperationEventModel, event_id)
        assert deleted_event is None
