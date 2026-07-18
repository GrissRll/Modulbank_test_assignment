import pytest
from httpx import ASGITransport, AsyncClient


@pytest.mark.asyncio
async def test_health200(client):
    response = await client.get("/health/live")
    assert response.status_code == 200
    assert response.json()["app_status"] == "healthy"


@pytest.mark.asyncio
async def test_health404(client):
    response = await client.get("/health/evil")
    assert response.status_code == 404


@pytest.mark.asyncio
async def test_ready200(client):
    response = await client.get("/health/ready")
    assert response.status_code == 200
    assert response.json()["app_status"] == "ready"
    assert response.json()["database"] == "available"


@pytest.mark.asyncio
async def test_ready404(client):
    response = await client.get("/health/ready12")
    assert response.status_code == 404


@pytest.mark.asyncio
async def test_ready503_db_unavailable(broken_db):
    app, broken_session = broken_db

    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as client:
        response = await client.get("/health/ready")
    assert response.status_code == 503
    assert response.json()["detail"] == {"app_status": "not ready", "database": "unavailable"}
