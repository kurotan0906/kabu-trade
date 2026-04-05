"""TradingView シグナル API"""

from typing import List

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, desc, func

from app.core.database import get_db
from app.models.tradingview_signal import TradingViewSignal
from app.schemas.tradingview_signal import TradingViewSignalCreate, TradingViewSignalResponse

router = APIRouter()


@router.post("/{symbol}", response_model=TradingViewSignalResponse, status_code=201)
async def create_signal(
    symbol: str,
    payload: TradingViewSignalCreate,
    db: AsyncSession = Depends(get_db),
):
    """TradingView 分析結果を保存（Claude が MCP 呼び出し後に POST する）"""
    data = payload.model_dump()
    data["symbol"] = symbol
    signal = TradingViewSignal(**data)
    db.add(signal)
    await db.commit()
    await db.refresh(signal)
    return signal


@router.get("/{symbol}", response_model=TradingViewSignalResponse)
async def get_signal(symbol: str, db: AsyncSession = Depends(get_db)):
    """銘柄の最新 TradingView シグナルを返す"""
    stmt = (
        select(TradingViewSignal)
        .where(TradingViewSignal.symbol == symbol)
        .order_by(desc(TradingViewSignal.updated_at))
        .limit(1)
    )
    result = await db.execute(stmt)
    signal = result.scalar_one_or_none()
    if not signal:
        raise HTTPException(status_code=404, detail=f"銘柄 {symbol} の TradingView シグナルが見つかりません")
    return signal


@router.get("", response_model=List[TradingViewSignalResponse])
async def list_signals(db: AsyncSession = Depends(get_db)):
    """全銘柄の最新 TradingView シグナル一覧（ランキングページ用）"""
    subq = (
        select(TradingViewSignal.symbol, func.max(TradingViewSignal.updated_at).label("latest"))
        .group_by(TradingViewSignal.symbol)
        .subquery()
    )
    stmt = (
        select(TradingViewSignal)
        .join(
            subq,
            (TradingViewSignal.symbol == subq.c.symbol)
            & (TradingViewSignal.updated_at == subq.c.latest),
        )
        .order_by(desc(TradingViewSignal.updated_at))
    )
    result = await db.execute(stmt)
    return result.scalars().all()
