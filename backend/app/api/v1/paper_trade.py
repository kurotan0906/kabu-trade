"""PaperTrade API endpoints"""

from datetime import date as date_cls
from typing import Union

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.schemas.paper_trade import (
    AccountUninitialized,
    AccountInitialized,
    AccountInitRequest,
    AccountResetRequest,
    TradeCreate,
    TradeCreateResponse,
    TradeResponse,
    TradesPage,
    HoldingResponse,
    SummaryResponse,
    ChartPoint,
    PerformanceItem,
    AnalyticsResponse,
)
from app.services import paper_trade_service as svc

router = APIRouter()


@router.get("/account", response_model=Union[AccountInitialized, AccountUninitialized])
async def get_account(db: AsyncSession = Depends(get_db)):
    info = await svc.get_account_with_totals(db)
    if info is None:
        return AccountUninitialized()
    return AccountInitialized(**info)


@router.post("/account", response_model=AccountInitialized, status_code=201)
async def init_account(payload: AccountInitRequest, db: AsyncSession = Depends(get_db)):
    await svc.init_account(db, payload.initial_cash)
    info = await svc.get_account_with_totals(db)
    return AccountInitialized(**info)


@router.post("/account/reset", response_model=AccountInitialized)
async def reset_account(payload: AccountResetRequest, db: AsyncSession = Depends(get_db)):
    await svc.reset_account(db, payload.initial_cash)
    info = await svc.get_account_with_totals(db)
    return AccountInitialized(**info)


@router.get("/holdings", response_model=list[HoldingResponse])
async def list_holdings(db: AsyncSession = Depends(get_db)):
    return await svc.list_holdings(db)


@router.get("/trades", response_model=TradesPage)
async def list_trades(
    db: AsyncSession = Depends(get_db),
    limit: int = Query(100, ge=1, le=500),
    offset: int = Query(0, ge=0),
):
    data = await svc.list_trades(db, limit=limit, offset=offset)
    return TradesPage(items=[TradeResponse.model_validate(t) for t in data["items"]], total=data["total"])


@router.post("/trades", response_model=TradeCreateResponse, status_code=201)
async def create_trade(payload: TradeCreate, db: AsyncSession = Depends(get_db)):
    trade = await svc.create_trade(db, payload.model_dump())
    info = await svc.get_account_with_totals(db)
    return TradeCreateResponse(trade=TradeResponse.model_validate(trade), cash_balance=info["cash_balance"], total_value=info["total_value"])


@router.get("/summary", response_model=SummaryResponse)
async def get_summary(db: AsyncSession = Depends(get_db)):
    data = await svc.get_summary(db)
    if data is None:
        raise HTTPException(status_code=409, detail="仮想口座が初期化されていません")
    return SummaryResponse(**data)


@router.get("/chart", response_model=list[ChartPoint])
async def get_chart(
    db: AsyncSession = Depends(get_db),
    from_date: date_cls | None = Query(None, alias="from"),
    to_date: date_cls | None = Query(None, alias="to"),
):
    return await svc.reconstruct_chart(db, from_date=from_date, to_date=to_date)


@router.get("/performance", response_model=list[PerformanceItem])
async def get_performance(db: AsyncSession = Depends(get_db)):
    return await svc.list_performance(db)


@router.get("/symbols/{symbol}/analytics", response_model=AnalyticsResponse)
async def get_symbol_analytics(
    symbol: str,
    db: AsyncSession = Depends(get_db),
    from_date: date_cls | None = Query(None, alias="from"),
    to_date: date_cls | None = Query(None, alias="to"),
):
    data = await svc.get_symbol_analytics(db, symbol, from_date=from_date, to_date=to_date)
    if data is None:
        raise HTTPException(status_code=404, detail="この銘柄の取引履歴がありません")
    return AnalyticsResponse(**data)
