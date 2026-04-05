"""TradingView シグナル API のテスト"""
import pytest
from httpx import AsyncClient, ASGITransport
from app.main import app


@pytest.mark.asyncio
async def test_list_signals_empty():
    """シグナルなし時は空リストを返す"""
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        response = await client.get("/api/v1/tradingview-signals")
    assert response.status_code == 200
    assert isinstance(response.json(), list)


@pytest.mark.asyncio
async def test_get_signal_not_found():
    """存在しない銘柄は 404"""
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        response = await client.get("/api/v1/tradingview-signals/9999")
    assert response.status_code == 404


@pytest.mark.asyncio
async def test_create_and_get_signal():
    """POST で保存した後 GET で取得できる"""
    payload = {
        "recommendation": "BUY",
        "score": 75.0,
        "buy_count": 12,
        "sell_count": 4,
        "neutral_count": 6,
        "ma_recommendation": "BUY",
        "osc_recommendation": "NEUTRAL",
        "details": {"RSI": 58.5},
    }
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        post_res = await client.post("/api/v1/tradingview-signals/7203", json=payload)
        assert post_res.status_code == 201
        created = post_res.json()
        assert created["symbol"] == "7203"
        assert created["recommendation"] == "BUY"

        get_res = await client.get("/api/v1/tradingview-signals/7203")
        assert get_res.status_code == 200
        fetched = get_res.json()
        assert fetched["symbol"] == "7203"
        assert fetched["score"] == 75.0


@pytest.mark.asyncio
async def test_list_signals_returns_latest_per_symbol():
    """同一銘柄を2回 POST → GET一覧は最新1件のみ"""
    payload_old = {"recommendation": "SELL", "score": 25.0}
    payload_new = {"recommendation": "STRONG_BUY", "score": 100.0}
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        await client.post("/api/v1/tradingview-signals/1234", json=payload_old)
        await client.post("/api/v1/tradingview-signals/1234", json=payload_new)
        list_res = await client.get("/api/v1/tradingview-signals")
    signals = list_res.json()
    matching = [s for s in signals if s["symbol"] == "1234"]
    assert len(matching) == 1
    assert matching[0]["recommendation"] == "STRONG_BUY"
