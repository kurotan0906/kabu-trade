"""TradingViewSignal Pydantic スキーマ"""

from __future__ import annotations
from datetime import datetime
from typing import Optional, Any, Dict
from pydantic import BaseModel


class TradingViewSignalCreate(BaseModel):
    recommendation: Optional[str] = None
    score: Optional[float] = None
    buy_count: Optional[int] = None
    sell_count: Optional[int] = None
    neutral_count: Optional[int] = None
    ma_recommendation: Optional[str] = None
    osc_recommendation: Optional[str] = None
    details: Optional[Dict[str, Any]] = None


class TradingViewSignalResponse(BaseModel):
    id: int
    symbol: str
    recommendation: Optional[str] = None
    score: Optional[float] = None
    buy_count: Optional[int] = None
    sell_count: Optional[int] = None
    neutral_count: Optional[int] = None
    ma_recommendation: Optional[str] = None
    osc_recommendation: Optional[str] = None
    details: Optional[Dict[str, Any]] = None
    updated_at: datetime

    class Config:
        from_attributes = True
