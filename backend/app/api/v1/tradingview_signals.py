"""TradingView シグナル API"""

from typing import List

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.schemas.tradingview_signal import TradingViewSignalCreate, TradingViewSignalResponse
from app.services import tradingview_signal_service

router = APIRouter()


@router.post("/{symbol}", response_model=TradingViewSignalResponse, status_code=201)
async def create_signal(
    symbol: str,
    payload: TradingViewSignalCreate,
    db: AsyncSession = Depends(get_db),
):
    """TradingView 分析結果を保存（Claude が MCP 呼び出し後に POST する）"""
    return await tradingview_signal_service.create_signal(db, symbol, payload)


@router.get("/{symbol}", response_model=TradingViewSignalResponse)
async def get_signal(symbol: str, db: AsyncSession = Depends(get_db)):
    """銘柄の最新 TradingView シグナルを返す"""
    signal = await tradingview_signal_service.get_signal(db, symbol)
    if not signal:
        raise HTTPException(status_code=404, detail=f"銘柄 {symbol} の TradingView シグナルが見つかりません")
    return signal


@router.get("", response_model=List[TradingViewSignalResponse])
async def list_signals(db: AsyncSession = Depends(get_db)):
    """全銘柄の最新 TradingView シグナル一覧（ランキングページ用）"""
    return await tradingview_signal_service.list_signals(db)
