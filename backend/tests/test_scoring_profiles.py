"""scoring_profiles のユニットテスト"""
import pytest

from app.analyzer.scoring_profiles import (
    GROWTH_PROFILE,
    BALANCED_PROFILE,
    INCOME_PROFILE,
    get_profile,
    compute_phase_score,
    _normalize_max,
    _normalize_min,
    _normalize_pbr,
)


class _FakeStock:
    def __init__(self, **kw):
        for k, v in kw.items():
            setattr(self, k, v)


class TestNormalize:
    def test_normalize_max_none_returns_half(self):
        assert _normalize_max(None, [(10, 1.0)]) == 0.5

    def test_normalize_max_exact_threshold(self):
        assert _normalize_max(10, [(10, 1.0), (20, 0.5)]) == 1.0

    def test_normalize_max_over(self):
        assert _normalize_max(30, [(10, 1.0), (20, 0.5)]) == 0.0

    def test_normalize_min_high_value(self):
        assert _normalize_min(0.25, [(0.20, 1.0), (0.10, 0.5)]) == 1.0

    def test_normalize_pbr_zero(self):
        assert _normalize_pbr(0) == 0.5


class TestGetProfile:
    def test_growth(self):
        assert get_profile("growth") is GROWTH_PROFILE

    def test_balanced(self):
        assert get_profile("balanced") is BALANCED_PROFILE

    def test_income(self):
        assert get_profile("income") is INCOME_PROFILE

    def test_unknown_falls_back_to_balanced(self):
        assert get_profile("???") is BALANCED_PROFILE


class TestComputePhaseScore:
    def test_high_growth_stock_favored_by_growth_profile(self):
        stock = _FakeStock(
            per=20.0, pbr=2.5, roe=0.22, dividend_yield=0.005, revenue_growth=0.35,
            ma_score=20, rsi_score=15, macd_score=15,
        )
        growth = compute_phase_score(stock, GROWTH_PROFILE)
        income = compute_phase_score(stock, INCOME_PROFILE)
        assert growth > income

    def test_high_dividend_stock_favored_by_income_profile(self):
        stock = _FakeStock(
            per=9.0, pbr=0.9, roe=0.11, dividend_yield=0.055, revenue_growth=0.02,
            ma_score=12, rsi_score=8, macd_score=8,
        )
        income = compute_phase_score(stock, INCOME_PROFILE)
        growth = compute_phase_score(stock, GROWTH_PROFILE)
        assert income > growth

    def test_dict_input(self):
        stock = {
            "per": 10.0, "pbr": 1.0, "roe": 0.15, "dividend_yield": 0.03,
            "revenue_growth": 0.10, "ma_score": 20, "rsi_score": 15, "macd_score": 15,
        }
        score = compute_phase_score(stock, BALANCED_PROFILE)
        assert 0 <= score <= 100

    def test_all_none_returns_midpoint(self):
        stock = _FakeStock(per=None, pbr=None, roe=None, dividend_yield=None,
                           revenue_growth=None, ma_score=None, rsi_score=None, macd_score=None)
        score = compute_phase_score(stock, BALANCED_PROFILE)
        # 全 None なら fundamentals が 0.5、technical が 0 → 25 点前後
        assert 20 <= score <= 30
