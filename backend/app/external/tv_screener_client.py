"""TradingView Screener 一括取得クライアント。

tradingview-screener パッケージ経由で market=japan の断面データを 1 回のクエリで取得する。
MCP と同一の HTTP API を叩くため、MCP で検証したフィルタ/カラムがそのまま使える。
"""
from __future__ import annotations

import logging
from typing import Any

from tradingview_screener import Query, col

logger = logging.getLogger(__name__)

TV_SCREENER_COLUMNS: list[str] = [
    # メタ
    "name", "description", "sector", "exchange", "currency",
    # 価格・出来高
    "close", "volume", "market_cap_basic", "average_volume_10d_calc",
    # ファンダメンタル（yfinance info 互換マッピング元）
    "price_earnings_ttm",
    "price_book_ratio", "price_book_fq",
    "return_on_equity",
    "dividend_yield_recent",
    "total_revenue_yoy_growth_fy",
    # テクニカル（technical.py と同じ指標）
    "RSI",
    "MACD.macd", "MACD.signal",
    "SMA25", "SMA75",
    # TV 総合レーティング（メタ・将来利用）
    "Recommend.All",
]


def _tv_to_symbol(ticker: str) -> str | None:
    """TV 形式 ('TSE:7203') を DB 形式 ('7203.T') に変換。TSE 以外は None。"""
    if not ticker or ":" not in ticker:
        return None
    exchange, code = ticker.split(":", 1)
    if exchange != "TSE":
        return None
    return f"{code}.T"


def fetch_japan_market_snapshot() -> dict[str, dict[str, Any]]:
    """日本市場の株式断面を取得。

    Returns:
        dict[symbol, row]: key は `{code}.T`、value は TV の各カラム値 dict。
        TSE 以外（NAG/FSE/SSE）と `type != 'stock'` は除外。
    """
    n, df = (
        Query()
        .set_markets("japan")
        .select(*TV_SCREENER_COLUMNS)
        .where(col("type") == "stock")
        .limit(5000)
        .get_scanner_data()
    )
    logger.info("tv_screener snapshot: total=%s rows_in_df=%s", n, len(df))

    result: dict[str, dict[str, Any]] = {}
    for record in df.to_dict(orient="records"):
        symbol = _tv_to_symbol(record.get("ticker", ""))
        if symbol is None:
            continue
        result[symbol] = record
    return result
