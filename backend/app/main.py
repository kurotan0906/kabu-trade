"""FastAPI application entry point"""

from contextlib import asynccontextmanager
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from app.core.config import settings
from app.core.logging import setup_logging
from app.core.exceptions import KabuTradeException
from app.core.redis_client import get_redis, close_redis

# ロギング設定
setup_logging()


@asynccontextmanager
async def lifespan(app: FastAPI):
    """アプリケーションのライフサイクル管理"""
    # 起動時
    await get_redis()  # Redis接続を初期化
    yield
    # 終了時
    await close_redis()  # Redis接続を閉じる

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
from app.api.v1 import stocks, evaluations

app.include_router(stocks.router, prefix="/api/v1/stocks", tags=["stocks"])
app.include_router(evaluations.router, prefix="/api/v1/evaluations", tags=["evaluations"])

# 将来の拡張用
# from app.api.v1 import strategies
# app.include_router(strategies.router, prefix="/api/v1/strategies", tags=["strategies"])
