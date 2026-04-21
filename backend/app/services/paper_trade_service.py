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


# =================================================================
# 資産推移チャート（履歴再構築）
# =================================================================

from collections import OrderedDict


def build_close_lookup(price_rows: list[tuple[str, date, float]]) -> dict[str, "OrderedDict[date, float]"]:
    """(symbol, date, close) のリストを symbol -> OrderedDict[date, close] に変換。
    各 OrderedDict は date 昇順で保持する。
    """
    sorted_rows = sorted(price_rows, key=lambda r: (r[0], r[1]))
    out: dict[str, OrderedDict[date, float]] = {}
    for symbol, d, close in sorted_rows:
        out.setdefault(symbol, OrderedDict())[d] = close
    return out


def lookup_close_forward_fill(
    lookup: dict[str, "OrderedDict[date, float]"],
    symbol: str,
    target: date,
) -> Optional[float]:
    """target 日の close。欠損日は target 以前の最新日の close を返す（前方補完）。"""
    prices = lookup.get(symbol)
    if not prices:
        return None
    if target in prices:
        return prices[target]
    candidate: Optional[float] = None
    for d, c in prices.items():
        if d > target:
            break
        candidate = c
    return candidate


def apply_trade_to_state(
    trade: dict,
    cash: float,
    holdings: dict[str, dict],
) -> float:
    """dict ベースの state に 1 件の trade を適用して new cash を返す。
    trade は {symbol, action, quantity, price} のみ必要。holdings は symbol -> {qty, avg_price}。
    """
    symbol = trade["symbol"]
    qty = trade["quantity"]
    price = trade["price"]
    if trade["action"] == "buy":
        cash -= price * qty
        current = holdings.get(symbol)
        if current is None:
            holdings[symbol] = {"qty": qty, "avg_price": price}
        else:
            new_avg = (current["avg_price"] * current["qty"] + price * qty) / (current["qty"] + qty)
            current["qty"] += qty
            current["avg_price"] = new_avg
    else:  # sell
        cash += price * qty
        current = holdings.get(symbol)
        if current is not None:
            current["qty"] -= qty
            if current["qty"] <= 0:
                del holdings[symbol]
    return cash


from datetime import timedelta


async def _load_stock_prices(
    db: AsyncSession,
    symbols: Sequence[str],
    from_date: date,
    to_date: date,
) -> list[tuple[str, date, float]]:
    if not symbols:
        return []
    stmt = select(StockPrice.stock_code, StockPrice.date, StockPrice.close).where(
        StockPrice.stock_code.in_(list(symbols)),
        StockPrice.date >= from_date,
        StockPrice.date <= to_date,
    )
    result = await db.execute(stmt)
    return [(r.stock_code, r.date, float(r.close)) for r in result.all()]


async def reconstruct_chart(
    db: AsyncSession,
    from_date: Optional[date] = None,
    to_date: Optional[date] = None,
) -> list[dict]:
    account = await get_account(db)
    if account is None:
        return []

    trades_result = await db.execute(
        select(PaperTrade)
        .where(PaperTrade.account_id == account.id)
        .order_by(PaperTrade.executed_at.asc(), PaperTrade.id.asc())
    )
    trades = list(trades_result.scalars().all())

    start_date = from_date or account.started_at.date()
    end_date = to_date or date.today()
    if end_date < start_date:
        return []

    all_symbols = list({t.symbol for t in trades})
    # from_date より前の終値も前方補完で使うので 30 日遡って取得
    price_rows = await _load_stock_prices(db, all_symbols, start_date - timedelta(days=30), end_date)
    lookup = build_close_lookup(price_rows)

    cash = account.initial_cash
    holdings: dict[str, dict] = {}
    trade_idx = 0
    result = []
    cursor = start_date
    while cursor <= end_date:
        while trade_idx < len(trades) and trades[trade_idx].executed_at.date() <= cursor:
            t = trades[trade_idx]
            cash = apply_trade_to_state(
                {
                    "symbol": t.symbol,
                    "action": t.action,
                    "quantity": t.quantity,
                    "price": t.price,
                },
                cash,
                holdings,
            )
            trade_idx += 1
        holdings_value = 0.0
        for symbol, h in holdings.items():
            close = lookup_close_forward_fill(lookup, symbol, cursor)
            if close is None:
                close = h["avg_price"]  # セーフガード
            holdings_value += h["qty"] * close
        result.append(
            {
                "date": cursor,
                "cash": cash,
                "holdings_value": holdings_value,
                "total_value": cash + holdings_value,
            }
        )
        cursor += timedelta(days=1)
    return result


