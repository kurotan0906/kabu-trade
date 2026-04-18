"""tv_screener_adapter のユニットテスト"""

import math

import pytest

from app.external.tv_screener_adapter import (
    _percent_to_ratio,
    _safe_float,
    tv_row_to_info,
    tv_row_to_technical_features,
)


class TestSafeFloat:
    def test_valid_number(self):
        assert _safe_float(10.5) == 10.5
        assert _safe_float("3.14") == 3.14
        assert _safe_float(0) == 0.0

    def test_none_returns_none(self):
        assert _safe_float(None) is None

    def test_nan_returns_none(self):
        assert _safe_float(float("nan")) is None

    def test_invalid_string_returns_none(self):
        assert _safe_float("abc") is None


class TestPercentToRatio:
    def test_percent_conversion(self):
        assert _percent_to_ratio(15.0) == 0.15
        assert _percent_to_ratio(2.5) == 0.025
        assert _percent_to_ratio(100) == 1.0

    def test_none_safety(self):
        assert _percent_to_ratio(None) is None
        assert _percent_to_ratio(float("nan")) is None


class TestTvRowToInfo:
    def test_all_fields_mapped(self):
        row = {
            "price_earnings_ttm": 15.0,
            "price_book_ratio": 1.2,
            "return_on_equity": 12.0,
            "dividend_yield_recent": 2.5,
            "total_revenue_yoy_growth_fy": 8.0,
            "market_cap_basic": 1_000_000_000,
            "description": "Toyota Motor",
            "name": "7203",
            "sector": "Automobiles",
        }
        info = tv_row_to_info(row)
        assert info["trailingPE"] == 15.0
        assert info["priceToBook"] == 1.2
        assert info["returnOnEquity"] == 0.12  # ratio
        # dividendYield は yfinance v0.2.40+ の percent 出力に合わせて percent のまま
        assert info["dividendYield"] == 2.5
        assert info["revenueGrowth"] == 0.08  # ratio
        assert info["marketCap"] == 1_000_000_000.0
        assert info["longName"] == "Toyota Motor"
        assert info["sector"] == "Automobiles"

    def test_pb_fallback_to_fq(self):
        row = {"price_book_ratio": None, "price_book_fq": 1.5}
        info = tv_row_to_info(row)
        assert info["priceToBook"] == 1.5

    def test_pb_ratio_preferred_over_fq(self):
        row = {"price_book_ratio": 2.0, "price_book_fq": 1.5}
        info = tv_row_to_info(row)
        assert info["priceToBook"] == 2.0

    def test_empty_row(self):
        info = tv_row_to_info({})
        assert info["trailingPE"] is None
        assert info["priceToBook"] is None
        assert info["returnOnEquity"] is None
        assert info["dividendYield"] is None
        assert info["revenueGrowth"] is None

    def test_longname_fallback_to_name(self):
        row = {"description": None, "name": "7203"}
        info = tv_row_to_info(row)
        assert info["longName"] == "7203"


class TestTvRowToTechnicalFeatures:
    def test_all_fields_mapped(self):
        row = {
            "close": 1000,
            "RSI": 55.0,
            "MACD.macd": 10.0,
            "MACD.signal": 5.0,
            "SMA25": 950.0,
            "SMA75": 900.0,
        }
        feats = tv_row_to_technical_features(row)
        assert feats == {
            "close": 1000.0,
            "rsi": 55.0,
            "macd": 10.0,
            "macd_signal": 5.0,
            "sma25": 950.0,
            "sma75": 900.0,
        }

    def test_empty_row(self):
        feats = tv_row_to_technical_features({})
        assert all(v is None for v in feats.values())
