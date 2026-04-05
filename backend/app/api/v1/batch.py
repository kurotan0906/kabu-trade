"""バッチスコアリング API"""

import asyncio
import logging
from fastapi import APIRouter, HTTPException
from app.core.redis_client import get_redis
from app.services.scoring_service import run_batch_scoring_sync, get_batch_status

logger = logging.getLogger(__name__)
router = APIRouter()

_running = False


@router.post("/scoring/run", status_code=202)
async def trigger_batch_scoring():
    """バッチスコアリングを手動トリガーする（非同期で開始して即返す）"""
    global _running
    if _running:
        raise HTTPException(status_code=409, detail="バッチスコアリングは既に実行中です")

    _running = True

    async def _run():
        global _running
        try:
            import redis as sync_redis_lib
            from app.core.config import settings
            sync_redis = sync_redis_lib.from_url(settings.REDIS_URL, decode_responses=True)
            loop = asyncio.get_event_loop()
            await loop.run_in_executor(None, run_batch_scoring_sync, sync_redis)
        except Exception as e:
            logger.error("バッチスコアリングエラー: %s", e)
        finally:
            _running = False

    asyncio.create_task(_run())
    return {"message": "バッチスコアリングを開始しました", "status": "accepted"}


@router.get("/scoring/status")
async def get_scoring_status():
    """バッチスコアリングの現在の進捗を返す"""
    redis = await get_redis()
    return await get_batch_status(redis)
