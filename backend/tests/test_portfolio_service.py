"""Portfolio service のユニットテスト（DB アクセス不要部分）"""
from datetime import date

from app.services import portfolio_service as ps


class TestNisa:
    def test_nisa_remaining_full(self):
        assert ps.get_nisa_remaining(0) == ps.NISA_GROWTH_ANNUAL_LIMIT

    def test_nisa_remaining_partial(self):
        assert ps.get_nisa_remaining(1_000_000) == ps.NISA_GROWTH_ANNUAL_LIMIT - 1_000_000

    def test_nisa_remaining_clamps_at_zero(self):
        assert ps.get_nisa_remaining(10_000_000) == 0.0


class TestValueConverters:
    def test_to_float_ok(self):
        assert ps._to_float("123.45") == 123.45

    def test_to_float_none(self):
        assert ps._to_float(None) is None

    def test_to_float_invalid(self):
        assert ps._to_float("abc") is None

    def test_to_date_ok(self):
        assert ps._to_date("2026-04-11") == date(2026, 4, 11)

    def test_to_date_none(self):
        assert ps._to_date(None) is None

    def test_to_date_invalid(self):
        assert ps._to_date("not-a-date") is None

    def test_stringify_date(self):
        assert ps._stringify(date(2026, 4, 11)) == "2026-04-11"

    def test_stringify_number(self):
        assert ps._stringify(1234.5) == "1234.5"
