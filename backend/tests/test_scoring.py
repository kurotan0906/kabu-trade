"""スコアリングロジックのユニットテスト"""
import pytest
import pandas as pd
import numpy as np

from app.analyzer.fundamental import calc_fundamental_score, score_per, score_pbr, score_roe
from app.analyzer.scorer import get_rating, build_stock_result


class TestFundamentalScore:
    def test_score_per_low(self):
        assert score_per(8.0) == 10

    def test_score_per_high(self):
        assert score_per(30.0) == 0

    def test_score_per_none(self):
        assert score_per(None) == 5

    def test_score_pbr_under_1(self):
        assert score_pbr(0.9) == 7

    def test_score_roe_high(self):
        assert score_roe(0.25) == 10

    def test_calc_fundamental_score_full(self):
        info = {
            "trailingPE": 8.0,
            "priceToBook": 0.9,
            "returnOnEquity": 0.20,
            "dividendYield": 0.03,
            "revenueGrowth": 0.10,
        }
        result = calc_fundamental_score(info)
        assert result["fundamental_score"] == float(10 + 7 + 10 + 7 + 7)
        assert result["per"] == 8.0
        assert result["data_quality"] == "ok"

    def test_calc_fundamental_score_empty_info(self):
        result = calc_fundamental_score({})
        assert result["data_quality"] == "partial"


class TestRating:
    def test_rating_strong_buy(self):
        assert get_rating(85) == "強い買い"

    def test_rating_buy(self):
        assert get_rating(65) == "買い"

    def test_rating_neutral(self):
        assert get_rating(45) == "中立"

    def test_rating_sell(self):
        assert get_rating(25) == "売り"

    def test_rating_strong_sell(self):
        assert get_rating(10) == "強い売り"


class TestBuildStockResult:
    def test_build_result_without_kurotenko(self):
        fundamental = {
            "fundamental_score": 35.0, "per": 10.0, "pbr": 1.0,
            "roe": 0.15, "dividend_yield": 0.02, "revenue_growth": 0.05, "data_quality": "ok"
        }
        technical = {"technical_score": 40.0, "ma_score": 20.0, "rsi_score": 10.0, "macd_score": 10.0}
        result = build_stock_result("7203.T", "トヨタ", "輸送用機器", fundamental, technical)
        assert result["total_score"] == 75.0
        assert result["rating"] == "買い"
        assert result["kurotenko_score"] is None

    def test_build_result_with_kurotenko(self):
        fundamental = {"fundamental_score": 40.0, "per": 8.0, "pbr": 0.9, "roe": 0.20, "dividend_yield": 0.03, "revenue_growth": 0.10, "data_quality": "ok"}
        technical = {"technical_score": 45.0, "ma_score": 20.0, "rsi_score": 15.0, "macd_score": 10.0}
        kurotenko = {"rating": 6, "year_end_turnaround": True, "consec_quarters_profit": True, "sales_yoy": True, "equity_ratio": False, "cf_positive": True, "cash_over_debt": True, "avg_volume": None, "market_cap": True}
        result = build_stock_result("7203.T", "トヨタ", "輸送用機器", fundamental, technical, kurotenko)
        assert result["kurotenko_score"] == pytest.approx(75.0)
        assert result["kurotenko_criteria"]["year_end_turnaround"] is True
