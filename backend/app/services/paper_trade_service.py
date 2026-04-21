"""PaperTrade service - 仮想売買の業務ロジック"""

from datetime import datetime, date, timezone
from typing import Optional, Sequence

from sqlalchemy import select, delete, func
from sqlalchemy.ext.asyncio import AsyncSession
from fastapi import HTTPException

from app.models.paper_trade import PaperAccount, PaperHolding, PaperTrade
from app.models.stock_score import StockScore
from app.models.stock_price import StockPrice


LOT_SIZE = 100  # 日本株の単元株


# =================================================================
# 現在値取得ヘルパ（Portfolio と同じ経路：stock_scores の最新 close_price）
# =================================================================

async def load_latest_prices(db: AsyncSession, symbols: Sequence[str]) -> dict[str, Optional[float]]:
    """symbol -> 最新 close_price（取得不能な銘柄は dict に含まれない）"""
    if not symbols:
        return {}
    try:
        latest_subq = (
            select(StockScore.symbol, func.max(StockScore.scored_at).label("max_at"))
            .where(StockScore.symbol.in_(list(symbols)))
            .group_by(StockScore.symbol)
            .subquery()
        )
        stmt = select(StockScore.symbol, StockScore.close_price).join(
            latest_subq,
            (StockScore.symbol == latest_subq.c.symbol)
            & (StockScore.scored_at == latest_subq.c.max_at),
        )
        result = await db.execute(stmt)
        return {row.symbol: row.close_price for row in result.all() if row.close_price is not None}
    except Exception:
        return {}


# =================================================================
# 口座取得・初期化・リセット
# =================================================================

async def get_account(db: AsyncSession) -> Optional[PaperAccount]:
    result = await db.execute(select(PaperAccount).limit(1))
    return result.scalars().first()


async def init_account(db: AsyncSession, initial_cash: float) -> PaperAccount:
    existing = await get_account(db)
    if existing is not None:
        raise HTTPException(status_code=409, detail="既に初期化されています。リセットしてください")
    now = datetime.now(timezone.utc)
    account = PaperAccount(
        initial_cash=initial_cash,
        cash_balance=initial_cash,
        started_at=now,
    )
    db.add(account)
    await db.commit()
    await db.refresh(account)
    return account


async def reset_account(db: AsyncSession, initial_cash: Optional[float] = None) -> PaperAccount:
    account = await get_account(db)
    if account is None:
        raise HTTPException(status_code=409, detail="仮想口座が初期化されていません")
    new_initial = initial_cash if initial_cash is not None else account.initial_cash
    await db.execute(delete(PaperTrade).where(PaperTrade.account_id == account.id))
    await db.execute(delete(PaperHolding).where(PaperHolding.account_id == account.id))
    account.initial_cash = new_initial
    account.cash_balance = new_initial
    account.started_at = datetime.now(timezone.utc)
    await db.commit()
    await db.refresh(account)
    return account


async def require_account(db: AsyncSession) -> PaperAccount:
    """未初期化なら 409 を投げる"""
    account = await get_account(db)
    if account is None:
        raise HTTPException(status_code=409, detail="仮想口座が初期化されていません")
    return account


# =================================================================
# 売買の純粋計算ロジック（DB アクセスなし、テスト容易）
# =================================================================

def validate_quantity(quantity: int) -> None:
    if quantity <= 0 or quantity % LOT_SIZE != 0:
        raise HTTPException(status_code=400, detail="数量は100株単位で指定してください")


def calc_weighted_avg(current_qty: int, current_avg: float, add_qty: int, add_price: float) -> float:
    """既存保有に買い増したときの新しい加重平均単価"""
    total_cost = current_avg * current_qty + add_price * add_qty
    total_qty = current_qty + add_qty
    return total_cost / total_qty


def calc_realized_pl(sell_price: float, avg_price: float, quantity: int) -> float:
    return (sell_price - avg_price) * quantity


