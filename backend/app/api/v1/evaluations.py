"""Evaluation API routes"""

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Optional
from app.core.database import get_db
from app.services.evaluation_service import EvaluationService
from app.schemas.evaluation import EvaluationResult
from app.core.exceptions import StockNotFoundError

router = APIRouter()


@router.post("", response_model=EvaluationResult)
async def create_evaluation(
    stock_code: str = Query(..., description="銘柄コード（例: 7203）"),
    period: Optional[str] = Query("1y", description="期間（1d, 1w, 1m, 3m, 6m, 1y）"),
    db: AsyncSession = Depends(get_db),
):
    """
    銘柄の評価を実行
    
    - **stock_code**: 銘柄コード（例: 7203）
    - **period**: 評価期間（1d, 1w, 1m, 3m, 6m, 1y）
    """
    service = EvaluationService(db)
    try:
        evaluation = await service.evaluate_stock(stock_code, period)
        return evaluation
    except StockNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.get("/{evaluation_id}", response_model=EvaluationResult)
async def get_evaluation(
    evaluation_id: int,
    db: AsyncSession = Depends(get_db),
):
    """
    評価結果を取得
    
    - **evaluation_id**: 評価ID
    """
    # TODO: 実装
    raise HTTPException(status_code=501, detail="Not implemented yet")


@router.get("", response_model=list[EvaluationResult])
async def list_evaluations(
    stock_code: Optional[str] = Query(None, description="銘柄コードでフィルタ"),
    limit: int = Query(10, description="取得件数"),
    db: AsyncSession = Depends(get_db),
):
    """
    評価履歴一覧を取得
    
    - **stock_code**: 銘柄コードでフィルタ（オプション）
    - **limit**: 取得件数
    """
    # TODO: 実装
    raise HTTPException(status_code=501, detail="Not implemented yet")
