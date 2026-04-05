"""スコアAPI"""

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, desc, func

from app.core.database import get_db
from app.models.stock_score import StockScore
from app.schemas.stock_score import StockScoreResponse, AnalysisAxesResponse
from app.services.analysis_axes_service import get_analysis_axes

router = APIRouter()


@router.get("", response_model=list)
async def list_scores(
    sort: str = Query("total_score", description="ソートカラム"),
    limit: int = Query(100, ge=1, le=500),
    db: AsyncSession = Depends(get_db),
):
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
    return result.scalars().all()


@router.get("/{symbol}", response_model=StockScoreResponse)
async def get_score(symbol: str, db: AsyncSession = Depends(get_db)):
    """銘柄の最新スコアを返す"""
    stmt = (
        select(StockScore)
        .where(StockScore.symbol == symbol)
        .order_by(desc(StockScore.scored_at))
        .limit(1)
    )
    result = await db.execute(stmt)
    score = result.scalar_one_or_none()
    if not score:
        raise HTTPException(status_code=404, detail=f"銘柄 {symbol} のスコアが見つかりません")
    return score


@router.get("/{symbol}/axes", response_model=AnalysisAxesResponse)
async def get_axes(symbol: str, db: AsyncSession = Depends(get_db)):
    """銘柄の全分析軸集約を返す"""
    return await get_analysis_axes(symbol, db)
