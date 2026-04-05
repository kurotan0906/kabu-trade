"""StockScore Pydantic スキーマ"""

from datetime import datetime
from typing import Optional, Any, Dict, List
from pydantic import BaseModel, Field


class StockScoreResponse(BaseModel):
    id: int
    symbol: str
    name: Optional[str] = None
    sector: Optional[str] = None
    scored_at: datetime
    total_score: Optional[float] = None
    rating: Optional[str] = None
    fundamental_score: Optional[float] = None
    technical_score: Optional[float] = None
    kurotenko_score: Optional[float] = None
    kurotenko_criteria: Optional[Dict[str, Any]] = None
    per: Optional[float] = None
    pbr: Optional[float] = None
    roe: Optional[float] = None
    dividend_yield: Optional[float] = None
    revenue_growth: Optional[float] = None
    ma_score: Optional[float] = None
    rsi_score: Optional[float] = None
    macd_score: Optional[float] = None
    data_quality: str = "ok"

    class Config:
        from_attributes = True


class AnalysisAxis(BaseModel):
    name: str
    score: Optional[float] = None
    recommendation: Optional[str] = None
    detail: Dict[str, Any] = Field(default_factory=dict)


class AnalysisAxesResponse(BaseModel):
    symbol: str
    axes: List[AnalysisAxis]
