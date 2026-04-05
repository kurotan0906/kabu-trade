"""バッチスコアリングサービス

JPX 全銘柄を yfinance で取得してスコアリングし、stock_scores テーブルに保存する。
進捗は Redis の batch:scoring:status キーに JSON で保存する。
"""

import json
import logging
from datetime import datetime, timezone
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import Optional

logger = logging.getLogger(__name__)

BATCH_REDIS_KEY = "batch:scoring:status"
MAX_WORKERS = 10


def _score_symbol(symbol: str, name: Optional[str], sector: Optional[str]) -> Optional[dict]:
    """1銘柄をスコアリングして dict を返す。失敗時は None。（同期関数）"""
    from app.external.yfinance_client import fetch_stock_data
    from app.analyzer.fundamental import calc_fundamental_score
    from app.analyzer.technical import calc_technical_score
    from app.analyzer.kurotenko_screener import evaluate_candidate
    from app.analyzer.scorer import build_stock_result

    data = fetch_stock_data(symbol)
    if data is None:
        return None
    try:
        fundamental = calc_fundamental_score(data["info"])
        technical = calc_technical_score(data["history"])
        kurotenko = evaluate_candidate(symbol)
        return build_stock_result(symbol, name, sector, fundamental, technical, kurotenko)
    except Exception as e:
        logger.error("%s: スコアリング失敗 - %s", symbol, e)
        return None


def run_batch_scoring_sync(redis_client) -> dict:
    """バッチスコアリングを同期で実行する（ThreadPoolExecutor 内で呼ぶ）。

    Args:
        redis_client: sync redis client

    Returns:
        {"processed": int, "failed": int, "total": int}
    """
    from sqlalchemy import create_engine
    from sqlalchemy.orm import Session
    from app.core.config import settings
    from app.external.yfinance_client import load_jpx_symbols
    from app.models.stock_score import StockScore

    sync_url = settings.DATABASE_URL.replace("+asyncpg", "+psycopg2")
    engine = create_engine(sync_url)

    logger.info("JPX 銘柄マスターを取得中...")
    try:
        symbols_data = load_jpx_symbols()
    except Exception as e:
        logger.error("JPX銘柄マスター取得失敗: %s", e)
        return {"processed": 0, "failed": 0, "total": 0}

    total = len(symbols_data)
    processed = 0
    failed = 0

    _set_status(redis_client, "running", total=total, processed=0, failed=0)
    logger.info("バッチスコアリング開始: %d 銘柄", total)

    symbol_map = {row["symbol"]: row for row in symbols_data}

    with ThreadPoolExecutor(max_workers=MAX_WORKERS) as executor:
        futures = {
            executor.submit(_score_symbol, row["symbol"], row["name"], row["market"]): row["symbol"]
            for row in symbols_data
        }
        with Session(engine) as session:
            for future in as_completed(futures):
                sym = futures[future]
                try:
                    result = future.result()
                except Exception as e:
                    logger.error("%s: 予期せぬエラー - %s", sym, e)
                    result = None

                if result is not None:
                    session.add(StockScore(**result))
                    processed += 1
                else:
                    session.add(StockScore(
                        symbol=sym,
                        name=symbol_map[sym]["name"],
                        data_quality="fetch_error",
                    ))
                    failed += 1

                if (processed + failed) % 100 == 0:
                    session.commit()
                    _set_status(redis_client, "running", total=total, processed=processed, failed=failed)
                    logger.info("進捗: %d/%d (失敗: %d)", processed + failed, total, failed)

            session.commit()

    _set_status(redis_client, "done", total=total, processed=processed, failed=failed, finished=True)
    logger.info("バッチスコアリング完了: 成功 %d / 失敗 %d", processed, failed)
    return {"processed": processed, "failed": failed, "total": total}


def _set_status(redis_client, status: str, total: int = 0, processed: int = 0, failed: int = 0, finished: bool = False):
    """Redis に進捗を書き込む（同期版）"""
    data = {
        "status": status,
        "total": total,
        "processed": processed,
        "failed": failed,
        "started_at": datetime.now(timezone.utc).isoformat(),
        "finished_at": datetime.now(timezone.utc).isoformat() if finished else None,
    }
    try:
        redis_client.set(BATCH_REDIS_KEY, json.dumps(data))
    except Exception as e:
        logger.warning("Redis 書き込み失敗: %s", e)


async def get_batch_status(redis_client) -> dict:
    """Redis から現在のバッチ進捗を取得する（非同期版）。"""
    try:
        raw = await redis_client.get(BATCH_REDIS_KEY)
        if raw:
            return json.loads(raw)
    except Exception:
        pass
    return {"status": "idle", "total": 0, "processed": 0, "failed": 0, "started_at": None, "finished_at": None}
