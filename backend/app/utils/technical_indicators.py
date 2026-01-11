"""Technical indicators calculation"""

import pandas as pd
import pandas_ta as ta
from typing import List, Dict, Any
from decimal import Decimal
from app.schemas.stock import StockPriceData


class TechnicalIndicators:
    """テクニカル指標計算クラス"""

    @staticmethod
    def calculate_moving_averages(
        prices: List[StockPriceData], short: int = 5, medium: int = 25, long: int = 75
    ) -> Dict[str, Decimal]:
        """
        移動平均線を計算
        
        Args:
            prices: 株価データのリスト
            short: 短期移動平均の期間（デフォルト: 5日）
            medium: 中期移動平均の期間（デフォルト: 25日）
            long: 長期移動平均の期間（デフォルト: 75日）
            
        Returns:
            Dict[str, Decimal]: 移動平均線の値
        """
        if not prices:
            return {
                "ma_short": Decimal("0"),
                "ma_medium": Decimal("0"),
                "ma_long": Decimal("0"),
            }

        df = pd.DataFrame([p.dict() for p in prices])
        df["close"] = pd.to_numeric(df["close"], errors="coerce")
        df = df.sort_values("date")

        ma_short = df["close"].rolling(window=short).mean().iloc[-1]
        ma_medium = df["close"].rolling(window=medium).mean().iloc[-1]
        ma_long = df["close"].rolling(window=long).mean().iloc[-1]

        return {
            "ma_short": Decimal(str(ma_short)) if not pd.isna(ma_short) else Decimal("0"),
            "ma_medium": Decimal(str(ma_medium)) if not pd.isna(ma_medium) else Decimal("0"),
            "ma_long": Decimal(str(ma_long)) if not pd.isna(ma_long) else Decimal("0"),
        }

    @staticmethod
    def calculate_rsi(prices: List[StockPriceData], period: int = 14) -> Decimal:
        """
        RSI（相対力指数）を計算
        
        Args:
            prices: 株価データのリスト
            period: RSIの期間（デフォルト: 14日）
            
        Returns:
            Decimal: RSIの値（0-100）
        """
        if len(prices) < period + 1:
            return Decimal("50")  # データ不足時は中立値

        df = pd.DataFrame([p.dict() for p in prices])
        df["close"] = pd.to_numeric(df["close"], errors="coerce")
        df = df.sort_values("date")

        rsi = ta.rsi(df["close"], length=period)
        rsi_value = rsi.iloc[-1]

        return (
            Decimal(str(rsi_value)) if not pd.isna(rsi_value) else Decimal("50")
        )

    @staticmethod
    def calculate_macd(
        prices: List[StockPriceData], fast: int = 12, slow: int = 26, signal: int = 9
    ) -> Dict[str, Decimal]:
        """
        MACDを計算
        
        Args:
            prices: 株価データのリスト
            fast: 短期EMA期間（デフォルト: 12）
            slow: 長期EMA期間（デフォルト: 26）
            signal: シグナル線期間（デフォルト: 9）
            
        Returns:
            Dict[str, Decimal]: MACD、シグナル、ヒストグラム
        """
        if len(prices) < slow + signal:
            return {
                "macd": Decimal("0"),
                "signal": Decimal("0"),
                "histogram": Decimal("0"),
            }

        df = pd.DataFrame([p.dict() for p in prices])
        df["close"] = pd.to_numeric(df["close"], errors="coerce")
        df = df.sort_values("date")

        macd_data = ta.macd(df["close"], fast=fast, slow=slow, signal=signal)

        macd_value = macd_data[f"MACD_{fast}_{slow}_{signal}"].iloc[-1]
        signal_value = macd_data[f"MACDs_{fast}_{slow}_{signal}"].iloc[-1]
        histogram_value = macd_data[f"MACDh_{fast}_{slow}_{signal}"].iloc[-1]

        return {
            "macd": Decimal(str(macd_value)) if not pd.isna(macd_value) else Decimal("0"),
            "signal": Decimal(str(signal_value)) if not pd.isna(signal_value) else Decimal("0"),
            "histogram": Decimal(str(histogram_value)) if not pd.isna(histogram_value) else Decimal("0"),
        }

    @staticmethod
    def calculate_bollinger_bands(
        prices: List[StockPriceData], period: int = 20, std: float = 2.0
    ) -> Dict[str, Decimal]:
        """
        ボリンジャーバンドを計算
        
        Args:
            prices: 株価データのリスト
            period: 移動平均の期間（デフォルト: 20日）
            std: 標準偏差の倍数（デフォルト: 2.0）
            
        Returns:
            Dict[str, Decimal]: 上バンド、中バンド（移動平均）、下バンド
        """
        if len(prices) < period:
            return {
                "upper": Decimal("0"),
                "middle": Decimal("0"),
                "lower": Decimal("0"),
            }

        df = pd.DataFrame([p.dict() for p in prices])
        df["close"] = pd.to_numeric(df["close"], errors="coerce")
        df = df.sort_values("date")

        bb_data = ta.bbands(df["close"], length=period, std=std)

        upper = bb_data[f"BBU_{period}_{std}"].iloc[-1]
        middle = bb_data[f"BBM_{period}_{std}"].iloc[-1]
        lower = bb_data[f"BBL_{period}_{std}"].iloc[-1]

        return {
            "upper": Decimal(str(upper)) if not pd.isna(upper) else Decimal("0"),
            "middle": Decimal(str(middle)) if not pd.isna(middle) else Decimal("0"),
            "lower": Decimal(str(lower)) if not pd.isna(lower) else Decimal("0"),
        }

    @staticmethod
    def find_support_resistance(prices: List[StockPriceData]) -> Dict[str, Decimal]:
        """
        サポート・レジスタンスラインを検出
        
        Args:
            prices: 株価データのリスト
            
        Returns:
            Dict[str, Decimal]: サポートライン、レジスタンスライン
        """
        if not prices:
            return {
                "support": Decimal("0"),
                "resistance": Decimal("0"),
            }

        df = pd.DataFrame([p.dict() for p in prices])
        df["low"] = pd.to_numeric(df["low"], errors="coerce")
        df["high"] = pd.to_numeric(df["high"], errors="coerce")
        df = df.sort_values("date")

        # 簡易的な実装: 過去N日間の最低値と最高値
        lookback = min(20, len(prices))
        support = df["low"].tail(lookback).min()
        resistance = df["high"].tail(lookback).max()

        return {
            "support": Decimal(str(support)) if not pd.isna(support) else Decimal("0"),
            "resistance": Decimal(str(resistance)) if not pd.isna(resistance) else Decimal("0"),
        }

    @staticmethod
    def calculate_all_indicators(prices: List[StockPriceData]) -> Dict[str, Any]:
        """
        すべてのテクニカル指標を計算
        
        Args:
            prices: 株価データのリスト
            
        Returns:
            Dict[str, Any]: すべてのテクニカル指標
        """
        return {
            "moving_averages": TechnicalIndicators.calculate_moving_averages(prices),
            "rsi": TechnicalIndicators.calculate_rsi(prices),
            "macd": TechnicalIndicators.calculate_macd(prices),
            "bollinger_bands": TechnicalIndicators.calculate_bollinger_bands(prices),
            "support_resistance": TechnicalIndicators.find_support_resistance(prices),
        }