# =================================================================
# 銘柄別パフォーマンス（一覧）
# =================================================================

async def list_performance(db: AsyncSession) -> list[dict]:
    account = await get_account(db)
    if account is None:
        return []

    trades_result = await db.execute(
        select(PaperTrade)
        .where(PaperTrade.account_id == account.id)
        .order_by(PaperTrade.executed_at.asc())
    )
    trades = list(trades_result.scalars().all())

    holdings = {h["symbol"]: h for h in await list_holdings(db)}

    by_symbol: dict[str, dict] = {}
    for t in trades:
        row = by_symbol.setdefault(
            t.symbol,
            {
                "symbol": t.symbol,
                "name": None,
                "total_buy_amount": 0.0,
                "total_sell_amount": 0.0,
                "realized_pl": 0.0,
                "trade_count": 0,
                "win_count": 0,
            },
        )
        row["trade_count"] += 1
        if t.action == "buy":
            row["total_buy_amount"] += t.total_amount
        else:
            row["total_sell_amount"] += t.total_amount
            row["realized_pl"] += t.realized_pl or 0.0
            if (t.realized_pl or 0.0) > 0:
                row["win_count"] += 1

    out = []
    for symbol, row in by_symbol.items():
        h = holdings.get(symbol)
        row["name"] = h["name"] if h else None
        unrealized = h["unrealized_pl"] if h and h["unrealized_pl"] is not None else 0.0
        row["unrealized_pl"] = unrealized
        row["total_pl"] = row["realized_pl"] + unrealized
        row["return_pct"] = (
            row["total_pl"] / row["total_buy_amount"] * 100
            if row["total_buy_amount"]
            else None
        )
        out.append(row)
    out.sort(key=lambda r: r["total_pl"], reverse=True)
    return out


# =================================================================
# 銘柄別詳細分析（Analytics）
# =================================================================

from collections import deque


def build_fifo_cycles(trades: list[dict]) -> tuple[list[dict], dict]:
    """trades（時系列昇順、単一 symbol）を FIFO で closed cycle 化する。
    戻り値: (cycles, open_lots_info)
      cycles: [{entry_date, exit_date, entry_price, exit_price, quantity, pl, return_pct, holding_days}]
      open_lots_info: {quantity, avg_price, entry_date} or {quantity: 0, ...}
    """
    lots: deque = deque()
    cycles: list[dict] = []
    for t in trades:
        if t["action"] == "buy":
            lots.append(
                {
                    "date": t["executed_at"],
                    "price": t["price"],
                    "qty": t["quantity"],
                }
            )
        else:  # sell
            remaining = t["quantity"]
            while remaining > 0 and lots:
                lot = lots[0]
                used = min(lot["qty"], remaining)
                pl = (t["price"] - lot["price"]) * used
                return_pct = (t["price"] - lot["price"]) / lot["price"] * 100 if lot["price"] else 0.0
                holding_days = (t["executed_at"].date() - lot["date"].date()).days
                cycles.append(
                    {
                        "entry_date": lot["date"],
                        "exit_date": t["executed_at"],
                        "entry_price": lot["price"],
                        "exit_price": t["price"],
                        "quantity": used,
                        "pl": pl,
                        "return_pct": return_pct,
                        "holding_days": holding_days,
                    }
                )
                lot["qty"] -= used
                remaining -= used
                if lot["qty"] == 0:
                    lots.popleft()

    open_qty = sum(l["qty"] for l in lots)
    if open_qty > 0:
        total_cost = sum(l["price"] * l["qty"] for l in lots)
        open_info = {
            "quantity": open_qty,
            "avg_price": total_cost / open_qty,
            "entry_date": lots[0]["date"],
        }
    else:
        open_info = {"quantity": 0, "avg_price": 0.0, "entry_date": None}
    return cycles, open_info


