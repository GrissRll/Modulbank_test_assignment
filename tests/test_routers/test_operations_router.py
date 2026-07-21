from datetime import datetime, timezone
from decimal import Decimal

import pytest

from app.models.operation import Currency, Operation, OperationStatus
from app.models.operation_event import OperationEvent


def operation_payload(operation_id: str = "operation-1") -> dict:
    return {
        "operation_id": operation_id,
        "amount": "100.00",
        "currency": "RUB",
        "description": "Order payment",
    }


@pytest.mark.asyncio
async def test_create_operation_returns_201_and_persists_operation(
    client, async_session_maker
):
    response = await client.post("/operations/", json=operation_payload())

    assert response.status_code == 201
    assert response.json() == {
        "operation_id": "operation-1",
        "amount": "100.00",
        "currency": "RUB",
        "description": "Order payment",
        "status": "CREATED",
        "provider_payment_id": None,
    }

    async with async_session_maker() as session:
        operation = await session.get(Operation, "operation-1")

    assert operation is not None
    assert operation.amount == Decimal("100.00")
    assert operation.currency == Currency.RUB
    assert operation.status == OperationStatus.CREATED


@pytest.mark.asyncio
async def test_create_operation_returns_409_for_existing_operation(client):
    payload = operation_payload()
    first_response = await client.post("/operations/", json=payload)

    duplicate_response = await client.post("/operations/", json=payload)

    assert first_response.status_code == 201
    assert duplicate_response.status_code == 409
    assert duplicate_response.json() == {"detail": "Operation already exists."}


@pytest.mark.asyncio
@pytest.mark.parametrize("amount", ["0", "-0.01"])
async def test_create_operation_rejects_non_positive_amount(client, amount):
    payload = operation_payload()
    payload["amount"] = amount

    response = await client.post("/operations/", json=payload)

    assert response.status_code == 422


@pytest.mark.asyncio
async def test_create_operation_rejects_too_long_description(client):
    payload = operation_payload()
    payload["description"] = "a" * 501

    response = await client.post("/operations/", json=payload)

    assert response.status_code == 422


@pytest.mark.asyncio
async def test_get_operation_returns_200_and_current_state(client):
    create_response = await client.post(
        "/operations/", json=operation_payload("operation-get")
    )

    response = await client.get("/operations/operation-get")

    assert create_response.status_code == 201
    assert response.status_code == 200
    assert response.json() == {
        "operation_id": "operation-get",
        "amount": "100.00",
        "currency": "RUB",
        "description": "Order payment",
        "status": "CREATED",
        "provider_payment_id": None,
    }


@pytest.mark.asyncio
async def test_get_operation_returns_404_when_operation_does_not_exist(client):
    response = await client.get("/operations/missing-operation")

    assert response.status_code == 404
    assert response.json() == {"detail": "Operation not found."}


@pytest.mark.asyncio
async def test_get_operation_events_returns_200_and_ordered_events(
    client, async_session_maker
):
    create_response = await client.post(
        "/operations/", json=operation_payload("operation-events")
    )
    occurred_at = datetime(2030, 1, 1, 12, 30, tzinfo=timezone.utc)
    async with async_session_maker() as session:
        session.add_all(
            [
                OperationEvent(
                    operation_id="operation-events",
                    event_id=2,
                    event_type=OperationStatus.PROCESSING,
                    from_status=OperationStatus.CREATED,
                    to_status=OperationStatus.PROCESSING,
                    message="Operation processing started",
                    occurred_at=occurred_at,
                ),
                OperationEvent(
                    operation_id="operation-events",
                    event_id=1,
                    event_type=OperationStatus.CREATED,
                    from_status=None,
                    to_status=OperationStatus.CREATED,
                    message="Operation created",
                    occurred_at=occurred_at,
                ),
            ]
        )
        await session.commit()

    response = await client.get("/operations/operation-events/events")

    assert create_response.status_code == 201
    assert response.status_code == 200
    assert response.json() == [
        {
            "operation_id": "operation-events",
            "event_id": 1,
            "event_type": "CREATED",
            "from_status": None,
            "to_status": "CREATED",
            "message": "Operation created",
            "occurred_at": "2030-01-01T12:30:00Z",
        },
        {
            "operation_id": "operation-events",
            "event_id": 2,
            "event_type": "PROCESSING",
            "from_status": "CREATED",
            "to_status": "PROCESSING",
            "message": "Operation processing started",
            "occurred_at": "2030-01-01T12:30:00Z",
        },
    ]


@pytest.mark.asyncio
async def test_get_operation_events_returns_empty_list(client):
    create_response = await client.post(
        "/operations/", json=operation_payload("operation-without-events")
    )

    response = await client.get("/operations/operation-without-events/events")

    assert create_response.status_code == 201
    assert response.status_code == 200
    assert response.json() == []


@pytest.mark.asyncio
async def test_get_operation_events_returns_404_for_missing_operation(client):
    response = await client.get("/operations/missing-operation/events")

    assert response.status_code == 404
    assert response.json() == {"detail": "Operation not found."}
