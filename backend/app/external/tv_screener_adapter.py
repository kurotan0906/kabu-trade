"""TV Screener 行データを既存スコアリング関数と互換な形式へ変換する。

- `tv_row_to_info`: yfinance `ticker.info` 互換 dict（calc_fundamental_score 向け）
- `tv_row_to_technical_features`: calc_technical_score_from_tv 向けフィーチャー dict
"""
from __future__ import annotations

from typing import Any


def _safe_float(value: Any) -> float | None:
    """None/NaN/文字列を安全に float に変換。変換不能なら None。"""
    if value is None:
        return None
    try:
        v = float(value)
    except (TypeError, ValueError):
        return None
    if v != v:  # NaN チェック
        return None
    return v


def _percent_to_ratio(value: Any) -> float | None:
    """TV の %単位値（例: 15.0 → 0.15）を小数に変換。None/NaN 安全。"""
    v = _safe_float(value)
    if v is None:
        return None
    return v / 100.0


def tv_row_to_info(row: dict[str, Any]) -> dict[str, Any]:
    """TV row → yfinance ticker.info 互換 dict。

    calc_fundamental_score が期待するキー:
      trailingPE, priceToBook, returnOnEquity, dividendYield, revenueGrowth

    単位系 (yfinance v0.2.40+ の挙動に合わせる):
      - trailingPE, priceToBook: そのまま（ratio 不要）
      - returnOnEquity, revenueGrowth: **ratio** (0.15 = 15%)。TV の percent を /100
      - dividendYield: **percent** (3.06 = 3.06%)。yfinance も percent を返すためそのまま

    NOTE: `score_dividend` のしきい値は 0.04/0.03/0.02 と ratio 前提で書かれており、
    yfinance の percent 出力と不整合で上振れする既知バグがある。本 refactor は
    hybrid 互換を優先するため adapter 側でも percent をそのまま渡す。
    """
    pb = _safe_float(row.get("price_book_ratio"))
    if pb is None:
        pb = _safe_float(row.get("price_book_fq"))

    return {
        "trailingPE": _safe_float(row.get("price_earnings_ttm")),
        "priceToBook": pb,
        "returnOnEquity": _percent_to_ratio(row.get("return_on_equity")),
        "dividendYield": _safe_float(row.get("dividend_yield_recent")),
        "revenueGrowth": _percent_to_ratio(row.get("total_revenue_yoy_growth_fy")),
        "marketCap": _safe_float(row.get("market_cap_basic")),
        "longName": row.get("description") or row.get("name"),
        "sector": row.get("sector"),
    }


def tv_row_to_technical_features(row: dict[str, Any]) -> dict[str, Any]:
    """TV row → calc_technical_score_from_tv 用の値 dict。"""
    return {
        "close": _safe_float(row.get("close")),
        "rsi": _safe_float(row.get("RSI")),
        "macd": _safe_float(row.get("MACD.macd")),
        "macd_signal": _safe_float(row.get("MACD.signal")),
        "sma25": _safe_float(row.get("SMA25")),
        "sma75": _safe_float(row.get("SMA75")),
    }
