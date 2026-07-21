from datetime import datetime, timezone
from decimal import Decimal

import pytest
import pytest_asyncio

from app.models.dispatch import PaymentDispatch
from app.models.operation import Currency, Operation
from app.repositories.dispatch import PaymentDispatchRepository


@pytest_asyncio.fixture
async def db_session(async_session_maker):
    async with async_session_maker() as session:
        yield session
        await session.rollback()


@pytest.fixture
def repository(db_session):
    return PaymentDispatchRepository(db=db_session)


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


@pytest_asyncio.fixture
async def dispatch(repository, operation):
    return await repository.create(
        {
            "operation_id": operation.operation_id,
            "idempotency_key": "dispatch-1",
            "request_payload": {"operation_id": operation.operation_id},
            "next_attempt_at": datetime.now(timezone.utc),
        }
    )


@pytest.mark.asyncio
async def test_create_persists_and_returns_dispatch(
    repository, db_session, operation
):
    result = await repository.create(
        {
            "operation_id": operation.operation_id,
            "idempotency_key": "dispatch-create",
            "request_payload": {
                "operation_id": operation.operation_id,
                "amount": "100.00",
            },
        }
    )
    dispatch_id = result.id
    db_session.expunge(result)

    persisted_dispatch = await db_session.get(PaymentDispatch, dispatch_id)

    assert persisted_dispatch is not None
    assert persisted_dispatch.operation_id == operation.operation_id
    assert persisted_dispatch.idempotency_key == "dispatch-create"
    assert persisted_dispatch.request_payload == {
        "operation_id": operation.operation_id,
        "amount": "100.00",
    }
    assert persisted_dispatch.attempt_count == 0


@pytest.mark.asyncio
async def test_get_by_operation_id_returns_dispatch(repository, dispatch):
    result = await repository.get_by_operation_id(dispatch.operation_id)

    assert result is dispatch
    assert result.id == dispatch.id


@pytest.mark.asyncio
async def test_get_by_operation_id_returns_none_when_dispatch_does_not_exist(
    repository,
):
    result = await repository.get_by_operation_id("missing-operation")

    assert result is None


@pytest.mark.asyncio
async def test_update_attempt_count_persists_retry_data(
    repository, db_session, dispatch
):
    next_attempt_at = datetime(2030, 1, 1, 12, 30, tzinfo=timezone.utc)

    result = await repository.update_attempt_count(
        dispatch_payment=dispatch,
        time=next_attempt_at,
        error_description="Provider is unavailable",
    )
    await db_session.refresh(dispatch)

    assert result is dispatch
    assert dispatch.attempt_count == 1
    assert dispatch.next_attempt_at == next_attempt_at
    assert dispatch.last_error == "Provider is unavailable"
