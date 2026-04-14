"""バッチスコアリング API

スコアリング本体は Cloud Run Jobs で実行する。Service の役割は:
    - /scoring/run   : Cloud Run Job をトリガする
    - /scoring/status: Redis から進捗を返す（Job 側が更新する）
    - /scoring/reset : Redis のステータスとチェックポイントをリセット

GCP_PROJECT_ID が未設定のローカル開発では、同プロセス内で直接実行する
フォールバック経路を残す（従来動作との互換）。
"""

import asyncio
import logging

import requests
from fastapi import APIRouter, HTTPException

from app.core.config import settings
from app.core.redis_client import get_redis
from app.services.scoring_service import (
    CHECKPOINT_REDIS_KEY,
    KUROTENKO_CACHE_KEY_FMT,
    run_batch_scoring_sync,
    get_batch_status,
)

logger = logging.getLogger(__name__)
router = APIRouter()

# ローカルフォールバック実行の二重起動防止
_running = False


def _trigger_cloud_run_job() -> dict:
    """Cloud Run Jobs の Run API を呼び出してバッチジョブを起動する。

    Cloud Run 上では ADC (Application Default Credentials) が自動で利用でき、
    サービスアカウント `1061707373577-compute@...` に `roles/run.invoker` を
    付与しておけば追加設定なしで起動できる。
    """
    try:
        from google.auth import default as google_auth_default
        from google.auth.transport.requests import Request as GoogleAuthRequest
    except ImportError as e:
        raise HTTPException(
            status_code=500,
            detail=f"google-auth が未インストールです: {e}",
        )

    project = settings.GCP_PROJECT_ID
    region = settings.GCP_REGION
    job_name = settings.CLOUD_RUN_BATCH_JOB_NAME

    credentials, _ = google_auth_default(scopes=["https://www.googleapis.com/auth/cloud-platform"])
    credentials.refresh(GoogleAuthRequest())
    token = credentials.token

    url = (
        f"https://run.googleapis.com/v2/projects/{project}"
        f"/locations/{region}/jobs/{job_name}:run"
    )
    resp = requests.post(
        url,
        headers={"Authorization": f"Bearer {token}", "Content-Type": "application/json"},
        json={},
        timeout=30,
    )
    if resp.status_code >= 400:
        logger.error("Cloud Run Job 起動失敗: %s %s", resp.status_code, resp.text)
        raise HTTPException(
            status_code=502,
            detail=f"Cloud Run Job 起動失敗 ({resp.status_code}): {resp.text}",
        )
    return resp.json()


@router.post("/scoring/run", status_code=202)
async def trigger_batch_scoring():
    """バッチスコアリングを開始する。

    本番（GCP_PROJECT_ID 設定済み）では Cloud Run Job を起動し、即座に 202 を返す。
    ローカル開発では同プロセス内で実行する。
    """
    # 本番: Cloud Run Jobs を起動
    if settings.GCP_PROJECT_ID:
        logger.info("Cloud Run Job を起動します: %s", settings.CLOUD_RUN_BATCH_JOB_NAME)
        loop = asyncio.get_event_loop()
        result = await loop.run_in_executor(None, _trigger_cloud_run_job)
        return {
            "message": "バッチスコアリングを Cloud Run Jobs で開始しました",
            "status": "accepted",
            "operation": result.get("name"),
        }

    # ローカル開発フォールバック（従来動作）
    global _running
    if _running:
        raise HTTPException(status_code=409, detail="バッチスコアリングは既に実行中です")
    _running = True

    async def _run():
        global _running
        try:
            import redis as sync_redis_lib
            sync_redis = sync_redis_lib.from_url(settings.REDIS_URL, decode_responses=True)
            loop = asyncio.get_event_loop()
            await loop.run_in_executor(None, run_batch_scoring_sync, sync_redis)
        except Exception as e:
            logger.error("バッチスコアリングエラー: %s", e)
        finally:
            _running = False

    asyncio.create_task(_run())
    return {"message": "バッチスコアリングをローカルで開始しました", "status": "accepted"}


@router.get("/scoring/status")
async def get_scoring_status():
    """バッチスコアリングの現在の進捗を返す"""
    redis = await get_redis()
    return await get_batch_status(redis)


@router.post("/scoring/reset", status_code=200)
async def reset_batch_status():
    """バッチスコアリングのステータス、チェックポイント、および
    kurotenko 評価キャッシュをリセットする。

    kurotenko キャッシュを残したままリセットすると
    「本当にやり直したい」場合に財務データが古いまま使われてしまうため、
    reset ではキャッシュも SCAN で一括削除する。
    """
    global _running
    redis = await get_redis()
    await redis.delete("batch:scoring:status")
    await redis.delete(CHECKPOINT_REDIS_KEY)

    # kurotenko:v1:* を SCAN で列挙して一括削除
    pattern = KUROTENKO_CACHE_KEY_FMT.format(symbol="*")
    deleted = 0
    try:
        async for key in redis.scan_iter(match=pattern, count=500):
            await redis.delete(key)
            deleted += 1
    except Exception as e:
        logger.warning("kurotenko キャッシュ削除失敗: %s", e)

    _running = False
    return {
        "message": "バッチステータス、チェックポイント、kurotenko キャッシュをリセットしました",
        "kurotenko_cache_deleted": deleted,
    }
