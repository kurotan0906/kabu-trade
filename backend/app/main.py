"""FastAPI application entry point"""

from contextlib import asynccontextmanager
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from app.core.config import settings
from app.core.logging import setup_logging
from app.core.exceptions import KabuTradeException
from app.core.redis_client import get_redis, close_redis
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger
import pytz

_scheduler = BackgroundScheduler(timezone=pytz.timezone("Asia/Tokyo"))


def _scheduled_batch():
    """APScheduler から呼ばれるバッチ実行（同期）"""
    import redis as sync_redis_lib
    from app.core.config import settings
    from app.services.scoring_service import run_batch_scoring_sync
    sync_redis = sync_redis_lib.from_url(settings.REDIS_URL, decode_responses=True)
    run_batch_scoring_sync(sync_redis)


# ロギング設定
setup_logging()


@asynccontextmanager
async def lifespan(app: FastAPI):
    """アプリケーションのライフサイクル管理"""
    # 起動時
    try:
        await get_redis()  # Redis接続を初期化
    except Exception as e:
        # Redis接続エラーを無視（データベースなしモード）
        print(f"⚠ Redis接続エラー（無視）: {e}")
    _scheduler.add_job(_scheduled_batch, CronTrigger(hour=18, minute=0))
    _scheduler.start()
    yield
    # 終了時
    _scheduler.shutdown(wait=False)
    try:
        await close_redis()  # Redis接続を閉じる
    except Exception:
        pass

# FastAPIアプリケーションの作成
app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    description="株取引支援システム - 個人の投資効率化のためのAPI",
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan,
)

# CORS設定
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# グローバルエラーハンドラー
@app.exception_handler(KabuTradeException)
async def kabu_trade_exception_handler(request: Request, exc: KabuTradeException):
    """カスタム例外のハンドラー"""
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "error": {
                "code": exc.error_code or "UNKNOWN_ERROR",
                "message": exc.detail,
                "details": {},
            }
        },
    )


@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "message": "Kabu Trade API",
        "version": settings.APP_VERSION,
        "status": "running",
    }


@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy"}


# APIルーターのインポート
from app.api.v1 import stocks

app.include_router(stocks.router, prefix="/api/v1/stocks", tags=["stocks"])

# 評価機能（Phase 2）- pandas_taがインストールされている場合のみ
try:
    from app.api.v1 import evaluations
    app.include_router(evaluations.router, prefix="/api/v1/evaluations", tags=["evaluations"])
except ImportError:
    # pandas_taがインストールされていない場合は評価機能をスキップ
    pass

# チャート分析機能
from app.api.v1 import chart_analysis
app.include_router(chart_analysis.router, prefix="/api/v1/chart-analysis", tags=["chart-analysis"])

# バッチスコアリング機能
from app.api.v1 import batch
app.include_router(batch.router, prefix="/api/v1/batch", tags=["batch"])

# スコアAPI
from app.api.v1 import scores
app.include_router(scores.router, prefix="/api/v1/scores", tags=["scores"])

# TradingView シグナル API
from app.api.v1 import tradingview_signals
app.include_router(tradingview_signals.router, prefix="/api/v1/tradingview-signals", tags=["tradingview-signals"])

# ポートフォリオ API
from app.api.v1 import portfolio
app.include_router(portfolio.router, prefix="/api/v1/portfolio", tags=["portfolio"])

# 将来価値シミュレータ API
from app.api.v1 import advisor
app.include_router(advisor.router, prefix="/api/v1/advisor", tags=["advisor"])

# 将来の拡張用
# from app.api.v1 import strategies
# app.include_router(strategies.router, prefix="/api/v1/strategies", tags=["strategies"])
