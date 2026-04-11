"""Advisor Pydantic schemas"""

from datetime import datetime
from typing import List, Optional
from pydantic import BaseModel, Field


class SimulateRequest(BaseModel):
    pv: float = Field(..., ge=0, description="現在評価額（円）")
    monthly_investment: float = Field(0, ge=0)
    annual_rate: float = Field(..., description="年利（小数。0.05 = 5%）")
    years: int = Field(..., ge=1, le=100)


class SimulatePoint(BaseModel):
    year: int
    value: float
    contributed: float
    gain: float


class SimulateResponse(BaseModel):
    final_value: float
    total_contributed: float
    total_gain: float
    timeseries: List[SimulatePoint]


class RequiredRateRequest(BaseModel):
    goal: float = Field(..., gt=0)
    pv: float = Field(..., gt=0)
    n_months: int = Field(..., ge=1)
    monthly_investment: float = Field(0, ge=0)


class RequiredRateResponse(BaseModel):
    annual_rate_percent: Optional[float]
    feasible: bool


class HistoryEntry(BaseModel):
    id: int
    created_at: datetime
    input_json: dict
    result_json: dict

    class Config:
        from_attributes = True
