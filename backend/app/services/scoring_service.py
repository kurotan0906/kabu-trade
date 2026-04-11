"""バッチスコアリングサービス

JPX 全銘柄を取得してスコアリングし、stock_scores テーブルに保存する。
データ源は settings.SCORING_DATA_SOURCE で切り替え可能:
    - "hybrid"   : yfinance の history + info を TradingView の指標で上書き（既定）
    - "tv"       : TradingView のみ（history 不要の簡易スコア）
    - "yfinance" : 従来動作

進捗は Redis の batch:scoring:status キーに JSON で保存する。
"""

import json
import logging
import time
from datetime import datetime, timezone
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import Optional

logger = logging.getLogger(__name__)

BATCH_REDIS_KEY = "batch:scoring:status"
# tradingview-ta のレート制限を避けるためデフォルトは控えめ。設定で上書き可能。
DEFAULT_MAX_WORKERS = 4
RETRY_BACKOFF_SECONDS = (1.0, 3.0)  # 1 回リトライ時の待機


def _fetch_merged_data(symbol: str, source: str) -> Optional[dict]:
    """設定に応じて TV / yfinance / hybrid でデータを取得する。

    Returns:
        {"info": dict, "history": pd.DataFrame | None, "recommendation": str | None}
        または None（全ソース失敗）
    """
    from app.external.yfinance_client import fetch_stock_data
    from app.external.tradingview_ta_client import fetch_stock_data_tv, merge_info

    if source == "yfinance":
        base = fetch_stock_data(symbol)
        if base is None:
            return None
        return {"info": base.get("info") or {}, "history": base.get("history"), "recommendation": None}

    if source == "tv":
        tv = fetch_stock_data_tv(symbol)
        if tv is None:
            return None
        return {"info": tv.get("info") or {}, "history": None, "recommendation": tv.get("recommendation")}

    # hybrid
    base = fetch_stock_data(symbol)
    tv = fetch_stock_data_tv(symbol)
    if base is None and tv is None:
        return None
    base_info = (base or {}).get("info") or {}
    tv_info = (tv or {}).get("info") or {}
    return {
        "info": merge_info(base_info, tv_info),
        "history": (base or {}).get("history"),
        "recommendation": (tv or {}).get("recommendation"),
    }


def _score_symbol(symbol: str, name: Optional[str], sector: Optional[str], source: str) -> Optional[dict]:
    """1銘柄をスコアリングして dict を返す。失敗時は None。（同期関数）"""
    from app.analyzer.fundamental import calc_fundamental_score
    from app.analyzer.technical import calc_technical_score
    from app.analyzer.kurotenko_screener import evaluate_candidate
    from app.analyzer.scorer import build_stock_result

    data = _fetch_merged_data(symbol, source)
    if data is None:
        return None
    try:
        fundamental = calc_fundamental_score(data["info"])
        if data.get("history") is not None:
            technical = calc_technical_score(data["history"])
        else:
            # TV のみモード: history がない → 技術スコアは中立値で埋める
            technical = {"technical_score": 24.0, "ma_score": 6.0, "rsi_score": 8.0, "macd_score": 3.0}
        kurotenko = evaluate_candidate(symbol)
        result = build_stock_result(symbol, name, sector, fundamental, technical, kurotenko)
        # TV の総合推奨はメタとして保持したいが、StockScore モデル未対応のため捨てる（将来拡張）
        return result
    except Exception as e:
        logger.error("%s: スコアリング失敗 - %s", symbol, e)
        return None


def _score_symbol_with_retry(symbol: str, name: Optional[str], sector: Optional[str], source: str) -> Optional[dict]:
    """1 回の指数バックオフリトライ付き"""
    result = _score_symbol(symbol, name, sector, source)
    if result is not None:
        return result
    time.sleep(RETRY_BACKOFF_SECONDS[0])
    result = _score_symbol(symbol, name, sector, source)
    if result is not None:
        return result
    time.sleep(RETRY_BACKOFF_SECONDS[1])
    return None


def run_batch_scoring_sync(redis_client) -> dict:
    """バッチスコアリングを同期で実行する（ThreadPoolExecutor 内で呼ぶ）。

    Returns:
        {"processed": int, "failed": int, "total": int}
    """
    from sqlalchemy import create_engine
    from sqlalchemy.orm import Session
    from app.core.config import settings
    from app.external.yfinance_client import load_jpx_symbols
    from app.models.stock_score import StockScore

    source = settings.SCORING_DATA_SOURCE
    max_workers = settings.SCORING_MAX_WORKERS or DEFAULT_MAX_WORKERS

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

    started_at = datetime.now(timezone.utc).isoformat()
    _set_status(redis_client, "running", total=total, processed=0, failed=0, started_at=started_at)
    logger.info("バッチスコアリング開始: %d 銘柄 / source=%s / workers=%d", total, source, max_workers)

    symbol_map = {row["symbol"]: row for row in symbols_data}

    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        futures = {
            executor.submit(_score_symbol_with_retry, row["symbol"], row["name"], row["market"], source): row["symbol"]
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
                    _set_status(redis_client, "running", total=total, processed=processed, failed=failed, started_at=started_at)
                    logger.info("進捗: %d/%d (失敗: %d)", processed + failed, total, failed)

            session.commit()

    _set_status(redis_client, "done", total=total, processed=processed, failed=failed, started_at=started_at, finished=True)
    logger.info("バッチスコアリング完了: 成功 %d / 失敗 %d", processed, failed)
    return {"processed": processed, "failed": failed, "total": total}


def _set_status(redis_client, status: str, total: int = 0, processed: int = 0, failed: int = 0, started_at: Optional[str] = None, finished: bool = False):
    """Redis に進捗を書き込む（同期版）"""
    data = {
        "status": status,
        "total": total,
        "processed": processed,
        "failed": failed,
        "started_at": started_at,
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
