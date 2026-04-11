"""Advisor API - 将来価値シミュレータ + 履歴"""

from typing import List

from fastapi import APIRouter, Depends
from sqlalchemy import select, desc
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.models.simulation_history import SimulationHistory
from app.schemas.advisor import (
    SimulateRequest,
    SimulateResponse,
    RequiredRateRequest,
    RequiredRateResponse,
    HistoryEntry,
)
from app.services import advisor_service

router = APIRouter()


@router.post("/simulate", response_model=SimulateResponse)
async def simulate(payload: SimulateRequest, db: AsyncSession = Depends(get_db)):
    timeseries = advisor_service.simulate(
        pv=payload.pv,
        monthly_investment=payload.monthly_investment,
        annual_rate=payload.annual_rate,
        years=payload.years,
    )
    final = timeseries[-1] if timeseries else {"value": payload.pv, "contributed": payload.pv, "gain": 0}
    response = SimulateResponse(
        final_value=final["value"],
        total_contributed=final["contributed"],
        total_gain=final["gain"],
        timeseries=timeseries,
    )

    # 履歴に保存
    db.add(SimulationHistory(
        input_json=payload.model_dump(),
        result_json=response.model_dump(),
    ))
    await db.commit()

    return response


@router.post("/required-rate", response_model=RequiredRateResponse)
async def required_rate(payload: RequiredRateRequest):
    rate = advisor_service.calculate_required_rate(
        goal=payload.goal,
        pv=payload.pv,
        n_months=payload.n_months,
        monthly_investment=payload.monthly_investment,
    )
    return RequiredRateResponse(
        annual_rate_percent=rate,
        feasible=rate is not None and rate <= 200.0,
    )


@router.get("/history", response_model=List[HistoryEntry])
async def list_history(db: AsyncSession = Depends(get_db), limit: int = 50):
    result = await db.execute(
        select(SimulationHistory).order_by(desc(SimulationHistory.created_at)).limit(limit)
    )
    return list(result.scalars().all())