async def _get_holding(db: AsyncSession, account_id: int, symbol: str) -> Optional[PaperHolding]:
    result = await db.execute(
        select(PaperHolding).where(
            PaperHolding.account_id == account_id,
            PaperHolding.symbol == symbol,
        )
    )
    return result.scalars().first()


async def _resolve_price(db: AsyncSession, symbol: str, provided: Optional[float]) -> float:
    if provided is not None:
        return provided
    prices = await load_latest_prices(db, [symbol])
    price = prices.get(symbol)
    if price is None:
        raise HTTPException(
            status_code=400,
            detail="現在値を取得できませんでした。価格を手動で入力してください",
        )
    return float(price)


async def execute_buy(
    db: AsyncSession,
    account: PaperAccount,
    symbol: str,
    quantity: int,
    price: Optional[float],
    executed_at: Optional[datetime],
    name: Optional[str],
    note: Optional[str],
) -> PaperTrade:
    validate_quantity(quantity)
    resolved_price = await _resolve_price(db, symbol, price)
    total_cost = resolved_price * quantity
    if account.cash_balance < total_cost:
        raise HTTPException(
            status_code=400,
            detail=f"現金残高が不足しています（必要: ¥{int(total_cost):,} / 残高: ¥{int(account.cash_balance):,}）",
        )

    account.cash_balance -= total_cost
    holding = await _get_holding(db, account.id, symbol)
    if holding is None:
        holding = PaperHolding(
            account_id=account.id,
            symbol=symbol,
            name=name,
            quantity=quantity,
            avg_price=resolved_price,
        )
        db.add(holding)
    else:
        holding.avg_price = calc_weighted_avg(holding.quantity, holding.avg_price, quantity, resolved_price)
        holding.quantity += quantity
        if name and not holding.name:
            holding.name = name

    trade = PaperTrade(
        account_id=account.id,
        symbol=symbol,
        action="buy",
        quantity=quantity,
        price=resolved_price,
        total_amount=resolved_price * quantity,
        realized_pl=None,
        executed_at=executed_at or datetime.now(timezone.utc),
        note=note,
    )
    db.add(trade)
    await db.commit()
    await db.refresh(trade)
    return trade


async def execute_sell(
    db: AsyncSession,
    account: PaperAccount,
    symbol: str,
    quantity: int,
    price: Optional[float],
    executed_at: Optional[datetime],
    note: Optional[str],
) -> PaperTrade:
    validate_quantity(quantity)
    holding = await _get_holding(db, account.id, symbol)
    if holding is None:
        raise HTTPException(status_code=400, detail="この銘柄は保有していません")
    if holding.quantity < quantity:
        raise HTTPException(
            status_code=400,
            detail=f"保有数量を超えています（保有: {holding.quantity}株）",
        )
    resolved_price = await _resolve_price(db, symbol, price)
    proceeds = resolved_price * quantity
    realized_pl = calc_realized_pl(resolved_price, holding.avg_price, quantity)

    account.cash_balance += proceeds
    holding.quantity -= quantity
    if holding.quantity == 0:
        await db.delete(holding)

    trade = PaperTrade(
        account_id=account.id,
        symbol=symbol,
        action="sell",
        quantity=quantity,
        price=resolved_price,
        total_amount=resolved_price * quantity,
        realized_pl=realized_pl,
        executed_at=executed_at or datetime.now(timezone.utc),
        note=note,
    )
    db.add(trade)
    await db.commit()
    await db.refresh(trade)
    return trade


async def create_trade(
    db: AsyncSession,
    payload: dict,
) -> PaperTrade:
    """API 層から呼ばれるエントリーポイント"""
    account = await require_account(db)
    common_kwargs = dict(
        symbol=payload["symbol"],
        quantity=payload["quantity"],
        price=payload.get("price"),
        executed_at=payload.get("executed_at"),
        note=payload.get("note"),
    )
    if payload["action"] == "buy":
        return await execute_buy(
            db,
            account,
            name=payload.get("name"),
            **common_kwargs,
        )
    else:
        return await execute_sell(db, account, **common_kwargs)


