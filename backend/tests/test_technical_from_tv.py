"""technical_from_tv のユニットテスト"""

import pytest

from app.analyzer.technical_from_tv import (
    calc_technical_score_from_tv,
    score_ma_from_tv,
    score_macd_from_tv,
    score_rsi_from_tv,
)


class TestScoreMa:
    def test_full_bullish_alignment(self):
        # close > sma25 > sma75
        assert score_ma_from_tv(1100, 1000, 900) == 20

    def test_weak_bullish(self):
        # close > sma25, but sma25 < sma75 → fall through
        assert score_ma_from_tv(1100, 1050, 1080) == 12

    def test_full_bearish_alignment(self):
        # close < sma25 < sma75
        assert score_ma_from_tv(900, 950, 1000) == 0

    def test_neutral_when_close_between(self):
        # close < sma25, sma25 > sma75 → neutral
        assert score_ma_from_tv(950, 1000, 900) == 6

    def test_none_returns_neutral(self):
        assert score_ma_from_tv(None, 1000, 900) == 6
        assert score_ma_from_tv(1000, None, 900) == 6
        assert score_ma_from_tv(1000, 900, None) == 6


class TestScoreRsi:
    @pytest.mark.parametrize(
        "rsi,expected",
        [
            (None, 8),
            (20, 15),   # ≤30
            (30, 15),
            (35, 10),   # ≤39
            (39, 10),
            (50, 8),    # ≤60
            (60, 8),
            (65, 4),    # ≤69
            (69, 4),
            (75, 0),    # >69
            (100, 0),
        ],
    )
    def test_rsi_ranges(self, rsi, expected):
        assert score_rsi_from_tv(rsi) == expected


class TestScoreMacd:
    def test_bullish(self):
        assert score_macd_from_tv(10, 5) == 8

    def test_bearish(self):
        assert score_macd_from_tv(5, 10) == 3

    def test_equal(self):
        assert score_macd_from_tv(5, 5) == 3

    def test_none(self):
        assert score_macd_from_tv(None, 5) == 3
        assert score_macd_from_tv(5, None) == 3


class TestCalcTechnicalScoreFromTv:
    def test_max_bullish(self):
        result = calc_technical_score_from_tv({
            "close": 1100, "sma25": 1000, "sma75": 900,
            "rsi": 25, "macd": 10, "macd_signal": 5,
        })
        assert result["ma_score"] == 20.0
        assert result["rsi_score"] == 15.0
        assert result["macd_score"] == 8.0
        assert result["technical_score"] == 43.0

    def test_max_bearish(self):
        result = calc_technical_score_from_tv({
            "close": 900, "sma25": 1000, "sma75": 1100,
            "rsi": 75, "macd": 5, "macd_signal": 10,
        })
        assert result["ma_score"] == 0.0
        assert result["rsi_score"] == 0.0
        assert result["macd_score"] == 3.0
        assert result["technical_score"] == 3.0

    def test_all_none_neutral(self):
        result = calc_technical_score_from_tv({})
        assert result["ma_score"] == 6.0
        assert result["rsi_score"] == 8.0
        assert result["macd_score"] == 3.0
        assert result["technical_score"] == 17.0
