import pytest
from decimal import Decimal

from sqlalchemy.exc import IntegrityError, SAWarning

from app.models.operation import Currency, Operation as OperationModel, OperationStatus


@pytest.mark.asyncio
async def test_create_operation_success(async_session_maker):
    async with async_session_maker() as session:
        operation = OperationModel(
            operation_id="operation-1",
            amount=Decimal("1111.00"),
            currency=Currency.RUB,
            description="Оплата заказа"
        )

        session.add(operation)
        await session.flush()
        assert operation.operation_id == "operation-1"
        assert operation.amount == Decimal("1111.00")
        assert operation.currency == "RUB"
        assert operation.description == "Оплата заказа"
        assert operation.status == OperationStatus.CREATED
        assert operation.created_at is not None


@pytest.mark.asyncio
async def test_create_operation_without_description(async_session_maker):
    async with async_session_maker() as session:
        operation = OperationModel(
            operation_id="operation-1",
            amount=Decimal("100.00"),
            currency=Currency.RUB,
        )

        session.add(operation)
        await session.flush()

        assert operation.description is None


@pytest.mark.asyncio
async def test_operation_id_is_required(async_session_maker):
    async with async_session_maker() as session:
        operation = OperationModel(
            amount=Decimal("100.00"),
            currency=Currency.RUB,
        )
        session.add(operation)

        with pytest.warns(SAWarning):
            with pytest.raises(IntegrityError):
                await session.flush()


@pytest.mark.asyncio
async def test_operation_amount_is_required(async_session_maker):
    async with async_session_maker() as session:
        operation = OperationModel(
            operation_id="operation-1",
            amount=None,
            currency=Currency.RUB,
        )
        session.add(operation)

        with pytest.raises(IntegrityError):
            await session.flush()


@pytest.mark.asyncio
async def test_operation_currency_is_required(async_session_maker):
    async with async_session_maker() as session:
        operation = OperationModel(
            operation_id="operation-1",
            amount=Decimal("100.00"),
            currency=None,
        )
        session.add(operation)

        with pytest.raises(IntegrityError):
            await session.flush()


@pytest.mark.asyncio
@pytest.mark.parametrize("amount", [Decimal("0.00"), Decimal("-0.01")])
async def test_operation_amount_must_be_positive(async_session_maker, amount):
    async with async_session_maker() as session:
        operation = OperationModel(
            operation_id="operation-1",
            amount=amount,
            currency=Currency.RUB,
        )
        session.add(operation)

        with pytest.raises(IntegrityError):
            await session.flush()


@pytest.mark.asyncio
async def test_operation_id_is_unique(async_session_maker):
    async with async_session_maker() as session:
        first_operation = OperationModel(
            operation_id="operation-custom",
            amount=Decimal("100.00"),
            currency=Currency.RUB,
        )
        session.add(first_operation)
        await session.flush()
        session.expunge(first_operation)

        duplicate_operation = OperationModel(
            operation_id="operation-custom",
            amount=Decimal("200.00"),
            currency=Currency.RUB,
        )
        session.add(duplicate_operation)

        with pytest.raises(IntegrityError):
            await session.flush()


@pytest.mark.asyncio
async def test_operation_has_default_status_and_created_at(async_session_maker):
    async with async_session_maker() as session:
        operation = OperationModel(
            operation_id="operation-1",
            amount=Decimal("100.00"),
            currency=Currency.RUB,
        )

        session.add(operation)
        await session.flush()

        assert operation.status == OperationStatus.CREATED
        assert operation.created_at is not None
