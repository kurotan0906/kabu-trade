"""Analysis engine - 分析エンジン"""

from typing import List, Dict, Any
from decimal import Decimal
from app.schemas.stock import StockInfo, StockPriceData
from app.utils.technical_indicators import TechnicalIndicators
from app.utils.fundamental_analysis import FundamentalAnalysis


class AnalysisEngine:
    """分析エンジン - テクニカル・ファンダメンタル分析の実行"""

    @staticmethod
    def calculate_technical_indicators(
        prices: List[StockPriceData],
    ) -> Dict[str, Any]:
        """
        テクニカル指標を計算
        
        Args:
            prices: 株価データのリスト
            
        Returns:
            Dict[str, Any]: テクニカル指標
        """
        return TechnicalIndicators.calculate_all_indicators(prices)

    @staticmethod
    def calculate_fundamental_metrics(
        stock_info: StockInfo,
    ) -> Dict[str, Any]:
        """
        ファンダメンタル指標を計算
        
        Args:
            stock_info: 銘柄情報
            
        Returns:
            Dict[str, Any]: ファンダメンタル指標
        """
        return FundamentalAnalysis.evaluate_financial_health(stock_info)

    @staticmethod
    def determine_buy_signal(
        technical: Dict[str, Any],
        fundamental: Dict[str, Any],
        current_price: Decimal,
    ) -> Dict[str, Any]:
        """
        買いシグナルを判定
        
        Args:
            technical: テクニカル指標
            fundamental: ファンダメンタル指標
            current_price: 現在の株価
            
        Returns:
            Dict[str, Any]: 買いシグナル（スコア、推奨度、理由）
        """
        score = 0
        reasons = []

        # RSI判定
        rsi = technical.get("rsi", Decimal("50"))
        if rsi < 30:
            score += 30
            reasons.append(f"RSI {rsi:.1f}が30を下回っており、売られすぎの可能性")
        elif rsi < 50:
            score += 15
            reasons.append(f"RSI {rsi:.1f}が50未満で買い機会の可能性")

        # 移動平均線判定
        ma = technical.get("moving_averages", {})
        ma_short = ma.get("ma_short", Decimal("0"))
        ma_long = ma.get("ma_long", Decimal("0"))
        if ma_short > ma_long and ma_short > 0 and ma_long > 0:
            score += 20
            reasons.append("短期移動平均線が長期移動平均線を上回っている（ゴールデンクロス）")

        # MACD判定
        macd_data = technical.get("macd", {})
        macd_histogram = macd_data.get("histogram", Decimal("0"))
        if macd_histogram > 0:
            score += 15
            reasons.append("MACDヒストグラムがプラスで上昇トレンド")

        # ボリンジャーバンド判定
        bb = technical.get("bollinger_bands", {})
        lower_band = bb.get("lower", Decimal("0"))
        if current_price <= lower_band and lower_band > 0:
            score += 15
            reasons.append("株価がボリンジャーバンドの下バンドに近づいている")

        # ファンダメンタル判定
        fundamental_score = fundamental.get("score", 50)
        if fundamental_score >= 70:
            score += 20
            reasons.append("ファンダメンタル指標が良好")
        elif fundamental_score >= 50:
            score += 10
            reasons.append("ファンダメンタル指標が適正")

        # スコアを0-100に正規化
        score = min(score, 100)

        # 推奨度を決定
        if score >= 80:
            recommendation = "強力"
        elif score >= 60:
            recommendation = "推奨"
        elif score >= 40:
            recommendation = "注意"
        else:
            recommendation = "非推奨"

        return {
            "score": score,
            "recommendation": recommendation,
            "reasons": reasons,
        }

    @staticmethod
    def determine_sell_signal(
        technical: Dict[str, Any],
        fundamental: Dict[str, Any],
        current_price: Decimal,
    ) -> Dict[str, Any]:
        """
        売りシグナルを判定
        
        Args:
            technical: テクニカル指標
            fundamental: ファンダメンタル指標
            current_price: 現在の株価
            
        Returns:
            Dict[str, Any]: 売りシグナル（スコア、推奨度、理由）
        """
        score = 0
        reasons = []

        # RSI判定
        rsi = technical.get("rsi", Decimal("50"))
        if rsi > 70:
            score += 30
            reasons.append(f"RSI {rsi:.1f}が70を上回っており、買われすぎの可能性")
        elif rsi > 50:
            score += 15
            reasons.append(f"RSI {rsi:.1f}が50を上回っている")

        # 移動平均線判定
        ma = technical.get("moving_averages", {})
        ma_short = ma.get("ma_short", Decimal("0"))
        ma_long = ma.get("ma_long", Decimal("0"))
        if ma_short < ma_long and ma_short > 0 and ma_long > 0:
            score += 20
            reasons.append("短期移動平均線が長期移動平均線を下回っている（デッドクロス）")

        # MACD判定
        macd_data = technical.get("macd", {})
        macd_histogram = macd_data.get("histogram", Decimal("0"))
        if macd_histogram < 0:
            score += 15
            reasons.append("MACDヒストグラムがマイナスで下降トレンド")

        # ボリンジャーバンド判定
        bb = technical.get("bollinger_bands", {})
        upper_band = bb.get("upper", Decimal("0"))
        if current_price >= upper_band and upper_band > 0:
            score += 15
            reasons.append("株価がボリンジャーバンドの上バンドに近づいている")

        # ファンダメンタル判定
        fundamental_score = fundamental.get("score", 50)
        if fundamental_score < 30:
            score += 20
            reasons.append("ファンダメンタル指標が悪化している")

        # スコアを0-100に正規化
        score = min(score, 100)

        # 推奨度を決定
        if score >= 80:
            recommendation = "強力"
        elif score >= 60:
            recommendation = "推奨"
        elif score >= 40:
            recommendation = "注意"
        else:
            recommendation = "様子見"

        return {
            "score": score,
            "recommendation": recommendation,
            "reasons": reasons,
        }
