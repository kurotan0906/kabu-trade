"""advisor_service のユニットテスト"""
import pytest

from app.services import advisor_service as a


class TestFutureValue:
    def test_zero_rate(self):
        # pv=100万、月10万積立、年利0%、10年 → 100万 + 120万*10 = 1300万
        assert a.future_value(1_000_000, 100_000, 0.0, 10) == 13_000_000

    def test_only_pv_compound(self):
        # pv=100万、積立0、年利5%、10 年 → 約 162.8万
        v = a.future_value(1_000_000, 0, 0.05, 10)
        assert 1_628_000 < v < 1_630_000

    def test_zero_years(self):
        assert a.future_value(500_000, 50_000, 0.05, 0) == 500_000


class TestCalculateRequiredRate:
    def test_invalid_months(self):
        assert a.calculate_required_rate(1_000_000, 500_000, 0) is None

    def test_invalid_pv(self):
        assert a.calculate_required_rate(1_000_000, 0, 120) is None

    def test_no_monthly_exact(self):
        # 100万 → 200万、10年間 → 年利 7.18%
        rate = a.calculate_required_rate(goal=2_000_000, pv=1_000_000, n_months=120, monthly_investment=0)
        assert rate is not None
        assert 7.0 < rate < 7.3

    def test_monthly_already_reaches_goal(self):
        # 積立のみで達成可能なら 0.0
        rate = a.calculate_required_rate(
            goal=1_500_000, pv=1_000_000, n_months=60, monthly_investment=50_000
        )
        assert rate == 0.0

    def test_monthly_binary_search(self):
        # 期待年利は正の値、具体値は二分探索結果に依存
        rate = a.calculate_required_rate(
            goal=10_000_000, pv=1_000_000, n_months=120, monthly_investment=30_000
        )
        assert rate is not None
        assert 0 < rate < 20


class TestSimulate:
    def test_timeseries_length(self):
        ts = a.simulate(1_000_000, 50_000, 0.05, 10)
        assert len(ts) == 11  # year 0 ..year 10
        assert ts[0]["year"] == 0
        assert ts[-1]["year"] == 10

    def test_contributed_accumulates(self):
        ts = a.simulate(1_000_000, 100_000, 0.0, 5)
        assert ts[0]["contributed"] == 1_000_000
        assert ts[5]["contributed"] == 1_000_000 + 100_000 * 12 * 5

    def test_gain_is_value_minus_contributed(self):
        ts = a.simulate(1_000_000, 50_000, 0.05, 3)
        for point in ts:
            assert point["gain"] == pytest.approx(point["value"] - point["contributed"], abs=0.01)
