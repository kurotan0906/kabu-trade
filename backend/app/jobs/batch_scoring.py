"""Cloud Run Jobs 用バッチスコアリングエントリポイント

使用例:
    python -m app.jobs.batch_scoring

Cloud Run Jobs は HTTP リクエストを介さず直接プロセスを起動するため、
Service のライフサイクル（リデプロイ、アイドル終了）の影響を受けない。
"""

import logging
import sys

import redis as sync_redis_lib

from app.core.config import settings
from app.core.logging import setup_logging
from app.services.scoring_service import run_batch_scoring_sync


def main() -> int:
    setup_logging()
    logger = logging.getLogger(__name__)
    logger.info("Cloud Run Job: バッチスコアリング開始")

    sync_redis = sync_redis_lib.from_url(settings.REDIS_URL, decode_responses=True)
    try:
        result = run_batch_scoring_sync(sync_redis)
        logger.info("Cloud Run Job: 完了 %s", result)
        return 0
    except Exception as e:
        logger.exception("Cloud Run Job: 失敗 - %s", e)
        return 1


if __name__ == "__main__":
    sys.exit(main())
