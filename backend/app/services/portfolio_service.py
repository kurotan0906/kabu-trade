"""Portfolio service - 保有銘柄の評価額・進捗率・NISA 残枠計算"""

from datetime import date, datetime
from typing import Optional, Sequence

from sqlalchemy import select, delete
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.portfolio import Holding, PortfolioSetting, TradeHistory
from app.models.stock_score import StockScore


NISA_GROWTH_ANNUAL_LIMIT = 2_400_000  # 成長投資枠年間上限 (円)


# ---------- 設定 (key-value) ----------

_ALLOWED_KEYS = {
    "target_amount",
    "target_deadline",
    "monthly_investment",
    "nisa_used_current_year",
}


async def get_settings(db: AsyncSession) -> dict:
    result = await db.execute(select(PortfolioSetting))
    rows = {r.key: r.value for r in result.scalars().all()}
    return {
        "target_amount": _to_float(rows.get("target_amount")),
        "target_deadline": _to_date(rows.get("target_deadline")),
        "monthly_investment": _to_float(rows.get("monthly_investment")),
        "nisa_used_current_year": _to_float(rows.get("nisa_used_current_year")) or 0.0,
    }


async def update_settings(db: AsyncSession, **kwargs) -> dict:
    for key, value in kwargs.items():
        if key not in _ALLOWED_KEYS or value is None:
            continue
        await _upsert_setting(db, key, _stringify(value))
    await db.commit()
    return await get_settings(db)


async def _upsert_setting(db: AsyncSession, key: str, value: str):
    existing = await db.get(PortfolioSetting, key)
    if existing:
        existing.value = value
    else:
        db.add(PortfolioSetting(key=key, value=value))


# ---------- 評価・進捗 ----------

async def calc_total_value(db: AsyncSession, holdings: Optional[Sequence[Holding]] = None) -> tuple[float, float]:
    """(total_value, total_cost) を返す。評価価格は最新 StockScore.per で近似できないため、
    当面は取得単価ベース（total_value = total_cost）。価格 API との連携は将来対応。
    """
    if holdings is None:
        result = await db.execute(select(Holding))
        holdings = list(result.scalars().all())

    total_cost = sum(h.quantity * h.avg_price for h in holdings)
    # StockScore には直近価格が無いため、評価額は暫定的に取得価格に揃える。
    total_value = total_cost
    return total_value, total_cost


async def calc_progress_rate(db: AsyncSession) -> Optional[float]:
    """目標額に対する総評価額の進捗率 (%) を返す。target 未設定なら None。"""
    settings = await get_settings(db)
    target = settings.get("target_amount")
    if not target or target <= 0:
        return None
    total_value, _ = await calc_total_value(db)
    return round(total_value / target * 100, 2)


async def get_progress_rate(db: AsyncSession) -> float:
    """scores API の profile=auto から呼ばれるヘルパ。None の場合は 0 を返す。"""
    rate = await calc_progress_rate(db)
    return rate or 0.0


def get_nisa_remaining(used: float) -> float:
    return max(0.0, NISA_GROWTH_ANNUAL_LIMIT - (used or 0))


async def get_summary(db: AsyncSession) -> dict:
    result = await db.execute(select(Holding))
    holdings = list(result.scalars().all())
    total_value, total_cost = await calc_total_value(db, holdings)
    settings = await get_settings(db)
    target = settings.get("target_amount")
    progress_rate = None
    if target and target > 0:
        progress_rate = round(total_value / target * 100, 2)

    current_phase = None
    if progress_rate is not None:
        try:
            from app.analyzer.phase_scorer import get_phase
            current_phase = get_phase(progress_rate)
        except ImportError:
            pass

    return {
        "total_value": total_value,
        "total_cost": total_cost,
        "unrealized_pl": total_value - total_cost,
        "holdings_count": len(holdings),
        "target_amount": target,
        "progress_rate": progress_rate,
        "nisa_remaining": get_nisa_remaining(settings.get("nisa_used_current_year") or 0),
        "current_phase": current_phase,
    }


# ---------- CRUD ----------

async def list_holdings(db: AsyncSession) -> list[Holding]:
    result = await db.execute(select(Holding).order_by(Holding.id))
    return list(result.scalars().all())


async def create_holding(db: AsyncSession, data: dict) -> Holding:
    h = Holding(**data)
    db.add(h)
    await db.commit()
    await db.refresh(h)
    return h


async def update_holding(db: AsyncSession, holding_id: int, data: dict) -> Optional[Holding]:
    h = await db.get(Holding, holding_id)
    if h is None:
        return None
    for k, v in data.items():
        if v is not None:
            setattr(h, k, v)
    await db.commit()
    await db.refresh(h)
    return h


async def delete_holding(db: AsyncSession, holding_id: int) -> bool:
    h = await db.get(Holding, holding_id)
    if h is None:
        return False
    await db.delete(h)
    await db.commit()
    return True


async def list_trades(db: AsyncSession, limit: int = 100) -> list[TradeHistory]:
    result = await db.execute(
        select(TradeHistory).order_by(TradeHistory.executed_at.desc()).limit(limit)
    )
    return list(result.scalars().all())


async def create_trade(db: AsyncSession, data: dict) -> TradeHistory:
    if data.get("executed_at") is None:
        data = {**data, "executed_at": datetime.utcnow()}
    t = TradeHistory(**data)
    db.add(t)
    await db.commit()
    await db.refresh(t)
    return t


# ---------- helpers ----------

def _to_float(s: Optional[str]) -> Optional[float]:
    if s is None:
        return None
    try:
        return float(s)
    except (ValueError, TypeError):
        return None


def _to_date(s: Optional[str]) -> Optional[date]:
    if s is None:
        return None
    try:
        return date.fromisoformat(s)
    except (ValueError, TypeError):
        return None


def _stringify(v) -> str:
    if isinstance(v, date):
        return v.isoformat()
    return str(v)