def build_summary_metrics(
    cycles: list[dict],
    buy_count: int,
    sell_count: int,
    unrealized_pl: float,
    total_buy_amount: float,
) -> dict:
    trade_count = buy_count + sell_count
    win_count = sum(1 for c in cycles if c["pl"] > 0)
    loss_count = sum(1 for c in cycles if c["pl"] < 0)
    total_gains = sum(c["pl"] for c in cycles if c["pl"] > 0)
    total_losses = -sum(c["pl"] for c in cycles if c["pl"] < 0)
    realized_pl = sum(c["pl"] for c in cycles)
    total_pl = realized_pl + unrealized_pl
    decided = win_count + loss_count
    win_rate = (win_count / decided) if decided else None
    avg_holding = (sum(c["holding_days"] for c in cycles) / len(cycles)) if cycles else None
    best_pl = max((c["pl"] for c in cycles), default=None)
    worst_pl = min((c["pl"] for c in cycles), default=None)
    profit_factor = (total_gains / total_losses) if total_losses else None
    expectancy = (realized_pl / len(cycles)) if cycles else None
    return_pct = (total_pl / total_buy_amount * 100) if total_buy_amount else None
    return {
        "total_pl": total_pl,
        "realized_pl": realized_pl,
        "unrealized_pl": unrealized_pl,
        "return_pct": return_pct,
        "trade_count": trade_count,
        "buy_count": buy_count,
        "sell_count": sell_count,
        "win_count": win_count,
        "loss_count": loss_count,
        "win_rate": win_rate,
        "avg_holding_days": avg_holding,
        "best_trade_pl": best_pl,
        "worst_trade_pl": worst_pl,
        "profit_factor": profit_factor,
        "expectancy": expectancy,
    }


