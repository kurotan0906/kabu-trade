"""ChartAnalysis API routes"""

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, desc
from typing import Optional
from app.core.database import get_db
from app.models.chart_analysis import ChartAnalysis
from app.schemas.chart_analysis import ChartAnalysisCreate, ChartAnalysisResponse
from app.services.chart_analysis_service import ChartAnalysisService

router = APIRouter()


@router.post(
    "/{symbol}/generate",
    response_model=ChartAnalysisResponse,
    status_code=201,
)
async def generate_chart_analysis(
    symbol: str,
    timeframe: str = Query("1D", description="時間足（現状は 1D 固定）"),
    db: AsyncSession = Depends(get_db),
):
    """
    指標計算 + ヒューリスティックで分析を自動生成し保存する。

    - **symbol**: 銘柄コード（例: 7203）
    - **timeframe**: 時間足（デフォルト 1D）
    """
    service = ChartAnalysisService(db)
    try:
        return await service.generate_and_save(symbol, timeframe)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.post("", response_model=ChartAnalysisResponse, status_code=201)
async def create_chart_analysis(
    data: ChartAnalysisCreate,
    db: AsyncSession = Depends(get_db),
):
    """
    チャート分析結果を保存

    - **symbol**: 銘柄コード（例: 7203）
    - **timeframe**: 時間足（例: 1D, 1W）
    - **trend**: トレンド（bullish/bearish/neutral）
    - **recommendation**: 推奨（buy/sell/hold）
    - **summary**: Claudeが生成したサマリー
    """
    analysis = ChartAnalysis(
        symbol=data.symbol,
        timeframe=data.timeframe,
        screenshot_path=data.screenshot_path,
        trend=data.trend,
        signals=data.signals,
        summary=data.summary,
        recommendation=data.recommendation,
    )
    db.add(analysis)
    await db.commit()
    await db.refresh(analysis)
    return analysis


@router.get("/{symbol}/latest", response_model=ChartAnalysisResponse)
async def get_latest_chart_analysis(
    symbol: str,
    timeframe: Optional[str] = Query(None, description="時間足でフィルタ"),
    db: AsyncSession = Depends(get_db),
):
    """
    銘柄の最新チャート分析を取得

    - **symbol**: 銘柄コード（例: 7203）
    - **timeframe**: 時間足でフィルタ（オプション）
    """
    stmt = select(ChartAnalysis).where(ChartAnalysis.symbol == symbol)
    if timeframe:
        stmt = stmt.where(ChartAnalysis.timeframe == timeframe)
    stmt = stmt.order_by(desc(ChartAnalysis.created_at)).limit(1)

    result = await db.execute(stmt)
    analysis = result.scalar_one_or_none()

    if not analysis:
        raise HTTPException(
            status_code=404,
            detail=f"銘柄 {symbol} のチャート分析が見つかりません",
        )
    return analysis


@router.get("/{symbol}/history", response_model=list[ChartAnalysisResponse])
async def list_chart_analyses(
    symbol: str,
    timeframe: Optional[str] = Query(None, description="時間足でフィルタ"),
    limit: int = Query(20, ge=1, le=100, description="取得件数"),
    db: AsyncSession = Depends(get_db),
):
    """
    銘柄のチャート分析履歴を取得

    - **symbol**: 銘柄コード（例: 7203）
    - **timeframe**: 時間足でフィルタ（オプション）
    - **limit**: 取得件数（最大100）
    """
    stmt = select(ChartAnalysis).where(ChartAnalysis.symbol == symbol)
    if timeframe:
        stmt = stmt.where(ChartAnalysis.timeframe == timeframe)
    stmt = stmt.order_by(desc(ChartAnalysis.created_at)).limit(limit)

    result = await db.execute(stmt)
    return result.scalars().all()
