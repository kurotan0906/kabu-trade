"""TradingView シグナルサービス"""

from typing import List, Optional

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, desc, func

from app.models.tradingview_signal import TradingViewSignal
from app.schemas.tradingview_signal import TradingViewSignalCreate


async def create_signal(
    db: AsyncSession,
    symbol: str,
    payload: TradingViewSignalCreate,
) -> TradingViewSignal:
    """TradingView 分析結果を保存して返す。"""
    data = payload.model_dump()
    data["symbol"] = symbol
    signal = TradingViewSignal(**data)
    db.add(signal)
    await db.commit()
    await db.refresh(signal)
    return signal


async def get_signal(db: AsyncSession, symbol: str) -> Optional[TradingViewSignal]:
    """銘柄の最新 TradingView シグナルを返す。存在しない場合は None。"""
    stmt = (
        select(TradingViewSignal)
        .where(TradingViewSignal.symbol == symbol)
        .order_by(desc(TradingViewSignal.updated_at))
        .limit(1)
    )
    result = await db.execute(stmt)
    return result.scalar_one_or_none()


async def list_signals(db: AsyncSession) -> List[TradingViewSignal]:
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
    return list(result.scalars().all())
