"""scores API のテスト"""
import pytest
from httpx import AsyncClient, ASGITransport
from app.main import app


@pytest.mark.asyncio
async def test_list_scores_empty():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        response = await client.get("/api/v1/scores")
    assert response.status_code == 200
    assert isinstance(response.json(), list)


@pytest.mark.asyncio
async def test_get_score_not_found():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        response = await client.get("/api/v1/scores/9999.T")
    assert response.status_code == 404


@pytest.mark.asyncio
async def test_get_axes_empty():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        response = await client.get("/api/v1/scores/9999.T/axes")
    assert response.status_code == 200
    data = response.json()
    assert data["symbol"] == "9999.T"
    assert data["axes"] == []


@pytest.mark.asyncio
async def test_batch_status():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        response = await client.get("/api/v1/batch/scoring/status")
    assert response.status_code == 200
    data = response.json()
    assert "status" in data
    assert "processed" in data
