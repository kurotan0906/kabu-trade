"""Portfolio API endpoints"""

from typing import List

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.schemas.portfolio import (
    HoldingCreate,
    HoldingUpdate,
    HoldingResponse,
    TradeCreate,
    TradeResponse,
    PortfolioSettingsUpdate,
    PortfolioSettingsResponse,
    PortfolioSummary,
)
from app.services import portfolio_service

router = APIRouter()


# ---------- Holdings ----------

@router.get("/holdings", response_model=List[HoldingResponse])
async def list_holdings(db: AsyncSession = Depends(get_db)):
    return await portfolio_service.list_holdings(db)


@router.post("/holdings", response_model=HoldingResponse, status_code=201)
async def create_holding(payload: HoldingCreate, db: AsyncSession = Depends(get_db)):
    return await portfolio_service.create_holding(db, payload.model_dump())


@router.put("/holdings/{holding_id}", response_model=HoldingResponse)
async def update_holding(holding_id: int, payload: HoldingUpdate, db: AsyncSession = Depends(get_db)):
    h = await portfolio_service.update_holding(db, holding_id, payload.model_dump(exclude_unset=True))
    if h is None:
        raise HTTPException(status_code=404, detail="holding not found")
    return h


@router.delete("/holdings/{holding_id}", status_code=204)
async def delete_holding(holding_id: int, db: AsyncSession = Depends(get_db)):
    ok = await portfolio_service.delete_holding(db, holding_id)
    if not ok:
        raise HTTPException(status_code=404, detail="holding not found")
    return None


# ---------- Settings ----------

@router.get("/settings", response_model=PortfolioSettingsResponse)
async def get_settings(db: AsyncSession = Depends(get_db)):
    return await portfolio_service.get_settings(db)


@router.put("/settings", response_model=PortfolioSettingsResponse)
async def update_settings(payload: PortfolioSettingsUpdate, db: AsyncSession = Depends(get_db)):
    return await portfolio_service.update_settings(db, **payload.model_dump(exclude_unset=True))


# ---------- Trades ----------

@router.get("/trades", response_model=List[TradeResponse])
async def list_trades(db: AsyncSession = Depends(get_db), limit: int = 100):
    return await portfolio_service.list_trades(db, limit=limit)


@router.post("/trades", response_model=TradeResponse, status_code=201)
async def create_trade(payload: TradeCreate, db: AsyncSession = Depends(get_db)):
    return await portfolio_service.create_trade(db, payload.model_dump())


# ---------- Summary ----------

@router.get("/summary", response_model=PortfolioSummary)
async def summary(db: AsyncSession = Depends(get_db)):
    return await portfolio_service.get_summary(db)
