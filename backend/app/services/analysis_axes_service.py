"""多軸分析集約サービス

stock_scores（最新1件）、chart_analyses（最新1件）、tradingview_signals（最新1件）を
symbol で結合して返す。
"""

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, desc

from app.models.stock_score import StockScore
from app.models.chart_analysis import ChartAnalysis
from app.models.tradingview_signal import TradingViewSignal
from app.schemas.stock_score import AnalysisAxesResponse, AnalysisAxis


async def get_analysis_axes(symbol: str, db: AsyncSession) -> AnalysisAxesResponse:
    """symbol の全分析軸を集約して返す。"""

    score_stmt = (
        select(StockScore)
        .where(StockScore.symbol == symbol)
        .order_by(desc(StockScore.scored_at))
        .limit(1)
    )
    score_result = await db.execute(score_stmt)
    stock_score = score_result.scalar_one_or_none()

    chart_stmt = (
        select(ChartAnalysis)
        .where(ChartAnalysis.symbol == symbol)
        .order_by(desc(ChartAnalysis.created_at))
        .limit(1)
    )
    chart_result = await db.execute(chart_stmt)
    chart_analysis = chart_result.scalar_one_or_none()

    tv_stmt = (
        select(TradingViewSignal)
        .where(TradingViewSignal.symbol == symbol)
        .order_by(desc(TradingViewSignal.updated_at))
        .limit(1)
    )
    tv_result = await db.execute(tv_stmt)
    tv_signal = tv_result.scalar_one_or_none()

    axes = []

    if stock_score:
        axes.append(AnalysisAxis(
            name="ファンダメンタル",
            score=stock_score.fundamental_score,
            detail={
                "per": stock_score.per,
                "pbr": stock_score.pbr,
                "roe": stock_score.roe,
                "dividend_yield": stock_score.dividend_yield,
                "revenue_growth": stock_score.revenue_growth,
            },
        ))
        axes.append(AnalysisAxis(
            name="テクニカル",
            score=stock_score.technical_score,
            detail={
                "ma_score": stock_score.ma_score,
                "rsi_score": stock_score.rsi_score,
                "macd_score": stock_score.macd_score,
            },
        ))
        criteria = stock_score.kurotenko_criteria or {}
        criteria_met = sum(1 for v in criteria.values() if v is True)
        axes.append(AnalysisAxis(
            name="黒点子",
            score=stock_score.kurotenko_score,
            detail={
                "criteria_met": criteria_met,
                "criteria_total": 8,
                **criteria,
            },
        ))

    if chart_analysis:
        axes.append(AnalysisAxis(
            name="チャート分析",
            score=None,
            recommendation=chart_analysis.recommendation,
            detail={
                "trend": chart_analysis.trend,
                "summary": chart_analysis.summary,
                "signals": chart_analysis.signals,
                "analyzed_at": chart_analysis.created_at.isoformat(),
            },
        ))

    if tv_signal:
        axes.append(AnalysisAxis(
            name="TradingView",
            score=tv_signal.score,
            recommendation=tv_signal.recommendation,
            detail={
                "buy_count": tv_signal.buy_count,
                "sell_count": tv_signal.sell_count,
                "neutral_count": tv_signal.neutral_count,
                "ma_recommendation": tv_signal.ma_recommendation,
                "osc_recommendation": tv_signal.osc_recommendation,
                "updated_at": tv_signal.updated_at.isoformat(),
            },
        ))

    return AnalysisAxesResponse(symbol=symbol, axes=axes)
