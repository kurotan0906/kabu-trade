"""paper_trade_service の純粋関数テスト（DB アクセス不要）"""

import pytest
from fastapi import HTTPException

from app.services import paper_trade_service as svc


class TestValidateQuantity:
    def test_ok_100(self):
        svc.validate_quantity(100)

    def test_ok_500(self):
        svc.validate_quantity(500)

    def test_zero_fails(self):
        with pytest.raises(HTTPException) as exc:
            svc.validate_quantity(0)
        assert exc.value.status_code == 400
        assert "100株単位" in exc.value.detail

    def test_negative_fails(self):
        with pytest.raises(HTTPException):
            svc.validate_quantity(-100)

    def test_not_lot_size_fails(self):
        with pytest.raises(HTTPException):
            svc.validate_quantity(150)


class TestCalcWeightedAvg:
    def test_simple(self):
        # 100株@1000 に 100株@1200 を買い増し → 平均 1100
        assert svc.calc_weighted_avg(100, 1000.0, 100, 1200.0) == 1100.0

    def test_unequal_qty(self):
        # 100株@1000 に 300株@1400 を買い増し → (100000 + 420000) / 400 = 1300
        assert svc.calc_weighted_avg(100, 1000.0, 300, 1400.0) == 1300.0


class TestCalcRealizedPl:
    def test_gain(self):
        assert svc.calc_realized_pl(2650.0, 2500.0, 100) == 15000.0

    def test_loss(self):
        assert svc.calc_realized_pl(2400.0, 2500.0, 100) == -10000.0

    def test_breakeven(self):
        assert svc.calc_realized_pl(2500.0, 2500.0, 100) == 0.0


from datetime import date as date_cls


class TestBuildCloseLookup:
    def test_builds_per_symbol_ordered(self):
        rows = [("A", date_cls(2026, 1, 2), 200.0), ("A", date_cls(2026, 1, 1), 100.0), ("B", date_cls(2026, 1, 1), 50.0)]
        lookup = svc.build_close_lookup(rows)
        assert list(lookup["A"].keys()) == [date_cls(2026, 1, 1), date_cls(2026, 1, 2)]
        assert lookup["A"][date_cls(2026, 1, 2)] == 200.0
        assert lookup["B"][date_cls(2026, 1, 1)] == 50.0


class TestForwardFill:
    def _lookup(self):
        return svc.build_close_lookup([("A", date_cls(2026, 1, 1), 100.0), ("A", date_cls(2026, 1, 3), 120.0)])

    def test_exact_hit(self):
        assert svc.lookup_close_forward_fill(self._lookup(), "A", date_cls(2026, 1, 1)) == 100.0

    def test_forward_fills_gap(self):
        assert svc.lookup_close_forward_fill(self._lookup(), "A", date_cls(2026, 1, 2)) == 100.0

    def test_before_earliest(self):
        assert svc.lookup_close_forward_fill(self._lookup(), "A", date_cls(2025, 12, 31)) is None

    def test_unknown_symbol(self):
        assert svc.lookup_close_forward_fill(self._lookup(), "X", date_cls(2026, 1, 1)) is None


class TestApplyTradeToState:
    def test_buy_new(self):
        holdings: dict = {}
        new_cash = svc.apply_trade_to_state({"symbol": "A", "action": "buy", "quantity": 100, "price": 1000.0}, 1_000_000.0, holdings)
        assert new_cash == 900_000.0
        assert holdings == {"A": {"qty": 100, "avg_price": 1000.0}}

    def test_buy_more_averages(self):
        holdings = {"A": {"qty": 100, "avg_price": 1000.0}}
        svc.apply_trade_to_state({"symbol": "A", "action": "buy", "quantity": 100, "price": 1200.0}, 1_000_000.0, holdings)
        assert holdings["A"]["qty"] == 200
        assert holdings["A"]["avg_price"] == 1100.0

    def test_sell_partial(self):
        holdings = {"A": {"qty": 200, "avg_price": 1000.0}}
        new_cash = svc.apply_trade_to_state({"symbol": "A", "action": "sell", "quantity": 100, "price": 1300.0}, 0.0, holdings)
        assert new_cash == 130_000.0
        assert holdings["A"]["qty"] == 100

    def test_sell_all_removes_holding(self):
        holdings = {"A": {"qty": 100, "avg_price": 1000.0}}
        svc.apply_trade_to_state({"symbol": "A", "action": "sell", "quantity": 100, "price": 1100.0}, 0.0, holdings)
        assert "A" not in holdings


from datetime import datetime as datetime_cls


def _trade(action: str, qty: int, price: float, day: int, month: int = 4):
    return {"action": action, "quantity": qty, "price": price, "executed_at": datetime_cls(2026, month, day)}


class TestBuildFifoCycles:
    def test_single_cycle(self):
        trades = [_trade("buy", 100, 2500, 1), _trade("sell", 100, 2650, 1, month=5)]
        cycles, open_info = svc.build_fifo_cycles(trades)
        assert len(cycles) == 1
        assert cycles[0]["pl"] == 15000
        assert cycles[0]["holding_days"] == 30
        assert open_info == {"quantity": 0, "avg_price": 0.0, "entry_date": None}

    def test_one_sell_consumes_two_lots(self):
        trades = [_trade("buy", 100, 1000, 1), _trade("buy", 100, 1200, 5), _trade("sell", 200, 1400, 10)]
        cycles, open_info = svc.build_fifo_cycles(trades)
        assert len(cycles) == 2
        assert cycles[0]["pl"] == 40000
        assert cycles[1]["pl"] == 20000
        assert open_info["quantity"] == 0

    def test_partial_close_leaves_open(self):
        trades = [_trade("buy", 100, 1000, 1), _trade("buy", 100, 1200, 5), _trade("sell", 100, 1400, 10)]
        cycles, open_info = svc.build_fifo_cycles(trades)
        assert len(cycles) == 1
        assert open_info["quantity"] == 100
        assert open_info["avg_price"] == 1200

    def test_fifo_total_pl(self):
        trades = [_trade("buy", 100, 1000, 1), _trade("buy", 100, 1200, 5), _trade("sell", 150, 1500, 10)]
        cycles, _ = svc.build_fifo_cycles(trades)
        assert sum(c["pl"] for c in cycles) == 65000


class TestBuildSummaryMetrics:
    def test_happy_path(self):
        cycles = [{"pl": 15000, "holding_days": 30, "return_pct": 6.0}, {"pl": -5000, "holding_days": 10, "return_pct": -2.0}]
        m = svc.build_summary_metrics(cycles, buy_count=2, sell_count=2, unrealized_pl=0, total_buy_amount=500000)
        assert m["win_count"] == 1
        assert m["win_rate"] == 0.5
        assert m["profit_factor"] == 3.0
        assert m["expectancy"] == 5000
        assert m["return_pct"] == 2.0

    def test_no_losses_profit_factor_null(self):
        cycles = [{"pl": 15000, "holding_days": 30, "return_pct": 6.0}]
        m = svc.build_summary_metrics(cycles, 1, 1, 0, 250000)
        assert m["profit_factor"] is None

    def test_no_trades(self):
        m = svc.build_summary_metrics([], 0, 0, 0, 0)
        assert m["win_rate"] is None
        assert m["return_pct"] is None