# =================================================================
# 読み取り系（サマリ・保有・履歴）
# =================================================================

async def list_holdings(db: AsyncSession) -> list[dict]:
    account = await get_account(db)
    if account is None:
        return []
    result = await db.execute(
        select(PaperHolding).where(PaperHolding.account_id == account.id).order_by(PaperHolding.id)
    )
    holdings = list(result.scalars().all())
    prices = await load_latest_prices(db, [h.symbol for h in holdings])
    out = []
    for h in holdings:
        current = prices.get(h.symbol)
        if current is None:
            market_value = None
            unrealized_pl = None
            unrealized_pl_pct = None
        else:
            market_value = h.quantity * current
            unrealized_pl = (current - h.avg_price) * h.quantity
            cost = h.avg_price * h.quantity
            unrealized_pl_pct = (unrealized_pl / cost * 100) if cost else None
        out.append(
            {
                "id": h.id,
                "symbol": h.symbol,
                "name": h.name,
                "quantity": h.quantity,
                "avg_price": h.avg_price,
                "current_price": current,
                "market_value": market_value,
                "unrealized_pl": unrealized_pl,
                "unrealized_pl_pct": unrealized_pl_pct,
            }
        )
    return out


async def list_trades(db: AsyncSession, limit: int = 100, offset: int = 0) -> dict:
    account = await get_account(db)
    if account is None:
        return {"items": [], "total": 0}
    total_result = await db.execute(
        select(func.count()).select_from(PaperTrade).where(PaperTrade.account_id == account.id)
    )
    total = int(total_result.scalar() or 0)
    result = await db.execute(
        select(PaperTrade)
        .where(PaperTrade.account_id == account.id)
        .order_by(PaperTrade.executed_at.desc(), PaperTrade.id.desc())
        .offset(offset)
        .limit(limit)
    )
    items = list(result.scalars().all())
    return {"items": items, "total": total}


async def get_account_with_totals(db: AsyncSession) -> Optional[dict]:
    """GET /account 用：未初期化なら None"""
    account = await get_account(db)
    if account is None:
        return None
    holdings = await list_holdings(db)
    holdings_value = sum(h["market_value"] or 0.0 for h in holdings)
    total_value = account.cash_balance + holdings_value
    return_pct = (
        (total_value - account.initial_cash) / account.initial_cash * 100
        if account.initial_cash
        else 0.0
    )
    return {
        "initial_cash": account.initial_cash,
        "cash_balance": account.cash_balance,
        "started_at": account.started_at,
        "total_value": total_value,
        "return_pct": return_pct,
    }


async def get_summary(db: AsyncSession) -> Optional[dict]:
    account = await get_account(db)
    if account is None:
        return None
    holdings = await list_holdings(db)
    holdings_value = sum(h["market_value"] or 0.0 for h in holdings)
    unrealized_pl = sum(h["unrealized_pl"] or 0.0 for h in holdings)
    realized_result = await db.execute(
        select(func.coalesce(func.sum(PaperTrade.realized_pl), 0.0)).where(
            PaperTrade.account_id == account.id,
            PaperTrade.action == "sell",
        )
    )
    realized_pl = float(realized_result.scalar() or 0.0)
    total_value = account.cash_balance + holdings_value
    return_pct = (
        (total_value - account.initial_cash) / account.initial_cash * 100
        if account.initial_cash
        else 0.0
    )
    return {
        "initial_cash": account.initial_cash,
        "cash_balance": account.cash_balance,
        "holdings_value": holdings_value,
        "total_value": total_value,
        "unrealized_pl": unrealized_pl,
        "realized_pl": realized_pl,
        "return_pct": return_pct,
        "started_at": account.started_at,
    }
