"""テクニカルスコア計算 - stock-advisor/analyzer/technical.py から移植"""

import pandas as pd
import ta


def score_ma(history: pd.DataFrame) -> int:
    if len(history) < 75:
        return 6
    close = history["Close"]
    ma25 = close.rolling(25).mean().iloc[-1]
    ma75 = close.rolling(75).mean().iloc[-1]
    price = close.iloc[-1]
    if price > ma25 and ma25 > ma75:
        return 20
    if price > ma25:
        return 12
    if price < ma25 and ma25 < ma75:
        return 0
    return 6


def score_rsi(rsi_value) -> int:
    if rsi_value is None:
        return 8
    if rsi_value <= 30:
        return 15
    if rsi_value <= 39:
        return 10
    if rsi_value <= 60:
        return 8
    if rsi_value <= 69:
        return 4
    return 0


def score_macd(recent_cross: bool, macd_above: bool) -> int:
    if recent_cross and macd_above:
        return 15
    if not recent_cross and macd_above:
        return 8
    if recent_cross and not macd_above:
        return 0
    return 3


def _calc_macd_state(history: pd.DataFrame):
    if len(history) < 35:
        return False, False
    close = history["Close"]
    macd_line = ta.trend.MACD(close, window_slow=26, window_fast=12, window_sign=9).macd()
    signal_line = ta.trend.MACD(close, window_slow=26, window_fast=12, window_sign=9).macd_signal()
    if macd_line is None or macd_line.empty:
        return False, False
    macd_above = macd_line.iloc[-1] > signal_line.iloc[-1]
    recent_cross = False
    for i in range(1, 4):
        if i >= len(macd_line):
            break
        if (macd_line.iloc[-i] > signal_line.iloc[-i] and
                macd_line.iloc[-(i + 1)] <= signal_line.iloc[-(i + 1)]):
            recent_cross = True
            break
    return recent_cross, macd_above


def calc_technical_score(history: pd.DataFrame) -> dict:
    """テクニカルスコアを計算して返す。

    Returns:
        dict: technical_score (0-50), ma_score, rsi_score, macd_score
    """
    ma_s = score_ma(history)

    rsi_val = None
    if len(history) >= 14:
        rsi_series = ta.momentum.RSIIndicator(history["Close"], window=14).rsi()
        if rsi_series is not None and not rsi_series.empty:
            val = rsi_series.iloc[-1]
            if not pd.isna(val):
                rsi_val = val
    rsi_s = score_rsi(rsi_val)

    recent_cross, macd_above = _calc_macd_state(history)
    macd_s = score_macd(recent_cross, macd_above)

    return {
        "technical_score": float(ma_s + rsi_s + macd_s),
        "ma_score": float(ma_s),
        "rsi_score": float(rsi_s),
        "macd_score": float(macd_s),
    }
