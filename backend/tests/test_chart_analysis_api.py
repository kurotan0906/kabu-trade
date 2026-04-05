"""ChartAnalysis API tests"""

import pytest
from app.schemas.chart_analysis import ChartAnalysisCreate, ChartAnalysisResponse
from datetime import datetime


def test_chart_analysis_create_requires_symbol():
    with pytest.raises(Exception):
        ChartAnalysisCreate(
            timeframe="1D",
            trend="bullish",
            summary="テストサマリー",
            recommendation="buy",
        )


def test_chart_analysis_create_valid():
    data = ChartAnalysisCreate(
        symbol="7203",
        timeframe="1D",
        trend="bullish",
        signals={"rsi": "oversold_recovery", "ma": "golden_cross_approaching"},
        summary="日足チャートでは上昇トレンドが継続中",
        recommendation="buy",
    )
    assert data.symbol == "7203"
    assert data.timeframe == "1D"
    assert data.trend == "bullish"
    assert data.recommendation == "buy"
    assert data.signals["rsi"] == "oversold_recovery"
    assert data.screenshot_path is None


def test_chart_analysis_create_optional_fields():
    data = ChartAnalysisCreate(
        symbol="9984",
        timeframe="1W",
        trend="neutral",
        summary="週足チャートではもみ合い継続",
        recommendation="hold",
    )
    assert data.signals is None
    assert data.screenshot_path is None


# API エンドポイントテスト
import pytest
from httpx import AsyncClient, ASGITransport
from app.main import app


@pytest.mark.asyncio
async def test_create_chart_analysis():
    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as client:
        response = await client.post(
            "/api/v1/chart-analysis",
            json={
                "symbol": "7203",
                "timeframe": "1D",
                "trend": "bullish",
                "signals": {"rsi": "oversold_recovery"},
                "summary": "日足チャートでは上昇トレンドが継続中",
                "recommendation": "buy",
            },
        )
    assert response.status_code == 201
    data = response.json()
    assert data["symbol"] == "7203"
    assert data["recommendation"] == "buy"
    assert "id" in data
    assert "created_at" in data


@pytest.mark.asyncio
async def test_get_latest_not_found():
    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as client:
        response = await client.get("/api/v1/chart-analysis/9999/latest")
    assert response.status_code == 404
