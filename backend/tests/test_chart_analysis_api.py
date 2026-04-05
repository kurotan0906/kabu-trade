"""ChartAnalysis API tests"""

import pytest
from app.schemas.chart_analysis import ChartAnalysisCreate, ChartAnalysisResponse
from datetime import datetime


def test_chart_analysis_create_requires_symbol():
    with pytest.raises(Exception):
        ChartAnalysisCreate(
            timeframe="1D",
            trend="bullish",
            summary="テストサマリー",
            recommendation="buy",
        )


def test_chart_analysis_create_valid():
    data = ChartAnalysisCreate(
        symbol="7203",
        timeframe="1D",
        trend="bullish",
        signals={"rsi": "oversold_recovery", "ma": "golden_cross_approaching"},
        summary="日足チャートでは上昇トレンドが継続中",
        recommendation="buy",
    )
    assert data.symbol == "7203"
    assert data.timeframe == "1D"
    assert data.trend == "bullish"
    assert data.recommendation == "buy"
    assert data.signals["rsi"] == "oversold_recovery"
    assert data.screenshot_path is None


def test_chart_analysis_create_optional_fields():
    data = ChartAnalysisCreate(
        symbol="9984",
        timeframe="1W",
        trend="neutral",
        summary="週足チャートではもみ合い継続",
        recommendation="hold",
    )
    assert data.signals is None
    assert data.screenshot_path is None
