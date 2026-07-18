import pytest
from decimal import Decimal
from datetime import datetime, timedelta
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError

from app.models.operation import Currency
from app.models.operation import Operation as OperationModel
from app.models.dispatch import PaymentDispatch as DispatchModel


@pytest.mark.asyncio
async def test_create_payment_dispatch(async_session_maker):
    async with async_session_maker() as session:
        async with session.begin():
            operation = OperationModel(
                amount=Decimal("1111.00"),
                currency=Currency.RUB,
                description="Оплата заказа",
            )

            session.add(operation)
            await session.flush()
            request_payload = {
                "operation_id": operation.operation_id,
                "amount": str(operation.amount),
                "currency": operation.currency.value,
                "description": operation.description,
                "status": operation.status.value,
            }

            dispatch = DispatchModel(
                operation_id=operation.operation_id,
                idempotency_key=operation.operation_id,
                request_payload=request_payload,
                next_attempt_at=datetime.now() + timedelta(seconds=30),
            )
            session.add(dispatch)
    operation_id = operation.operation_id

    async with async_session_maker() as session:

        operation_db = await session.get(OperationModel, operation_id)
        dispatch_db = await session.scalar(
            select(DispatchModel).where(
                DispatchModel.idempotency_key == operation_db.operation_id
            )
        )
        assert dispatch_db is not None
        assert operation_db is not None
        assert dispatch_db is not None
        assert dispatch_db.operation_id == operation_id
        assert dispatch_db.idempotency_key == operation_id
        assert dispatch_db.request_payload == {
            "operation_id": operation_id,
            "amount": "1111.00",
            "currency": Currency.RUB.value,
            "description": "Оплата заказа",
            "status": operation_db.status.value,
        }
        assert dispatch_db.next_attempt_at is not None


@pytest.mark.asyncio
async def test_payment_dispatch_defaults(async_session_maker):
    async with async_session_maker() as session:
        operation = OperationModel(
            amount=Decimal("100.00"),
            currency=Currency.RUB,
        )
        session.add(operation)
        await session.flush()

        dispatch = DispatchModel(
            operation_id=operation.operation_id,
            idempotency_key="dispatch-defaults",
            request_payload={"operation_id": operation.operation_id},
        )
        session.add(dispatch)
        await session.flush()

        assert dispatch.id is not None
        assert dispatch.attempt_count == 0
        assert dispatch.next_attempt_at is not None
        assert dispatch.created_at is not None
        assert dispatch.last_error is None
        assert dispatch.updated_at is None


@pytest.mark.asyncio
async def test_payment_dispatch_requires_existing_operation(async_session_maker):
    async with async_session_maker() as session:
        dispatch = DispatchModel(
            operation_id="operation-missing",
            idempotency_key="missing-operation",
            request_payload={"operation_id": "operation-missing"},
        )
        session.add(dispatch)

        with pytest.raises(IntegrityError):
            await session.flush()


@pytest.mark.asyncio
async def test_payment_dispatch_operation_id_is_unique(async_session_maker):
    async with async_session_maker() as session:
        operation = OperationModel(
            amount=Decimal("100.00"),
            currency=Currency.RUB,
        )
        session.add(operation)
        await session.flush()

        first_dispatch = DispatchModel(
            operation_id=operation.operation_id,
            idempotency_key="first-dispatch",
            request_payload={"operation_id": operation.operation_id},
        )
        session.add(first_dispatch)
        await session.flush()

        duplicate_dispatch = DispatchModel(
            operation_id=operation.operation_id,
            idempotency_key="second-dispatch",
            request_payload={"operation_id": operation.operation_id},
        )
        session.add(duplicate_dispatch)

        with pytest.raises(IntegrityError):
            await session.flush()


@pytest.mark.asyncio
async def test_payment_dispatch_idempotency_key_is_unique(async_session_maker):
    async with async_session_maker() as session:
        first_operation = OperationModel(
            amount=Decimal("100.00"),
            currency=Currency.RUB,
        )
        second_operation = OperationModel(
            amount=Decimal("200.00"),
            currency=Currency.RUB,
        )
        session.add_all([first_operation, second_operation])
        await session.flush()

        first_dispatch = DispatchModel(
            operation_id=first_operation.operation_id,
            idempotency_key="duplicate-key",
            request_payload={"operation_id": first_operation.operation_id},
        )
        session.add(first_dispatch)
        await session.flush()

        duplicate_dispatch = DispatchModel(
            operation_id=second_operation.operation_id,
            idempotency_key="duplicate-key",
            request_payload={"operation_id": second_operation.operation_id},
        )
        session.add(duplicate_dispatch)

        with pytest.raises(IntegrityError):
            await session.flush()


@pytest.mark.asyncio
async def test_payment_dispatch_payload_is_required(async_session_maker):
    async with async_session_maker() as session:
        operation = OperationModel(
            amount=Decimal("100.00"),
            currency=Currency.RUB,
        )
        session.add(operation)
        await session.flush()

        dispatch = DispatchModel(
            operation_id=operation.operation_id,
            idempotency_key="missing-payload",
        )
        session.add(dispatch)

        with pytest.raises(IntegrityError):
            await session.flush()


@pytest.mark.asyncio
async def test_payment_dispatch_is_deleted_with_operation(async_session_maker):
    async with async_session_maker() as session:
        operation = OperationModel(
            amount=Decimal("100.00"),
            currency=Currency.RUB,
        )
        session.add(operation)
        await session.flush()

        dispatch = DispatchModel(
            operation_id=operation.operation_id,
            idempotency_key="cascade-delete",
            request_payload={"operation_id": operation.operation_id},
        )
        session.add(dispatch)
        await session.flush()
        dispatch_id = dispatch.id
        session.expunge(dispatch)

        await session.delete(operation)
        await session.flush()

        deleted_dispatch = await session.get(DispatchModel, dispatch_id)
        assert deleted_dispatch is None