async def get_symbol_analytics(
    db: AsyncSession,
    symbol: str,
    from_date: Optional[date] = None,
    to_date: Optional[date] = None,
) -> Optional[dict]:
    """銘柄別の全指標を一括計算。対象銘柄に取引が 1 件も無ければ None を返す。"""
    account = await get_account(db)
    if account is None:
        return None

    trades_result = await db.execute(
        select(PaperTrade)
        .where(
            PaperTrade.account_id == account.id,
            PaperTrade.symbol == symbol,
        )
        .order_by(PaperTrade.executed_at.asc(), PaperTrade.id.asc())
    )
    db_trades = list(trades_result.scalars().all())
    if not db_trades:
        return None

    trades = [
        {
            "action": t.action,
            "quantity": t.quantity,
            "price": t.price,
            "executed_at": t.executed_at,
        }
        for t in db_trades
    ]

    cycles_raw, open_info = build_fifo_cycles(trades)

    buy_count = sum(1 for t in db_trades if t.action == "buy")
    sell_count = sum(1 for t in db_trades if t.action == "sell")
    total_buy_amount = sum(t.total_amount for t in db_trades if t.action == "buy")

    # 現在値
    prices = await load_latest_prices(db, [symbol])
    current_price = prices.get(symbol)

    # open_position と含み損益
    if open_info["quantity"] > 0 and current_price is not None:
        unrealized_pl = (current_price - open_info["avg_price"]) * open_info["quantity"]
        unrealized_pl_pct = (
            (current_price - open_info["avg_price"]) / open_info["avg_price"] * 100
            if open_info["avg_price"]
            else None
        )
    else:
        unrealized_pl = 0.0
        unrealized_pl_pct = None

    summary = build_summary_metrics(
        cycles_raw, buy_count, sell_count, unrealized_pl, total_buy_amount
    )

    # MFE / MAE
    open_position = None
    if open_info["quantity"] > 0:
        holding_days = (date.today() - open_info["entry_date"].date()).days if open_info["entry_date"] else 0
        mfe: Optional[float] = None
        mae: Optional[float] = None
        if current_price is not None:
            entry_day = open_info["entry_date"].date()
            price_rows = await _load_stock_prices(
                db, [symbol], entry_day - timedelta(days=30), date.today()
            )
            lookup = build_close_lookup(price_rows)
            cursor = entry_day
            while cursor <= date.today():
                close = lookup_close_forward_fill(lookup, symbol, cursor)
                if close is not None:
                    diff = (close - open_info["avg_price"]) * open_info["quantity"]
                    if mfe is None or diff > mfe:
                        mfe = diff
                    if mae is None or diff < mae:
                        mae = diff
                cursor += timedelta(days=1)
            if mfe is not None and mfe < 0:
                mfe = 0.0
            if mae is not None and mae > 0:
                mae = 0.0
        open_position = {
            "quantity": open_info["quantity"],
            "avg_price": open_info["avg_price"],
            "current_price": current_price,
            "unrealized_pl": unrealized_pl if current_price is not None else None,
            "unrealized_pl_pct": unrealized_pl_pct,
            "entry_date": open_info["entry_date"],
            "holding_days": holding_days,
            "mfe": mfe,
            "mae": mae,
        }

    # タイミング
    start_day = from_date or (db_trades[0].executed_at.date())
    end_day = to_date or date.today()
    price_rows_timing = await _load_stock_prices(db, [symbol], start_day, end_day)
    timing_prices = sorted(price_rows_timing, key=lambda r: r[1])
    price_series = [{"date": d, "close": c} for (_, d, c) in timing_prices]
    trade_markers = [
        {
            "date": t.executed_at,
            "action": t.action,
            "price": t.price,
            "quantity": t.quantity,
        }
        for t in db_trades
        if start_day <= t.executed_at.date() <= end_day
    ]

    # バイ＆ホールド
    first_buy = next((t for t in db_trades if t.action == "buy"), None)
    if first_buy and current_price is not None:
        bh_value_now = first_buy.quantity * current_price
        bh_return_pct = (current_price - first_buy.price) / first_buy.price * 100
        actual_return_pct = summary["return_pct"]
        diff_pct = (
            actual_return_pct - bh_return_pct if actual_return_pct is not None else None
        )
        buy_and_hold = {
            "first_buy_date": first_buy.executed_at,
            "first_buy_price": first_buy.price,
            "bh_value_now": bh_value_now,
            "bh_return_pct": bh_return_pct,
            "actual_return_pct": actual_return_pct,
            "diff_pct": diff_pct,
        }
    else:
        buy_and_hold = {
            "first_buy_date": first_buy.executed_at if first_buy else None,
            "first_buy_price": first_buy.price if first_buy else None,
            "bh_value_now": None,
            "bh_return_pct": None,
            "actual_return_pct": summary["return_pct"],
            "diff_pct": None,
        }

    # 投下資本/損益推移
    eq_lookup = build_close_lookup(price_rows_timing)
    invested = 0.0
    realized_cum = 0.0
    open_qty = 0
    open_avg = 0.0
    trade_iter = iter(db_trades)
    next_trade = next(trade_iter, None)
    equity_timeseries = []
    cursor = start_day
    while cursor <= end_day:
        while next_trade is not None and next_trade.executed_at.date() <= cursor:
            if next_trade.action == "buy":
                invested += next_trade.total_amount
                new_qty = open_qty + next_trade.quantity
                open_avg = (
                    (open_avg * open_qty + next_trade.price * next_trade.quantity) / new_qty
                    if new_qty
                    else 0.0
                )
                open_qty = new_qty
            else:
                realized_cum += next_trade.realized_pl or 0.0
                open_qty -= next_trade.quantity
                if open_qty <= 0:
                    open_qty = 0
                    open_avg = 0.0
            next_trade = next(trade_iter, None)
        unreal = 0.0
        if open_qty > 0:
            close = lookup_close_forward_fill(eq_lookup, symbol, cursor)
            if close is not None:
                unreal = (close - open_avg) * open_qty
        equity_timeseries.append(
            {
                "date": cursor,
                "invested": invested,
                "realized_pl": realized_cum,
                "unrealized_pl": unreal,
                "total_pl": realized_cum + unreal,
            }
        )
        cursor += timedelta(days=1)

    holding_row = await _get_holding(db, account.id, symbol)
    name_value = holding_row.name if holding_row else None

    return {
        "symbol": symbol,
        "name": name_value,
        "summary": summary,
        "position_cycles": cycles_raw,
        "open_position": open_position,
        "timing": {
            "price_series": price_series,
            "trade_markers": trade_markers,
        },
        "buy_and_hold": buy_and_hold,
        "equity_timeseries": equity_timeseries,
    }
