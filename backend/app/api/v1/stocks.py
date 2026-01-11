"""Stock API routes"""

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Optional
from app.core.database import get_db
from app.services.stock_service import StockService
from app.schemas.stock import StockInfo, StockPriceResponse, StockPriceData
from app.core.exceptions import StockNotFoundError

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
    service = StockService(db)
    try:
        stock_info = await service.get_stock_info(code)
        return stock_info
    except StockNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))


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
    service = StockService(db)
    try:
        # 銘柄情報を取得（銘柄名を取得するため）
        stock_info = await service.get_stock_info(code)

        # 株価データを取得
        prices = await service.get_stock_prices(code, period=period)

        return StockPriceResponse(
            stock_code=code,
            stock_name=stock_info.name,
            period=period or "1y",
            prices=prices,
        )
    except StockNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
