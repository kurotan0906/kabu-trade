"""
スコア上位100銘柄の TradingView テクニカル分析を一括取得して DB に保存するスクリプト
"""

import asyncio
import json
import logging
import time
import requests
from sqlalchemy import text
from app.core.database import engine
from app.models.tradingview_signal import TradingViewSignal
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import sessionmaker

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
logger = logging.getLogger(__name__)

TV_SCAN_URL = "https://scanner.tradingview.com/japan/scan"

TV_COLUMNS = [
    "Recommend.All",
    "Recommend.MA",
    "Recommend.Other",
    "RSI",
    "MACD.macd",
    "MACD.signal",
    "BB.upper",
    "BB.lower",
    "SMA20",
    "EMA50",
    "EMA200",
    "ADX",
    "Stoch.K",
    "Stoch.D",
]

HEADERS = {
    "User-Agent": "Mozilla/5.0",
    "Content-Type": "application/json",
}


def recommend_to_label(val: float) -> str:
    if val is None:
        return "NEUTRAL"
    if val >= 0.5:
        return "STRONG_BUY"
    if val >= 0.1:
        return "BUY"
    if val <= -0.5:
        return "STRONG_SELL"
    if val <= -0.1:
        return "SELL"
    return "NEUTRAL"


def recommend_to_score(val: float) -> float:
    """Recommend.All (-1〜+1) を 0〜100 に変換"""
    if val is None:
        return 50.0
    return round((val + 1) / 2 * 100, 2)


def fetch_tv_batch(symbols: list[str]) -> dict[str, dict]:
    """TradingView screener API で一括取得。symbols は銘柄コードのみ（.T なし）"""
    tickers = [f"TSE:{s}" for s in symbols]
    payload = {
        "symbols": {"tickers": tickers},
        "columns": TV_COLUMNS,
    }
    try:
        resp = requests.post(TV_SCAN_URL, json=payload, headers=HEADERS, timeout=30)
        resp.raise_for_status()
        data = resp.json()
    except Exception as e:
        logger.error("TradingView API エラー: %s", e)
        return {}

    result = {}
    for item in data.get("data", []):
        ticker = item.get("s", "")  # e.g. "TSE:1301"
        values = item.get("d", [])
        if not ticker:
            continue
        code = ticker.split(":")[-1]  # "1301"
        row = dict(zip(TV_COLUMNS, values))
        result[code] = row

    return result


async def get_top100_symbols() -> list[str]:
    async with engine.connect() as conn:
        result = await conn.execute(text("""
            WITH latest AS (
                SELECT symbol, MAX(scored_at) as latest_at
                FROM stock_scores
                GROUP BY symbol
            )
            SELECT s.symbol
            FROM stock_scores s
            JOIN latest l ON s.symbol = l.symbol AND s.scored_at = l.latest_at
            WHERE s.data_quality != 'fetch_error'
              AND s.total_score IS NOT NULL
            ORDER BY s.total_score DESC
            LIMIT 100
        """))
        return [row[0] for row in result]


async def save_signals(signals: list[dict]):
    async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    async with async_session() as session:
        for sig in signals:
            obj = TradingViewSignal(**sig)
            session.add(obj)
        await session.commit()
    logger.info("DB に %d 件保存しました", len(signals))


async def main():
    # 1. 上位100銘柄取得
    symbols_with_t = await get_top100_symbols()
    # symbol は "1301.T" 形式 → コードのみにする
    symbols = [s.replace(".T", "") for s in symbols_with_t]
    symbol_map = {s.replace(".T", ""): s for s in symbols_with_t}  # code -> "code.T"
    logger.info("対象銘柄数: %d", len(symbols))

    # 2. TradingView から一括取得（50件ずつ）
    all_tv_data = {}
    batch_size = 50
    for i in range(0, len(symbols), batch_size):
        batch = symbols[i:i + batch_size]
        logger.info("TradingView 取得中: %d〜%d", i + 1, i + len(batch))
        tv_data = fetch_tv_batch(batch)
        all_tv_data.update(tv_data)
        if i + batch_size < len(symbols):
            time.sleep(1)  # レート制限対策

    logger.info("TradingView から取得できた銘柄数: %d / %d", len(all_tv_data), len(symbols))

    # 3. シグナルオブジェクト構築
    signals = []
    for code in symbols:
        symbol_t = symbol_map[code]  # "1301.T"
        tv = all_tv_data.get(code)
        if tv is None:
            logger.warning("取得できなかった銘柄: %s", code)
            continue

        rec_val = tv.get("Recommend.All")
        ma_val = tv.get("Recommend.MA")
        osc_val = tv.get("Recommend.Other")

        signals.append({
            "symbol": symbol_t,
            "recommendation": recommend_to_label(rec_val),
            "score": recommend_to_score(rec_val),
            "buy_count": None,
            "sell_count": None,
            "neutral_count": None,
            "ma_recommendation": recommend_to_label(ma_val) if ma_val is not None else None,
            "osc_recommendation": recommend_to_label(osc_val) if osc_val is not None else None,
            "details": {k: v for k, v in tv.items()},
        })

    logger.info("保存対象シグナル数: %d", len(signals))

    # 4. DB 保存
    await save_signals(signals)

    # 5. サマリー表示
    from collections import Counter
    recs = Counter(s["recommendation"] for s in signals)
    logger.info("推奨分布: %s", dict(recs))


if __name__ == "__main__":
    asyncio.run(main())
