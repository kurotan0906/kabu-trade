"""Stock API routes"""

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Optional
from app.core.database import get_db
from app.schemas.stock import StockInfo, StockPriceResponse

router = APIRouter()


@router.get("/{code}", response_model=StockInfo)
async def get_stock(
    code: str,
    db: AsyncSession = Depends(get_db),
):
    """
    銘柄情報を取得
    
    - **code**: 銘柄コード（例: 7203）
    """
    # TODO: Phase 1.2で実装
    raise HTTPException(status_code=501, detail="Not implemented yet")


@router.get("/{code}/prices", response_model=StockPriceResponse)
async def get_stock_prices(
    code: str,
    period: Optional[str] = Query("1y", description="期間（1d, 1w, 1m, 3m, 6m, 1y）"),
    db: AsyncSession = Depends(get_db),
):
    """
    株価データを取得
    
    - **code**: 銘柄コード（例: 7203）
    - **period**: 期間（1d, 1w, 1m, 3m, 6m, 1y）
    """
    # TODO: Phase 1.2で実装
    raise HTTPException(status_code=501, detail="Not implemented yet")
