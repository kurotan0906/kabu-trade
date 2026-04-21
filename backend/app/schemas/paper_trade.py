"""PaperTrade Pydantic schemas"""

from datetime import datetime, date
from typing import Optional, Literal, List
from pydantic import BaseModel, Field


# ---------- Account ----------

class AccountUninitialized(BaseModel):
    initialized: Literal[False] = False


class AccountInitialized(BaseModel):
    initialized: Literal[True] = True
    initial_cash: float
    cash_balance: float
    started_at: datetime
    total_value: float
    return_pct: float


class AccountInitRequest(BaseModel):
    initial_cash: float = Field(..., gt=0)


class AccountResetRequest(BaseModel):
    initial_cash: Optional[float] = Field(None, gt=0)


# ---------- Trade ----------

class TradeCreate(BaseModel):
    action: Literal["buy", "sell"]
    symbol: str
    quantity: int = Field(..., gt=0)
    price: Optional[float] = Field(None, gt=0)
    executed_at: Optional[datetime] = None
    note: Optional[str] = None


class TradeResponse(BaseModel):
    id: int
    symbol: str
    action: Literal["buy", "sell"]
    quantity: int
    price: float
    total_amount: float
    realized_pl: Optional[float]
    executed_at: datetime
    note: Optional[str]

    class Config:
        from_attributes = True


class TradesPage(BaseModel):
    items: List[TradeResponse]
    total: int


class TradeCreateResponse(BaseModel):
    trade: TradeResponse
    cash_balance: float
    total_value: float


# ---------- Holding ----------

class HoldingResponse(BaseModel):
    id: int
    symbol: str
    name: Optional[str]
    quantity: int
    avg_price: float
    current_price: Optional[float]
    market_value: Optional[float]
    unrealized_pl: Optional[float]
    unrealized_pl_pct: Optional[float]


# ---------- Summary ----------

class SummaryResponse(BaseModel):
    initial_cash: float
    cash_balance: float
    holdings_value: float
    total_value: float
    unrealized_pl: float
    realized_pl: float
    return_pct: float
    started_at: datetime


# ---------- Chart ----------

class ChartPoint(BaseModel):
    date: date
    cash: float
    holdings_value: float
    total_value: float


# ---------- Performance (symbol list) ----------

class PerformanceItem(BaseModel):
    symbol: str
    name: Optional[str]
    total_buy_amount: float
    total_sell_amount: float
    realized_pl: float
    unrealized_pl: float
    total_pl: float
    return_pct: Optional[float]
    trade_count: int
    win_count: int


# ---------- Symbol Analytics ----------

class SummaryMetrics(BaseModel):
    total_pl: float
    realized_pl: float
    unrealized_pl: float
    return_pct: Optional[float]
    trade_count: int
    buy_count: int
    sell_count: int
    win_count: int
    loss_count: int
    win_rate: Optional[float]
    avg_holding_days: Optional[float]
    best_trade_pl: Optional[float]
    worst_trade_pl: Optional[float]
    profit_factor: Optional[float]
    expectancy: Optional[float]


class PositionCycle(BaseModel):
    entry_date: datetime
    exit_date: datetime
    entry_price: float
    exit_price: float
    quantity: int
    pl: float
    return_pct: float
    holding_days: int


class OpenPosition(BaseModel):
    quantity: int
    avg_price: float
    current_price: Optional[float]
    unrealized_pl: Optional[float]
    unrealized_pl_pct: Optional[float]
    entry_date: datetime
    holding_days: int
    mfe: Optional[float]
    mae: Optional[float]


class TradeMarker(BaseModel):
    date: datetime
    action: Literal["buy", "sell"]
    price: float
    quantity: int


class PricePoint(BaseModel):
    date: date
    close: float


class TimingData(BaseModel):
    price_series: List[PricePoint]
    trade_markers: List[TradeMarker]


class BuyAndHold(BaseModel):
    first_buy_date: Optional[datetime]
    first_buy_price: Optional[float]
    bh_value_now: Optional[float]
    bh_return_pct: Optional[float]
    actual_return_pct: Optional[float]
    diff_pct: Optional[float]


class EquityPoint(BaseModel):
    date: date
    invested: float
    realized_pl: float
    unrealized_pl: float
    total_pl: float


class AnalyticsResponse(BaseModel):
    symbol: str
    name: Optional[str]
    summary: SummaryMetrics
    position_cycles: List[PositionCycle]
    open_position: Optional[OpenPosition]
    timing: TimingData
    buy_and_hold: BuyAndHold
    equity_timeseries: List[EquityPoint]
