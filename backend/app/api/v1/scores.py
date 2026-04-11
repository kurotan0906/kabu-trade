"""スコアAPI"""

from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.schemas.stock_score import StockScoreResponse, AnalysisAxesResponse
from app.services import score_service
from app.services.analysis_axes_service import get_analysis_axes
from app.services.profile_scoring_service import list_scores_with_profile

router = APIRouter()

_VALID_PROFILES = {"growth", "balanced", "income", "auto"}


@router.get("", response_model=List[StockScoreResponse])
async def list_scores(
    sort: str = Query("total_score", description="ソートカラム"),
    limit: int = Query(100, ge=1, le=500),
    profile: Optional[str] = Query(None, description="growth|balanced|income|auto"),
    db: AsyncSession = Depends(get_db),
):
    """全銘柄スコア一覧（最新スコアのみ）。

    profile 指定時はプロファイルに基づいて phase_score を計算し、そのスコアで降順ソートする。
    profile=auto はポートフォリオ進捗率から自動選択（Phase 4 で有効化）。
    """
    if profile is None:
        return await score_service.list_scores(db, sort=sort, limit=limit)

    if profile not in _VALID_PROFILES:
        raise HTTPException(status_code=400, detail=f"profile must be one of {_VALID_PROFILES}")

    # auto の場合、現在のポートフォリオ進捗率を取得する（Phase 3 の portfolio_service 登場後に有効化）
    progress_rate = None
    if profile == "auto":
        try:
            from app.services.portfolio_service import get_progress_rate
            progress_rate = await get_progress_rate(db)
        except ImportError:
            progress_rate = 0.0

    enriched = await list_scores_with_profile(db, profile, limit=limit, progress_rate=progress_rate)

    # StockScoreResponse に profile_* を載せて返す
    out: List[StockScoreResponse] = []
    for item in enriched:
        resp = StockScoreResponse.model_validate(item["score"])
        resp.profile_score = item["profile_score"]
        resp.profile_name = item["profile_name"]
        resp.current_phase = item["current_phase"]
        resp.adjusted_total_score = item.get("adjusted_total_score")
        out.append(resp)
    return out


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
