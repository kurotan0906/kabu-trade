"""スコアサービス"""

from typing import List, Optional

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, desc, func

from app.models.stock_score import StockScore


async def list_scores(
    db: AsyncSession,
    sort: str = "total_score",
    limit: int = 100,
) -> List[StockScore]:
    """全銘柄スコア一覧（最新スコアのみ、指定軸で降順ソート）"""
    allowed_sorts = {"total_score", "fundamental_score", "technical_score", "kurotenko_score"}
    if sort not in allowed_sorts:
        sort = "total_score"

    subq = (
        select(StockScore.symbol, func.max(StockScore.scored_at).label("latest"))
        .group_by(StockScore.symbol)
        .subquery()
    )
    sort_col = getattr(StockScore, sort)
    stmt = (
        select(StockScore)
        .join(subq, (StockScore.symbol == subq.c.symbol) & (StockScore.scored_at == subq.c.latest))
        .where(StockScore.data_quality != "fetch_error")
        .order_by(desc(sort_col))
        .limit(limit)
    )
    result = await db.execute(stmt)
    return list(result.scalars().all())


async def get_score(db: AsyncSession, symbol: str) -> Optional[StockScore]:
    """銘柄の最新スコアを返す。存在しない場合は None。"""
    stmt = (
        select(StockScore)
        .where(StockScore.symbol == symbol)
        .order_by(desc(StockScore.scored_at))
        .limit(1)
    )
    result = await db.execute(stmt)
    return result.scalar_one_or_none()
