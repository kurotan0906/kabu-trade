"""スコアAPI"""

from typing import List

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.schemas.stock_score import StockScoreResponse, AnalysisAxesResponse
from app.services import score_service
from app.services.analysis_axes_service import get_analysis_axes

router = APIRouter()


@router.get("", response_model=List[StockScoreResponse])
async def list_scores(
    sort: str = Query("total_score", description="ソートカラム"),
    limit: int = Query(100, ge=1, le=500),
    db: AsyncSession = Depends(get_db),
):
    """全銘柄スコア一覧（最新スコアのみ、指定軸で降順ソート）"""
    return await score_service.list_scores(db, sort=sort, limit=limit)


@router.get("/{symbol}", response_model=StockScoreResponse)
async def get_score(symbol: str, db: AsyncSession = Depends(get_db)):
    """銘柄の最新スコアを返す"""
    score = await score_service.get_score(db, symbol)
    if not score:
        raise HTTPException(status_code=404, detail=f"銘柄 {symbol} のスコアが見つかりません")
    return score


@router.get("/{symbol}/axes", response_model=AnalysisAxesResponse)
async def get_axes(symbol: str, db: AsyncSession = Depends(get_db)):
    """銘柄の全分析軸集約を返す"""
    return await get_analysis_axes(symbol, db)
