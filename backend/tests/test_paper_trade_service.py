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
