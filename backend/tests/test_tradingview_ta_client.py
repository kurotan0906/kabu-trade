"""tradingview_ta_client のユニットテスト

TA_Handler は monkeypatch で差し替え、実ネットワークを叩かない。
"""
import pytest

from app.external import tradingview_ta_client as tvc


class _FakeAnalysis:
    def __init__(self, indicators, summary):
        self.indicators = indicators
        self.summary = summary


class _FakeHandler:
    """tradingview_ta.TA_Handler を差し替えるためのフェイク"""
    captured = {}
    indicators_to_return = {}
    summary_to_return = {}
    raise_on_call = False

    def __init__(self, symbol, exchange, screener, interval, timeout=10):
        _FakeHandler.captured = {
            "symbol": symbol,
            "exchange": exchange,
            "screener": screener,
            "interval": interval,
        }

    def get_analysis(self):
        if _FakeHandler.raise_on_call:
            raise RuntimeError("boom")
        return _FakeAnalysis(_FakeHandler.indicators_to_return, _FakeHandler.summary_to_return)


@pytest.fixture(autouse=True)
def _patch_ta_handler(monkeypatch):
    import tradingview_ta
    monkeypatch.setattr(tradingview_ta, "TA_Handler", _FakeHandler)
    _FakeHandler.indicators_to_return = {}
    _FakeHandler.summary_to_return = {}
    _FakeHandler.raise_on_call = False
    yield


class TestSymbolToTv:
    def test_jpx_code(self):
        assert tvc.symbol_to_tv("7203.T") == ("TSE", "7203")

    def test_bare_code(self):
        assert tvc.symbol_to_tv("9984") == ("TSE", "9984")

    def test_invalid(self):
        assert tvc.symbol_to_tv("") is None
        assert tvc.symbol_to_tv(".T") is None


class TestFetchStockDataTv:
    def test_maps_indicators_to_yfinance_keys(self):
        _FakeHandler.indicators_to_return = {
            "price_earnings_ttm": 12.5,
            "price_book_fq": 1.1,
            "return_on_equity": 18.0,  # 百分率で返るケース
            "dividend_yield_current": 2.5,  # 百分率
            "RSI": 55.0,
        }
        _FakeHandler.summary_to_return = {"RECOMMENDATION": "BUY"}

        result = tvc.fetch_stock_data_tv("7203.T")

        assert result is not None
        assert result["symbol"] == "7203.T"
        assert result["recommendation"] == "BUY"
        info = result["info"]
        assert info["trailingPE"] == 12.5
        assert info["priceToBook"] == 1.1
        assert info["returnOnEquity"] == pytest.approx(0.18)  # 百分率→小数
        assert info["dividendYield"] == pytest.approx(0.025)
        assert result["tv_indicators"]["RSI"] == 55.0
        # TA_Handler に正しく変換したシンボルを渡している
        assert _FakeHandler.captured["exchange"] == "TSE"
        assert _FakeHandler.captured["symbol"] == "7203"

    def test_returns_none_on_exception(self):
        _FakeHandler.raise_on_call = True
        assert tvc.fetch_stock_data_tv("7203.T") is None

    def test_returns_none_on_invalid_symbol(self):
        assert tvc.fetch_stock_data_tv(".T") is None

    def test_missing_indicators_yield_none(self):
        _FakeHandler.indicators_to_return = {}
        _FakeHandler.summary_to_return = {}
        result = tvc.fetch_stock_data_tv("9984.T")
        assert result is not None
        assert result["info"]["trailingPE"] is None
        assert result["info"]["priceToBook"] is None
        assert result["recommendation"] is None


class TestMergeInfo:
    def test_override_wins_when_not_none(self):
        base = {"trailingPE": 20.0, "priceToBook": 2.0, "returnOnEquity": 0.05}
        override = {"trailingPE": 12.0, "priceToBook": None, "returnOnEquity": 0.18}
        merged = tvc.merge_info(base, override)
        assert merged["trailingPE"] == 12.0  # override
        assert merged["priceToBook"] == 2.0   # base 保持
        assert merged["returnOnEquity"] == 0.18

    def test_none_base(self):
        merged = tvc.merge_info(None, {"trailingPE": 10.0})
        assert merged == {"trailingPE": 10.0}
