"""Portfolio Pydantic schemas"""

from datetime import datetime, date
from typing import Optional, Literal, List, Dict
from pydantic import BaseModel, Field


AccountType = Literal["general", "nisa_growth", "nisa_tsumitate"]


class HoldingBase(BaseModel):
    symbol: str
    name: Optional[str] = None
    quantity: int = Field(..., ge=0)
    avg_price: float = Field(..., ge=0)
    purchase_date: Optional[date] = None
    account_type: AccountType = "general"


class HoldingCreate(HoldingBase):
    pass


class HoldingUpdate(BaseModel):
    name: Optional[str] = None
    quantity: Optional[int] = Field(None, ge=0)
    avg_price: Optional[float] = Field(None, ge=0)
    purchase_date: Optional[date] = None
    account_type: Optional[AccountType] = None


class HoldingResponse(HoldingBase):
    id: int
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class TradeBase(BaseModel):
    symbol: str
    action: Literal["buy", "sell"]
    quantity: int = Field(..., ge=1)
    price: float = Field(..., ge=0)
    account_type: AccountType = "general"
    note: Optional[str] = None


class TradeCreate(TradeBase):
    executed_at: Optional[datetime] = None


class TradeResponse(TradeBase):
    id: int
    executed_at: datetime

    class Config:
        from_attributes = True


class PortfolioSettingsUpdate(BaseModel):
    target_amount: Optional[float] = None
    target_deadline: Optional[date] = None
    monthly_investment: Optional[float] = None
    nisa_used_current_year: Optional[float] = None


class PortfolioSettingsResponse(BaseModel):
    target_amount: Optional[float] = None
    target_deadline: Optional[date] = None
    monthly_investment: Optional[float] = None
    nisa_used_current_year: float = 0


class PortfolioSummary(BaseModel):
    total_value: float
    total_cost: float
    unrealized_pl: float
    holdings_count: int
    target_amount: Optional[float] = None
    progress_rate: Optional[float] = None
    nisa_remaining: float
    current_phase: Optional[str] = None
