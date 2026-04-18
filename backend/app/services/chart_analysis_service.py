"""Chart analysis service - 指標計算とヒューリスティックで分析を自動生成"""

from decimal import Decimal
from typing import Any, Dict, List
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.chart_analysis import ChartAnalysis
from app.schemas.stock import StockPriceData
from app.services.stock_service import StockService
from app.utils.technical_indicators import TechnicalIndicators


class ChartAnalysisService:
    """テクニカル指標からルールベースで分析を生成し、DB に保存するサービス"""

    def __init__(self, db: AsyncSession):
        self.db = db
        self.stock_service = StockService(db)

    async def generate_and_save(
        self, symbol: str, timeframe: str = "1D"
    ) -> ChartAnalysis:
        prices: List[StockPriceData] = await self.stock_service.get_stock_prices(
            symbol, period="1y"
        )
        if not prices:
            raise ValueError(f"price data unavailable for {symbol}")

        indicators = TechnicalIndicators.calculate_all_indicators(prices)
        last_close = Decimal(str(prices[-1].close))

        score = self._score_signals(indicators, last_close)
        trend = self._derive_trend(score)
        recommendation = self._derive_recommendation(score)
        signals_dict = self._build_signals_dict(indicators, last_close)
        summary = self._build_summary(
            symbol, last_close, indicators, trend, recommendation
        )

        analysis = ChartAnalysis(
            symbol=symbol,
            timeframe=timeframe,
            screenshot_path=None,
            trend=trend,
            signals=signals_dict,
            summary=summary,
            recommendation=recommendation,
        )
        self.db.add(analysis)
        await self.db.commit()
        await self.db.refresh(analysis)
        return analysis

    @staticmethod
    def _score_signals(indicators: Dict[str, Any], close: Decimal) -> int:
        score = 0
        ma = indicators["moving_averages"]
        ma_s, ma_m, ma_l = ma["ma_short"], ma["ma_medium"], ma["ma_long"]
        if ma_s > 0 and ma_m > 0 and ma_l > 0:
            if close > ma_s > ma_m > ma_l:
                score += 2
            elif close < ma_s < ma_m < ma_l:
                score -= 2

        macd = indicators["macd"]
        if macd["macd"] > macd["signal"]:
            score += 1
        elif macd["macd"] < macd["signal"]:
            score -= 1

        rsi = indicators["rsi"]
        if rsi > 70:
            score -= 1
        elif rsi >= 50:
            score += 1
        elif rsi >= 30:
            score -= 1
        else:
            score += 1

        bb = indicators["bollinger_bands"]
        if bb["upper"] > 0 and bb["lower"] > 0:
            if close > bb["upper"]:
                score -= 1
            elif close < bb["lower"]:
                score += 1

        return score

    @staticmethod
    def _derive_trend(score: int) -> str:
        if score >= 2:
            return "bullish"
        if score <= -2:
            return "bearish"
        return "neutral"

    @staticmethod
    def _derive_recommendation(score: int) -> str:
        if score >= 3:
            return "buy"
        if score <= -3:
            return "sell"
        return "hold"

    @staticmethod
    def _fmt(value: Decimal, digits: int = 2) -> str:
        return f"{float(value):.{digits}f}"

    @classmethod
    def _build_signals_dict(
        cls, indicators: Dict[str, Any], close: Decimal
    ) -> Dict[str, str]:
        ma = indicators["moving_averages"]
        macd = indicators["macd"]
        bb = indicators["bollinger_bands"]
        sr = indicators["support_resistance"]
        rsi = indicators["rsi"]

        rsi_label = (
            "過熱"
            if rsi > 70
            else "やや強気"
            if rsi >= 50
            else "やや弱気"
            if rsi >= 30
            else "売られすぎ"
        )
        macd_cross = "GC" if macd["macd"] > macd["signal"] else "DC"
        bb_position = (
            "上抜け"
            if close > bb["upper"]
            else "下抜け"
            if close < bb["lower"]
            else "中央帯"
        )
        ma_alignment = (
            "完全陽転（価格 > 5日 > 25日 > 75日）"
            if close > ma["ma_short"] > ma["ma_medium"] > ma["ma_long"]
            else "完全陰転（価格 < 5日 < 25日 < 75日）"
            if close < ma["ma_short"] < ma["ma_medium"] < ma["ma_long"]
            else "混在"
        )

        return {
            "rsi": f"{cls._fmt(rsi)} {rsi_label}",
            "macd": f"{cls._fmt(macd['macd'], 3)} vs Signal {cls._fmt(macd['signal'], 3)} ({macd_cross})",
            "bollinger": f"upper {cls._fmt(bb['upper'])} / lower {cls._fmt(bb['lower'])} / price {cls._fmt(close)} ({bb_position})",
            "ma": f"5日 {cls._fmt(ma['ma_short'])} / 25日 {cls._fmt(ma['ma_medium'])} / 75日 {cls._fmt(ma['ma_long'])} — {ma_alignment}",
            "support_resistance": f"S {cls._fmt(sr['support'])} / R {cls._fmt(sr['resistance'])}",
        }

    @classmethod
    def _build_summary(
        cls,
        symbol: str,
        close: Decimal,
        indicators: Dict[str, Any],
        trend: str,
        recommendation: str,
    ) -> str:
        ma = indicators["moving_averages"]
        macd = indicators["macd"]
        bb = indicators["bollinger_bands"]
        rsi = indicators["rsi"]

        trend_jp = {"bullish": "強気", "bearish": "弱気", "neutral": "中立"}[trend]
        rec_jp = {"buy": "買い", "sell": "売り", "hold": "様子見"}[recommendation]

        ma_note = (
            "MA配列は完全陽転で上昇基調"
            if close > ma["ma_short"] > ma["ma_medium"] > ma["ma_long"]
            else "MA配列は完全陰転で下降基調"
            if close < ma["ma_short"] < ma["ma_medium"] < ma["ma_long"]
            else "MA配列は混在でトレンド不鮮明"
        )
        macd_note = (
            "MACD > Signal でモメンタム陽転"
            if macd["macd"] > macd["signal"]
            else "MACD < Signal でモメンタム陰転"
        )
        rsi_note = (
            f"RSI {cls._fmt(rsi)} で過熱圏"
            if rsi > 70
            else f"RSI {cls._fmt(rsi)} で売られすぎ圏"
            if rsi < 30
            else f"RSI {cls._fmt(rsi)} で中立域"
        )
        bb_note = (
            "BB上限を超過し反落警戒"
            if close > bb["upper"]
            else "BB下限を割り込み反発余地"
            if close < bb["lower"]
            else "BB中央帯でレンジ色"
        )

        return (
            f"{symbol} 日足は{trend_jp}・推奨は{rec_jp}。"
            f"{ma_note}。{macd_note}、{rsi_note}、{bb_note}。"
            f"価格 {cls._fmt(close)} / BB {cls._fmt(bb['lower'])}〜{cls._fmt(bb['upper'])}。"
        )
