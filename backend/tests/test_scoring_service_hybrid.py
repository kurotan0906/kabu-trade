"""scoring_service の hybrid / tv / yfinance モード切替テスト

ネットワークに出ないよう、yfinance_client と tradingview_ta_client を monkeypatch で差し替える。
"""
import pandas as pd
import pytest

from app.services import scoring_service


def _fake_history() -> pd.DataFrame:
    # technical.score_ma/rsi/macd が動くように十分な長さのダミー
    import numpy as np
    n = 120
    prices = pd.Series([1000 + i * 2 for i in range(n)], dtype=float)
    return pd.DataFrame({
        "Close": prices,
        "Open": prices,
        "High": prices + 5,
        "Low": prices - 5,
        "Volume": [100000] * n,
    })


@pytest.fixture
def fake_yf(monkeypatch):
    calls = {"count": 0}

    def _fake(symbol):
        calls["count"] += 1
        return {
            "symbol": symbol,
            "history": _fake_history(),
            "info": {
                "trailingPE": 25.0,  # TV 側で 12 に上書きされるはず (hybrid)
                "priceToBook": 1.8,
                "returnOnEquity": 0.05,
                "dividendYield": 0.015,
                "revenueGrowth": 0.08,
            },
        }
    monkeypatch.setattr("app.external.yfinance_client.fetch_stock_data", _fake)
    return calls


@pytest.fixture
def fake_tv(monkeypatch):
    calls = {"count": 0}

    def _fake(symbol):
        calls["count"] += 1
        return {
            "symbol": symbol,
            "info": {
                "trailingPE": 12.0,
                "priceToBook": None,  # None は base を上書きしない
                "returnOnEquity": 0.18,
                "dividendYield": 0.025,
            },
            "recommendation": "BUY",
            "tv_indicators": {},
        }
    monkeypatch.setattr("app.external.tradingview_ta_client.fetch_stock_data_tv", _fake)
    return calls


@pytest.fixture(autouse=True)
def _no_kurotenko(monkeypatch):
    # 黒転評価は yfinance 実ネットワークを叩くので、テスト中は None を返す
    monkeypatch.setattr(
        "app.analyzer.kurotenko_screener.evaluate_candidate",
        lambda symbol: None,
    )


class TestFetchMergedData:
    def test_hybrid_merges_tv_over_yfinance(self, fake_yf, fake_tv):
        data = scoring_service._fetch_merged_data("7203.T", "hybrid")
        assert data is not None
        assert data["info"]["trailingPE"] == 12.0  # TV 上書き
        assert data["info"]["priceToBook"] == 1.8  # base 保持
        assert data["info"]["returnOnEquity"] == 0.18
        assert data["info"]["revenueGrowth"] == 0.08  # TV にない値は base 由来
        assert data["history"] is not None
        assert data["recommendation"] == "BUY"
        assert fake_yf["count"] == 1 and fake_tv["count"] == 1

    def test_yfinance_only(self, fake_yf, fake_tv):
        data = scoring_service._fetch_merged_data("7203.T", "yfinance")
        assert data["info"]["trailingPE"] == 25.0  # 上書きされない
        assert data["recommendation"] is None
        assert fake_tv["count"] == 0

    def test_tv_only(self, fake_yf, fake_tv):
        data = scoring_service._fetch_merged_data("7203.T", "tv")
        assert data["info"]["trailingPE"] == 12.0
        assert data["history"] is None
        assert data["recommendation"] == "BUY"
        assert fake_yf["count"] == 0


class TestScoreSymbol:
    def test_hybrid_scoring_produces_full_result(self, fake_yf, fake_tv):
        result = scoring_service._score_symbol("7203.T", "トヨタ", "輸送用機器", "hybrid")
        assert result is not None
        assert result["symbol"] == "7203.T"
        assert result["name"] == "トヨタ"
        assert "total_score" in result
        assert result["per"] == 12.0  # TV 値が反映

    def test_tv_only_scoring_uses_neutral_technical(self, fake_yf, fake_tv):
        result = scoring_service._score_symbol("7203.T", "トヨタ", "輸送用機器", "tv")
        assert result is not None
        assert result["technical_score"] == 24.0  # 中立フォールバック

    def test_returns_none_when_all_sources_fail(self, monkeypatch):
        monkeypatch.setattr("app.external.yfinance_client.fetch_stock_data", lambda s: None)
        monkeypatch.setattr("app.external.tradingview_ta_client.fetch_stock_data_tv", lambda s: None)
        assert scoring_service._score_symbol("X.T", "x", "y", "hybrid") is None
