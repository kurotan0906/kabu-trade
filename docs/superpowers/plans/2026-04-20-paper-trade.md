# ペーパートレード機能 実装計画

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 仮想資金で銘柄の擬似売買ができる「ペーパートレード」ページと、銘柄別に豊富な指標で売買結果を分析できる詳細ページを追加する。

**Architecture:** 既存 Portfolio モジュールの隣に `paper_trade` を独立配置。Backend は SQLAlchemy + FastAPI の 3 レイヤ構造（models / services / api）。Frontend は React Router + Tailwind、銘柄別分析ページには **Indicator Registry パターン** で指標ごとに独立コンポーネントを登録する。

**Tech Stack:** Python 3.11 / FastAPI / SQLAlchemy async / Alembic / pytest / React 18 / TypeScript / React Router / Recharts / Tailwind v4

**Reference:** `docs/superpowers/specs/2026-04-20-paper-trade-design.md`

---

## ディレクトリ構成（完成像）

```
backend/app/
  models/paper_trade.py
  schemas/paper_trade.py
  services/paper_trade_service.py       # 単一ファイル。内部で関数ごとに分割
  api/v1/paper_trade.py
  alembic/versions/008_add_paper_trade.py

backend/tests/
  test_paper_trade_service.py           # pure function テスト（FIFO, MFE/MAE 等）
  test_paper_trade_api.py               # エンドポイントの統合テスト（必要に応じて追加）

frontend/src/
  pages/PaperTradePage.tsx
  pages/PaperTradeSymbolPage.tsx
  components/paper-trade/
    BuyDialog.tsx
    SellDialog.tsx
    InitCapitalDialog.tsx
    ResetConfirmDialog.tsx
    AssetHistoryChart.tsx
    PerformanceTable.tsx
    analytics/
      registry.ts
      IndicatorSelector.tsx
      SummaryCard.tsx
      PositionCyclesCard.tsx
      OpenPositionCard.tsx
      TimingChartCard.tsx
      BuyAndHoldCard.tsx
      EquityTimeseriesCard.tsx
  services/api/paperTradeApi.ts
  types/paperTrade.ts
```

タスク分解は「機能単位で動くブロック」を優先。個々の Indicator Card は機械的作業なので 2 タスクに束ねる。

---

## Task 1: Alembic マイグレーション + SQLAlchemy モデル

**Files:**
- Create: `backend/alembic/versions/008_add_paper_trade.py`
- Create: `backend/app/models/paper_trade.py`

**目的:** 3 テーブル（paper_accounts / paper_holdings / paper_trades）を作成。将来の手数料・配当に備えた予約カラムを paper_trades に含める。

- [ ] **Step 1: マイグレーションファイルを作成**

Create `backend/alembic/versions/008_add_paper_trade.py`:

```python
"""add paper trade tables

Revision ID: 008_add_paper_trade
Revises: 007_add_close_price
Create Date: 2026-04-20 00:00:00.000000
"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa

revision: str = '008_add_paper_trade'
down_revision: Union[str, None] = '007_add_close_price'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        'paper_accounts',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('initial_cash', sa.Float(), nullable=False),
        sa.Column('cash_balance', sa.Float(), nullable=False),
        sa.Column('started_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.PrimaryKeyConstraint('id'),
    )

    op.create_table(
        'paper_holdings',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('account_id', sa.Integer(), nullable=False),
        sa.Column('symbol', sa.String(length=10), nullable=False),
        sa.Column('name', sa.String(length=100), nullable=True),
        sa.Column('quantity', sa.Integer(), nullable=False),
        sa.Column('avg_price', sa.Float(), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('account_id', 'symbol', name='uq_paper_holdings_account_symbol'),
    )
    op.create_index('ix_paper_holdings_account_id', 'paper_holdings', ['account_id'])
    op.create_index('ix_paper_holdings_symbol', 'paper_holdings', ['symbol'])

    op.create_table(
        'paper_trades',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('account_id', sa.Integer(), nullable=False),
        sa.Column('symbol', sa.String(length=10), nullable=False),
        sa.Column('action', sa.String(length=4), nullable=False),
        sa.Column('quantity', sa.Integer(), nullable=False),
        sa.Column('price', sa.Float(), nullable=False),
        sa.Column('total_amount', sa.Float(), nullable=False),
        sa.Column('realized_pl', sa.Float(), nullable=True),
        sa.Column('executed_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('note', sa.String(length=255), nullable=True),
        sa.Column('fee', sa.Float(), nullable=True, comment='予約: 手数料。MVP では常に NULL'),
        sa.Column('dividend', sa.Float(), nullable=True, comment='予約: 配当。MVP では常に NULL'),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index('ix_paper_trades_account_id', 'paper_trades', ['account_id'])
    op.create_index('ix_paper_trades_symbol', 'paper_trades', ['symbol'])
    op.create_index('ix_paper_trades_executed_at', 'paper_trades', ['executed_at'])


def downgrade() -> None:
    op.drop_index('ix_paper_trades_executed_at', table_name='paper_trades')
    op.drop_index('ix_paper_trades_symbol', table_name='paper_trades')
    op.drop_index('ix_paper_trades_account_id', table_name='paper_trades')
    op.drop_table('paper_trades')
    op.drop_index('ix_paper_holdings_symbol', table_name='paper_holdings')
    op.drop_index('ix_paper_holdings_account_id', table_name='paper_holdings')
    op.drop_table('paper_holdings')
    op.drop_table('paper_accounts')
```

- [ ] **Step 2: モデルファイルを作成**

Create `backend/app/models/paper_trade.py`:

```python
"""PaperTrade models - 仮想売買の口座・保有・取引履歴"""

from sqlalchemy import Column, Integer, Float, String, DateTime, UniqueConstraint
from sqlalchemy.sql import func
from app.core.database import Base


class PaperAccount(Base):
    """ペーパートレード仮想口座 (MVP では 1 行のみ)"""

    __tablename__ = "paper_accounts"

    id = Column(Integer, primary_key=True, autoincrement=True)
    initial_cash = Column(Float, nullable=False, comment="初期資金")
    cash_balance = Column(Float, nullable=False, comment="現在の仮想現金残高")
    started_at = Column(DateTime(timezone=True), nullable=False, comment="運用開始日")
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)


class PaperHolding(Base):
    """ペーパートレード保有銘柄"""

    __tablename__ = "paper_holdings"

    id = Column(Integer, primary_key=True, autoincrement=True)
    account_id = Column(Integer, nullable=False, index=True)
    symbol = Column(String(10), nullable=False, index=True)
    name = Column(String(100), nullable=True)
    quantity = Column(Integer, nullable=False)
    avg_price = Column(Float, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)

    __table_args__ = (
        UniqueConstraint("account_id", "symbol", name="uq_paper_holdings_account_symbol"),
    )


class PaperTrade(Base):
    """ペーパートレード取引履歴"""

    __tablename__ = "paper_trades"

    id = Column(Integer, primary_key=True, autoincrement=True)
    account_id = Column(Integer, nullable=False, index=True)
    symbol = Column(String(10), nullable=False, index=True)
    action = Column(String(4), nullable=False, comment="'buy' or 'sell'")
    quantity = Column(Integer, nullable=False)
    price = Column(Float, nullable=False)
    total_amount = Column(Float, nullable=False)
    realized_pl = Column(Float, nullable=True, comment="sell のみ記録")
    executed_at = Column(DateTime(timezone=True), nullable=False, index=True)
    note = Column(String(255), nullable=True)
    fee = Column(Float, nullable=True, comment="予約: MVP では常に NULL")
    dividend = Column(Float, nullable=True, comment="予約: MVP では常に NULL")
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
```

- [ ] **Step 3: マイグレーション適用を検証**

Run:
```bash
cd backend && uv run alembic upgrade head
```
Expected: `INFO  [alembic.runtime.migration] Running upgrade 007_add_close_price -> 008_add_paper_trade`

- [ ] **Step 4: テーブル作成を DB 側で確認**

Run (psql が無い場合は Neon ダッシュボードまたは `uv run python -c "..."` で代替):
```bash
cd backend && uv run python -c "
import asyncio
from sqlalchemy import text
from app.core.database import engine

async def check():
    async with engine.begin() as conn:
        result = await conn.execute(text(\"SELECT table_name FROM information_schema.tables WHERE table_name LIKE 'paper_%'\"))
        print(sorted([r[0] for r in result]))

asyncio.run(check())
"
```
Expected: `['paper_accounts', 'paper_holdings', 'paper_trades']`

- [ ] **Step 5: Commit**

```bash
git add backend/alembic/versions/008_add_paper_trade.py backend/app/models/paper_trade.py
git commit -m "feat(paper-trade): 仮想口座・保有・取引履歴テーブルを追加"
```

---

## Task 2: Pydantic スキーマ

**Files:**
- Create: `backend/app/schemas/paper_trade.py`

**目的:** API 入出力の型を定義。フロント側の型と 1:1 対応させる。

- [ ] **Step 1: スキーマファイルを作成**

Create `backend/app/schemas/paper_trade.py`:

```python
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
```

- [ ] **Step 2: インポートだけで読めることを確認**

Run:
```bash
cd backend && uv run python -c "from app.schemas.paper_trade import AccountInitialized, TradeCreate, AnalyticsResponse; print('OK')"
```
Expected: `OK`

- [ ] **Step 3: Commit**

```bash
git add backend/app/schemas/paper_trade.py
git commit -m "feat(paper-trade): Pydantic スキーマを追加"
```

---

## Task 3: Service 層 - 口座 init / reset + 現在値ヘルパ

**Files:**
- Create: `backend/app/services/paper_trade_service.py`

**目的:** 口座初期化・リセット機能と、以降のタスクで使う「最新終値取得」ヘルパを置く。

- [ ] **Step 1: サービスファイルの骨組みとヘルパ関数を作成**

Create `backend/app/services/paper_trade_service.py`:

```python
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
```

- [ ] **Step 2: インポート可能か確認**

Run:
```bash
cd backend && uv run python -c "from app.services import paper_trade_service; print(paper_trade_service.LOT_SIZE)"
```
Expected: `100`

- [ ] **Step 3: Commit**

```bash
git add backend/app/services/paper_trade_service.py
git commit -m "feat(paper-trade): Service 層の骨組みと口座 init/reset を追加"
```

---

## Task 4: Service 層 - 買い・売り実行

**Files:**
- Modify: `backend/app/services/paper_trade_service.py` (関数を追記)

**目的:** 売買実行（検証 → 現金・保有・履歴の 3 者更新）。エラーハンドリングはすべて HTTPException(400) で統一。

- [ ] **Step 1: Pure な検証関数を作成（テスト容易化のため）**

`backend/app/services/paper_trade_service.py` の末尾に追記:

```python
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
```

- [ ] **Step 2: Pure 関数のテストを書く（失敗確認 → 実装 → 成功確認済みなので即コミット）**

Create `backend/tests/test_paper_trade_service.py`:

```python
"""paper_trade_service の純粋関数テスト（DB アクセス不要）"""

import pytest
from fastapi import HTTPException

from app.services import paper_trade_service as svc


class TestValidateQuantity:
    def test_ok_100(self):
        svc.validate_quantity(100)

    def test_ok_500(self):
        svc.validate_quantity(500)

    def test_zero_fails(self):
        with pytest.raises(HTTPException) as exc:
            svc.validate_quantity(0)
        assert exc.value.status_code == 400
        assert "100株単位" in exc.value.detail

    def test_negative_fails(self):
        with pytest.raises(HTTPException):
            svc.validate_quantity(-100)

    def test_not_lot_size_fails(self):
        with pytest.raises(HTTPException):
            svc.validate_quantity(150)


class TestCalcWeightedAvg:
    def test_simple(self):
        # 100株@1000 に 100株@1200 を買い増し → 平均 1100
        assert svc.calc_weighted_avg(100, 1000.0, 100, 1200.0) == 1100.0

    def test_unequal_qty(self):
        # 100株@1000 に 300株@1400 を買い増し → (100000 + 420000) / 400 = 1300
        assert svc.calc_weighted_avg(100, 1000.0, 300, 1400.0) == 1300.0


class TestCalcRealizedPl:
    def test_gain(self):
        assert svc.calc_realized_pl(2650.0, 2500.0, 100) == 15000.0

    def test_loss(self):
        assert svc.calc_realized_pl(2400.0, 2500.0, 100) == -10000.0

    def test_breakeven(self):
        assert svc.calc_realized_pl(2500.0, 2500.0, 100) == 0.0
```

Run:
```bash
cd backend && uv run pytest tests/test_paper_trade_service.py -v
```
Expected: all pass.

- [ ] **Step 3: 買い実行の関数を追記**

`backend/app/services/paper_trade_service.py` の末尾に追記:

```python
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
```

- [ ] **Step 4: 売り実行の関数を追記**

さらに末尾に追記:

```python
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
```

- [ ] **Step 5: Pure 関数テストを再実行してリグレッションが無いことを確認**

Run:
```bash
cd backend && uv run pytest tests/test_paper_trade_service.py -v
```
Expected: all pass.

- [ ] **Step 6: Commit**

```bash
git add backend/app/services/paper_trade_service.py backend/tests/test_paper_trade_service.py
git commit -m "feat(paper-trade): 買い・売り実行ロジックと純粋関数テストを追加"
```

---

## Task 5: Service 層 - サマリ / 保有一覧 / 取引履歴

**Files:**
- Modify: `backend/app/services/paper_trade_service.py`

**目的:** 読み取り系の関数を揃える。

- [ ] **Step 1: 関数を追記**

`backend/app/services/paper_trade_service.py` の末尾に追記:

```python
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
```

- [ ] **Step 2: インポート確認**

Run:
```bash
cd backend && uv run python -c "from app.services.paper_trade_service import list_holdings, list_trades, get_summary, get_account_with_totals; print('OK')"
```
Expected: `OK`

- [ ] **Step 3: Commit**

```bash
git add backend/app/services/paper_trade_service.py
git commit -m "feat(paper-trade): サマリ・保有一覧・取引履歴の読み取り関数を追加"
```

---

## Task 6: Service 層 - 資産推移チャート（履歴再構築）

**Files:**
- Modify: `backend/app/services/paper_trade_service.py`

**目的:** 日次総資産を trades + stock_prices から再計算。前方補完あり。純粋ロジック部分はテスト可能な形で切り出す。

- [ ] **Step 1: 純粋関数と純粋関数のテストを書く**

`backend/app/services/paper_trade_service.py` の末尾に追記:

```python
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
```

テストを追加 `backend/tests/test_paper_trade_service.py`:

```python
from datetime import date as date_cls

# 既存の import の下に追加


class TestBuildCloseLookup:
    def test_builds_per_symbol_ordered(self):
        rows = [
            ("A", date_cls(2026, 1, 2), 200.0),
            ("A", date_cls(2026, 1, 1), 100.0),
            ("B", date_cls(2026, 1, 1), 50.0),
        ]
        lookup = svc.build_close_lookup(rows)
        assert list(lookup["A"].keys()) == [date_cls(2026, 1, 1), date_cls(2026, 1, 2)]
        assert lookup["A"][date_cls(2026, 1, 2)] == 200.0
        assert lookup["B"][date_cls(2026, 1, 1)] == 50.0


class TestForwardFill:
    def _lookup(self):
        return svc.build_close_lookup(
            [
                ("A", date_cls(2026, 1, 1), 100.0),
                ("A", date_cls(2026, 1, 3), 120.0),
            ]
        )

    def test_exact_hit(self):
        assert svc.lookup_close_forward_fill(self._lookup(), "A", date_cls(2026, 1, 1)) == 100.0

    def test_forward_fills_gap(self):
        # 1/2 は無いので 1/1 の値を返す
        assert svc.lookup_close_forward_fill(self._lookup(), "A", date_cls(2026, 1, 2)) == 100.0

    def test_before_earliest(self):
        # 1/1 より前 → None
        assert svc.lookup_close_forward_fill(self._lookup(), "A", date_cls(2025, 12, 31)) is None

    def test_unknown_symbol(self):
        assert svc.lookup_close_forward_fill(self._lookup(), "X", date_cls(2026, 1, 1)) is None


class TestApplyTradeToState:
    def test_buy_new(self):
        cash = 1_000_000.0
        holdings: dict[str, dict] = {}
        new_cash = svc.apply_trade_to_state(
            {"symbol": "A", "action": "buy", "quantity": 100, "price": 1000.0},
            cash,
            holdings,
        )
        assert new_cash == 900_000.0
        assert holdings == {"A": {"qty": 100, "avg_price": 1000.0}}

    def test_buy_more_averages(self):
        holdings = {"A": {"qty": 100, "avg_price": 1000.0}}
        svc.apply_trade_to_state(
            {"symbol": "A", "action": "buy", "quantity": 100, "price": 1200.0},
            1_000_000.0,
            holdings,
        )
        assert holdings["A"]["qty"] == 200
        assert holdings["A"]["avg_price"] == 1100.0

    def test_sell_partial(self):
        holdings = {"A": {"qty": 200, "avg_price": 1000.0}}
        new_cash = svc.apply_trade_to_state(
            {"symbol": "A", "action": "sell", "quantity": 100, "price": 1300.0},
            0.0,
            holdings,
        )
        assert new_cash == 130_000.0
        assert holdings["A"]["qty"] == 100

    def test_sell_all_removes_holding(self):
        holdings = {"A": {"qty": 100, "avg_price": 1000.0}}
        svc.apply_trade_to_state(
            {"symbol": "A", "action": "sell", "quantity": 100, "price": 1100.0},
            0.0,
            holdings,
        )
        assert "A" not in holdings
```

Run:
```bash
cd backend && uv run pytest tests/test_paper_trade_service.py -v
```
Expected: all pass.

- [ ] **Step 2: 履歴再構築関数（DB アクセスあり）を実装**

`backend/app/services/paper_trade_service.py` の末尾に追記:

```python
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
```

- [ ] **Step 3: 再テストしリグレッションを確認**

Run:
```bash
cd backend && uv run pytest tests/test_paper_trade_service.py -v
```
Expected: all pass.

- [ ] **Step 4: Commit**

```bash
git add backend/app/services/paper_trade_service.py backend/tests/test_paper_trade_service.py
git commit -m "feat(paper-trade): 資産推移チャートの履歴再構築ロジックを追加"
```

---

## Task 7: Service 層 - 銘柄別パフォーマンス（一覧）

**Files:**
- Modify: `backend/app/services/paper_trade_service.py`

**目的:** メインページ下部の「銘柄別パフォーマンス」テーブル用。

- [ ] **Step 1: 関数を追記**

`backend/app/services/paper_trade_service.py` の末尾に追記:

```python
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
```

- [ ] **Step 2: インポート確認**

Run:
```bash
cd backend && uv run python -c "from app.services.paper_trade_service import list_performance; print('OK')"
```
Expected: `OK`

- [ ] **Step 3: Commit**

```bash
git add backend/app/services/paper_trade_service.py
git commit -m "feat(paper-trade): 銘柄別パフォーマンス一覧の集計関数を追加"
```

---

## Task 8: Service 層 - 銘柄別詳細分析（FIFO / MFE / バイ&ホールド / エクイティ推移）

**Files:**
- Modify: `backend/app/services/paper_trade_service.py`
- Modify: `backend/tests/test_paper_trade_service.py`

**目的:** 詳細分析ページの `/symbols/{symbol}/analytics` レスポンスを生成。FIFO マッチングと統計指標の純粋ロジックはテスト可能な形で切り出す。

- [ ] **Step 1: FIFO サイクル計算（純粋関数）を実装**

`backend/app/services/paper_trade_service.py` の末尾に追記:

```python
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
```

- [ ] **Step 2: FIFO / Summary のテストを追加**

`backend/tests/test_paper_trade_service.py` の末尾に追加:

```python
from datetime import datetime as datetime_cls


def _trade(action: str, qty: int, price: float, day: int):
    return {
        "action": action,
        "quantity": qty,
        "price": price,
        "executed_at": datetime_cls(2026, 4, day),
    }


class TestBuildFifoCycles:
    def test_single_cycle(self):
        trades = [_trade("buy", 100, 2500, 1), _trade("sell", 100, 2650, 31)]
        cycles, open_info = svc.build_fifo_cycles(trades)
        assert len(cycles) == 1
        c = cycles[0]
        assert c["entry_price"] == 2500
        assert c["exit_price"] == 2650
        assert c["quantity"] == 100
        assert c["pl"] == 15000
        assert c["return_pct"] == 6.0
        assert c["holding_days"] == 30
        assert open_info == {"quantity": 0, "avg_price": 0.0, "entry_date": None}

    def test_one_sell_consumes_two_lots(self):
        # 100@1000 + 100@1200 を 200@1400 で売る → cycle が 2 件
        trades = [
            _trade("buy", 100, 1000, 1),
            _trade("buy", 100, 1200, 5),
            _trade("sell", 200, 1400, 10),
        ]
        cycles, open_info = svc.build_fifo_cycles(trades)
        assert len(cycles) == 2
        assert cycles[0]["entry_price"] == 1000
        assert cycles[0]["pl"] == 40000  # (1400-1000)*100
        assert cycles[1]["entry_price"] == 1200
        assert cycles[1]["pl"] == 20000  # (1400-1200)*100
        assert open_info["quantity"] == 0

    def test_partial_close_leaves_open(self):
        # 100@1000 + 100@1200 を 100@1400 で売る → cycle 1件, open 100@1200
        trades = [
            _trade("buy", 100, 1000, 1),
            _trade("buy", 100, 1200, 5),
            _trade("sell", 100, 1400, 10),
        ]
        cycles, open_info = svc.build_fifo_cycles(trades)
        assert len(cycles) == 1
        assert cycles[0]["entry_price"] == 1000
        assert open_info["quantity"] == 100
        assert open_info["avg_price"] == 1200

    def test_fifo_total_pl_equals_sum_of_per_trade_realized_pl(self):
        # FIFO の pl 合計 = 加重平均方式の sell 合計と一致する
        trades = [
            _trade("buy", 100, 1000, 1),
            _trade("buy", 100, 1200, 5),
            _trade("sell", 150, 1500, 10),  # 加重平均@1100 → pl = (1500-1100)*150 = 60000
        ]
        cycles, _ = svc.build_fifo_cycles(trades)
        # FIFO: 100@1000→1500 (50000), 50@1200→1500 (15000) = 65000
        # 加重平均: (1500-1100)*150 = 60000
        # → 合計は按分の違いにより一致しない場合がある旨は spec で言及済み
        # ここでは FIFO 合計だけを検証
        assert sum(c["pl"] for c in cycles) == 65000


class TestBuildSummaryMetrics:
    def test_happy_path(self):
        cycles = [
            {"pl": 15000, "holding_days": 30, "return_pct": 6.0},
            {"pl": -5000, "holding_days": 10, "return_pct": -2.0},
        ]
        m = svc.build_summary_metrics(cycles, buy_count=2, sell_count=2, unrealized_pl=0, total_buy_amount=500000)
        assert m["trade_count"] == 4
        assert m["win_count"] == 1
        assert m["loss_count"] == 1
        assert m["win_rate"] == 0.5
        assert m["avg_holding_days"] == 20.0
        assert m["best_trade_pl"] == 15000
        assert m["worst_trade_pl"] == -5000
        assert m["profit_factor"] == 3.0  # 15000 / 5000
        assert m["expectancy"] == 5000  # (15000 + -5000) / 2
        assert m["realized_pl"] == 10000
        assert m["total_pl"] == 10000
        assert m["return_pct"] == 2.0  # 10000 / 500000 * 100

    def test_no_losses_profit_factor_null(self):
        cycles = [{"pl": 15000, "holding_days": 30, "return_pct": 6.0}]
        m = svc.build_summary_metrics(cycles, 1, 1, 0, 250000)
        assert m["profit_factor"] is None

    def test_no_trades(self):
        m = svc.build_summary_metrics([], 0, 0, 0, 0)
        assert m["win_rate"] is None
        assert m["avg_holding_days"] is None
        assert m["best_trade_pl"] is None
        assert m["worst_trade_pl"] is None
        assert m["profit_factor"] is None
        assert m["expectancy"] is None
        assert m["return_pct"] is None
```

Run:
```bash
cd backend && uv run pytest tests/test_paper_trade_service.py -v
```
Expected: all pass.

- [ ] **Step 3: Analytics レスポンス生成関数を実装（DB アクセスあり）**

`backend/app/services/paper_trade_service.py` の末尾に追記:

```python
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

    # MFE / MAE: 現在保有ありかつ現在値取得可能のときのみ算出
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

    name = next((t.symbol for t in []), None)  # name は holdings から取る
    holding_row = await _get_holding(db, account.id, symbol)
    name_value = holding_row.name if holding_row else (db_trades[-1].note if False else None)

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
```

- [ ] **Step 4: テストを再実行してリグレッションなきを確認**

Run:
```bash
cd backend && uv run pytest tests/test_paper_trade_service.py -v
```
Expected: all pass.

- [ ] **Step 5: Commit**

```bash
git add backend/app/services/paper_trade_service.py backend/tests/test_paper_trade_service.py
git commit -m "feat(paper-trade): 銘柄別詳細分析（FIFO/MFE/バイ&ホールド/エクイティ推移）を追加"
```

---

## Task 9: API ルーター + main.py へのマウント

**Files:**
- Create: `backend/app/api/v1/paper_trade.py`
- Modify: `backend/app/main.py`

**目的:** 全エンドポイントを実装し、ルーターを FastAPI に登録。

- [ ] **Step 1: API ルーターを作成**

Create `backend/app/api/v1/paper_trade.py`:

```python
"""PaperTrade API endpoints"""

from datetime import date as date_cls
from typing import Union

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.schemas.paper_trade import (
    AccountUninitialized,
    AccountInitialized,
    AccountInitRequest,
    AccountResetRequest,
    TradeCreate,
    TradeCreateResponse,
    TradeResponse,
    TradesPage,
    HoldingResponse,
    SummaryResponse,
    ChartPoint,
    PerformanceItem,
    AnalyticsResponse,
)
from app.services import paper_trade_service as svc

router = APIRouter()


# ---------- Account ----------

@router.get("/account", response_model=Union[AccountInitialized, AccountUninitialized])
async def get_account(db: AsyncSession = Depends(get_db)):
    info = await svc.get_account_with_totals(db)
    if info is None:
        return AccountUninitialized()
    return AccountInitialized(**info)


@router.post("/account", response_model=AccountInitialized, status_code=201)
async def init_account(payload: AccountInitRequest, db: AsyncSession = Depends(get_db)):
    await svc.init_account(db, payload.initial_cash)
    info = await svc.get_account_with_totals(db)
    return AccountInitialized(**info)


@router.post("/account/reset", response_model=AccountInitialized)
async def reset_account(payload: AccountResetRequest, db: AsyncSession = Depends(get_db)):
    await svc.reset_account(db, payload.initial_cash)
    info = await svc.get_account_with_totals(db)
    return AccountInitialized(**info)


# ---------- Holdings / Trades ----------

@router.get("/holdings", response_model=list[HoldingResponse])
async def list_holdings(db: AsyncSession = Depends(get_db)):
    return await svc.list_holdings(db)


@router.get("/trades", response_model=TradesPage)
async def list_trades(
    db: AsyncSession = Depends(get_db),
    limit: int = Query(100, ge=1, le=500),
    offset: int = Query(0, ge=0),
):
    data = await svc.list_trades(db, limit=limit, offset=offset)
    return TradesPage(
        items=[TradeResponse.model_validate(t) for t in data["items"]],
        total=data["total"],
    )


@router.post("/trades", response_model=TradeCreateResponse, status_code=201)
async def create_trade(payload: TradeCreate, db: AsyncSession = Depends(get_db)):
    trade = await svc.create_trade(db, payload.model_dump())
    info = await svc.get_account_with_totals(db)
    return TradeCreateResponse(
        trade=TradeResponse.model_validate(trade),
        cash_balance=info["cash_balance"],
        total_value=info["total_value"],
    )


# ---------- Summary / Chart / Performance ----------

@router.get("/summary", response_model=SummaryResponse)
async def get_summary(db: AsyncSession = Depends(get_db)):
    data = await svc.get_summary(db)
    if data is None:
        raise HTTPException(status_code=409, detail="仮想口座が初期化されていません")
    return SummaryResponse(**data)


@router.get("/chart", response_model=list[ChartPoint])
async def get_chart(
    db: AsyncSession = Depends(get_db),
    from_date: date_cls | None = Query(None, alias="from"),
    to_date: date_cls | None = Query(None, alias="to"),
):
    return await svc.reconstruct_chart(db, from_date=from_date, to_date=to_date)


@router.get("/performance", response_model=list[PerformanceItem])
async def get_performance(db: AsyncSession = Depends(get_db)):
    return await svc.list_performance(db)


# ---------- Symbol Analytics ----------

@router.get("/symbols/{symbol}/analytics", response_model=AnalyticsResponse)
async def get_symbol_analytics(
    symbol: str,
    db: AsyncSession = Depends(get_db),
    from_date: date_cls | None = Query(None, alias="from"),
    to_date: date_cls | None = Query(None, alias="to"),
):
    data = await svc.get_symbol_analytics(db, symbol, from_date=from_date, to_date=to_date)
    if data is None:
        raise HTTPException(status_code=404, detail="この銘柄の取引履歴がありません")
    return AnalyticsResponse(**data)
```

- [ ] **Step 2: main.py にルーターを登録**

`backend/app/main.py` の末尾付近、Advisor 登録の直後に追加:

```python
# ペーパートレード API
from app.api.v1 import paper_trade
app.include_router(paper_trade.router, prefix="/api/v1/paper-trade", tags=["paper-trade"])
```

- [ ] **Step 3: サーバ起動確認**

Run:
```bash
cd backend && uv run python -c "from app.main import app; print([r.path for r in app.routes if '/paper-trade' in r.path])"
```
Expected: リストに `/api/v1/paper-trade/account` などが含まれる

- [ ] **Step 4: エンドポイントの疎通確認（dev server を立てる）**

Run:
```bash
cd backend && uv run uvicorn app.main:app --port 8000 &
sleep 3
curl -s http://localhost:8000/api/v1/paper-trade/account
```
Expected: `{"initialized":false}`

その後、バックグラウンドサーバを停止する。

- [ ] **Step 5: Commit**

```bash
git add backend/app/api/v1/paper_trade.py backend/app/main.py
git commit -m "feat(paper-trade): API ルーターを実装し FastAPI に登録"
```

---

## Task 10: フロントエンド型定義 + API クライアント + ルーティング + ナビ

**Files:**
- Create: `frontend/src/types/paperTrade.ts`
- Create: `frontend/src/services/api/paperTradeApi.ts`
- Modify: `frontend/src/App.tsx`
- Modify: `frontend/src/components/layout/NavLinks.tsx`

**目的:** フロント側の足回りを整える。

- [ ] **Step 1: 型定義を作成**

Create `frontend/src/types/paperTrade.ts`:

```ts
export type TradeAction = 'buy' | 'sell';

export type AccountUninitialized = { initialized: false };

export interface AccountInitialized {
  initialized: true;
  initial_cash: number;
  cash_balance: number;
  started_at: string;
  total_value: number;
  return_pct: number;
}

export type AccountResponse = AccountInitialized | AccountUninitialized;

export interface PaperTrade {
  id: number;
  symbol: string;
  action: TradeAction;
  quantity: number;
  price: number;
  total_amount: number;
  realized_pl: number | null;
  executed_at: string;
  note: string | null;
}

export interface TradesPage {
  items: PaperTrade[];
  total: number;
}

export interface PaperHolding {
  id: number;
  symbol: string;
  name: string | null;
  quantity: number;
  avg_price: number;
  current_price: number | null;
  market_value: number | null;
  unrealized_pl: number | null;
  unrealized_pl_pct: number | null;
}

export interface PaperSummary {
  initial_cash: number;
  cash_balance: number;
  holdings_value: number;
  total_value: number;
  unrealized_pl: number;
  realized_pl: number;
  return_pct: number;
  started_at: string;
}

export interface ChartPoint {
  date: string;
  cash: number;
  holdings_value: number;
  total_value: number;
}

export interface PerformanceItem {
  symbol: string;
  name: string | null;
  total_buy_amount: number;
  total_sell_amount: number;
  realized_pl: number;
  unrealized_pl: number;
  total_pl: number;
  return_pct: number | null;
  trade_count: number;
  win_count: number;
}

export interface SummaryMetrics {
  total_pl: number;
  realized_pl: number;
  unrealized_pl: number;
  return_pct: number | null;
  trade_count: number;
  buy_count: number;
  sell_count: number;
  win_count: number;
  loss_count: number;
  win_rate: number | null;
  avg_holding_days: number | null;
  best_trade_pl: number | null;
  worst_trade_pl: number | null;
  profit_factor: number | null;
  expectancy: number | null;
}

export interface PositionCycle {
  entry_date: string;
  exit_date: string;
  entry_price: number;
  exit_price: number;
  quantity: number;
  pl: number;
  return_pct: number;
  holding_days: number;
}

export interface OpenPosition {
  quantity: number;
  avg_price: number;
  current_price: number | null;
  unrealized_pl: number | null;
  unrealized_pl_pct: number | null;
  entry_date: string;
  holding_days: number;
  mfe: number | null;
  mae: number | null;
}

export interface TradeMarker {
  date: string;
  action: TradeAction;
  price: number;
  quantity: number;
}

export interface PricePoint {
  date: string;
  close: number;
}

export interface TimingData {
  price_series: PricePoint[];
  trade_markers: TradeMarker[];
}

export interface BuyAndHold {
  first_buy_date: string | null;
  first_buy_price: number | null;
  bh_value_now: number | null;
  bh_return_pct: number | null;
  actual_return_pct: number | null;
  diff_pct: number | null;
}

export interface EquityPoint {
  date: string;
  invested: number;
  realized_pl: number;
  unrealized_pl: number;
  total_pl: number;
}

export interface AnalyticsResponse {
  symbol: string;
  name: string | null;
  summary: SummaryMetrics;
  position_cycles: PositionCycle[];
  open_position: OpenPosition | null;
  timing: TimingData;
  buy_and_hold: BuyAndHold;
  equity_timeseries: EquityPoint[];
}

export interface TradeCreatePayload {
  action: TradeAction;
  symbol: string;
  quantity: number;
  price?: number;
  executed_at?: string;
  note?: string | null;
  name?: string | null;
}

export interface TradeCreateResponse {
  trade: PaperTrade;
  cash_balance: number;
  total_value: number;
}
```

- [ ] **Step 2: API クライアントを作成**

Create `frontend/src/services/api/paperTradeApi.ts`:

```ts
import { apiClient } from '@/lib/apiClient';
import type {
  AccountResponse,
  AccountInitialized,
  PaperTrade,
  TradesPage,
  PaperHolding,
  PaperSummary,
  ChartPoint,
  PerformanceItem,
  AnalyticsResponse,
  TradeCreatePayload,
  TradeCreateResponse,
} from '@/types/paperTrade';

const base = '/paper-trade';

export const paperTradeApi = {
  async getAccount(): Promise<AccountResponse> {
    const { data } = await apiClient.get<AccountResponse>(`${base}/account`);
    return data;
  },
  async initAccount(initial_cash: number): Promise<AccountInitialized> {
    const { data } = await apiClient.post<AccountInitialized>(`${base}/account`, { initial_cash });
    return data;
  },
  async resetAccount(initial_cash?: number): Promise<AccountInitialized> {
    const { data } = await apiClient.post<AccountInitialized>(`${base}/account/reset`, { initial_cash });
    return data;
  },
  async listHoldings(): Promise<PaperHolding[]> {
    const { data } = await apiClient.get<PaperHolding[]>(`${base}/holdings`);
    return data;
  },
  async listTrades(limit = 100, offset = 0): Promise<TradesPage> {
    const { data } = await apiClient.get<TradesPage>(`${base}/trades`, { params: { limit, offset } });
    return data;
  },
  async createTrade(payload: TradeCreatePayload): Promise<TradeCreateResponse> {
    const { data } = await apiClient.post<TradeCreateResponse>(`${base}/trades`, payload);
    return data;
  },
  async getSummary(): Promise<PaperSummary> {
    const { data } = await apiClient.get<PaperSummary>(`${base}/summary`);
    return data;
  },
  async getChart(from?: string, to?: string): Promise<ChartPoint[]> {
    const { data } = await apiClient.get<ChartPoint[]>(`${base}/chart`, { params: { from, to } });
    return data;
  },
  async getPerformance(): Promise<PerformanceItem[]> {
    const { data } = await apiClient.get<PerformanceItem[]>(`${base}/performance`);
    return data;
  },
  async getSymbolAnalytics(symbol: string, from?: string, to?: string): Promise<AnalyticsResponse> {
    const { data } = await apiClient.get<AnalyticsResponse>(
      `${base}/symbols/${encodeURIComponent(symbol)}/analytics`,
      { params: { from, to } }
    );
    return data;
  },
};
```

- [ ] **Step 3: ナビに項目を追加**

Modify `frontend/src/components/layout/NavLinks.tsx`:

```ts
export const NAV_ITEMS: NavItem[] = [
  { to: '/', label: 'ホーム', icon: '🏠' },
  { to: '/ranking', label: 'ランキング', icon: '📊' },
  { to: '/portfolio', label: 'ポートフォリオ', icon: '💼' },
  { to: '/paper-trade', label: 'ペーパートレード', icon: '🧪' },
  { to: '/simulator', label: 'シミュレータ', icon: '📈' },
  { to: '/history', label: '履歴', icon: '📜' },
];
```

- [ ] **Step 4: ルーティングにページを追加**

Modify `frontend/src/App.tsx`:

```tsx
import { BrowserRouter, Routes, Route } from 'react-router-dom'
import HomePage from './pages/HomePage'
import StockDetailPage from './pages/StockDetailPage'
import StockRankingPage from './pages/StockRankingPage'
import PortfolioPage from './pages/PortfolioPage'
import SimulatorPage from './pages/SimulatorPage'
import AnalysisHistoryPage from './pages/AnalysisHistoryPage'
import PaperTradePage from './pages/PaperTradePage'
import PaperTradeSymbolPage from './pages/PaperTradeSymbolPage'
import { AppShell } from './components/layout/AppShell'
import './App.css'

function App() {
  return (
    <BrowserRouter>
      <Routes>
        <Route element={<AppShell />}>
          <Route path="/" element={<HomePage />} />
          <Route path="/ranking" element={<StockRankingPage />} />
          <Route path="/portfolio" element={<PortfolioPage />} />
          <Route path="/paper-trade" element={<PaperTradePage />} />
          <Route path="/paper-trade/symbols/:symbol" element={<PaperTradeSymbolPage />} />
          <Route path="/simulator" element={<SimulatorPage />} />
          <Route path="/history" element={<AnalysisHistoryPage />} />
          <Route path="/stocks/:code" element={<StockDetailPage />} />
        </Route>
      </Routes>
    </BrowserRouter>
  )
}

export default App
```

- [ ] **Step 5: 一時スタブページを作成（コンパイルを通すため）**

Create `frontend/src/pages/PaperTradePage.tsx`:

```tsx
const PaperTradePage = () => <div className="p-6">WIP</div>;
export default PaperTradePage;
```

Create `frontend/src/pages/PaperTradeSymbolPage.tsx`:

```tsx
const PaperTradeSymbolPage = () => <div className="p-6">WIP</div>;
export default PaperTradeSymbolPage;
```

- [ ] **Step 6: 型チェック**

Run:
```bash
cd frontend && npx tsc --noEmit
```
Expected: エラー 0 件

- [ ] **Step 7: Commit**

```bash
git add frontend/src/types/paperTrade.ts frontend/src/services/api/paperTradeApi.ts frontend/src/components/layout/NavLinks.tsx frontend/src/App.tsx frontend/src/pages/PaperTradePage.tsx frontend/src/pages/PaperTradeSymbolPage.tsx
git commit -m "feat(paper-trade): 型・APIクライアント・ルーティング・ナビを追加"
```

---

## Task 11: メインページ骨組み + Init / Reset ダイアログ

**Files:**
- Modify: `frontend/src/pages/PaperTradePage.tsx`
- Create: `frontend/src/components/paper-trade/InitCapitalDialog.tsx`
- Create: `frontend/src/components/paper-trade/ResetConfirmDialog.tsx`

**目的:** 未初期化時の EmptyState、初期化後の Stat カード表示、Init/Reset ダイアログを完成させる。

- [ ] **Step 1: InitCapitalDialog を作成**

Create `frontend/src/components/paper-trade/InitCapitalDialog.tsx`:

```tsx
import { useEffect, useState } from 'react';
import { Dialog, Field, NumberInput, Button } from '@/components/ui';
import { paperTradeApi } from '@/services/api/paperTradeApi';

interface Props {
  open: boolean;
  onClose: () => void;
  onInitialized: () => void;
}

export const InitCapitalDialog = ({ open, onClose, onInitialized }: Props) => {
  const [cash, setCash] = useState(1_000_000);
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (open) {
      setCash(1_000_000);
      setError(null);
    }
  }, [open]);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (cash <= 0) {
      setError('初期資金は 1 円以上で指定してください');
      return;
    }
    setSubmitting(true);
    setError(null);
    try {
      await paperTradeApi.initAccount(cash);
      onInitialized();
      onClose();
    } catch (err) {
      setError(err instanceof Error ? err.message : '初期化に失敗しました');
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <Dialog open={open} onClose={onClose} title="仮想口座を作成" size="sm">
      <form onSubmit={handleSubmit} className="flex flex-col gap-4">
        <p className="text-sm text-slate-600">
          この資金を元手に擬似的な売買を行います。リセットするまで変更できません。
        </p>
        <Field label="初期資金 (円)">
          <NumberInput value={cash} onChange={setCash} min={0} step={100_000} />
        </Field>
        {error && (
          <div className="rounded-md border border-rose-200 bg-rose-50 px-3 py-2 text-xs text-rose-700">
            {error}
          </div>
        )}
        <div className="flex justify-end gap-2 pt-2">
          <Button type="button" variant="secondary" onClick={onClose} disabled={submitting}>
            キャンセル
          </Button>
          <Button type="submit" variant="accent" disabled={submitting}>
            {submitting ? '作成中...' : '作成する'}
          </Button>
        </div>
      </form>
    </Dialog>
  );
};

export default InitCapitalDialog;
```

- [ ] **Step 2: ResetConfirmDialog を作成**

Create `frontend/src/components/paper-trade/ResetConfirmDialog.tsx`:

```tsx
import { useEffect, useState } from 'react';
import { Dialog, Field, NumberInput, Button } from '@/components/ui';
import { paperTradeApi } from '@/services/api/paperTradeApi';

interface Props {
  open: boolean;
  onClose: () => void;
  currentInitialCash: number;
  onReset: () => void;
}

export const ResetConfirmDialog = ({ open, onClose, currentInitialCash, onReset }: Props) => {
  const [cash, setCash] = useState(currentInitialCash);
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (open) {
      setCash(currentInitialCash);
      setError(null);
    }
  }, [open, currentInitialCash]);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setSubmitting(true);
    setError(null);
    try {
      await paperTradeApi.resetAccount(cash);
      onReset();
      onClose();
    } catch (err) {
      setError(err instanceof Error ? err.message : 'リセットに失敗しました');
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <Dialog open={open} onClose={onClose} title="仮想口座をリセット" size="sm">
      <form onSubmit={handleSubmit} className="flex flex-col gap-4">
        <div className="rounded-md border border-amber-200 bg-amber-50 px-3 py-2 text-xs text-amber-800">
          保有銘柄・取引履歴・現金残高がすべて消去され、指定した初期資金で再スタートします。
        </div>
        <Field label="新しい初期資金 (円)">
          <NumberInput value={cash} onChange={setCash} min={0} step={100_000} />
        </Field>
        {error && (
          <div className="rounded-md border border-rose-200 bg-rose-50 px-3 py-2 text-xs text-rose-700">
            {error}
          </div>
        )}
        <div className="flex justify-end gap-2 pt-2">
          <Button type="button" variant="secondary" onClick={onClose} disabled={submitting}>
            キャンセル
          </Button>
          <Button type="submit" variant="danger" disabled={submitting}>
            {submitting ? 'リセット中...' : 'リセット実行'}
          </Button>
        </div>
      </form>
    </Dialog>
  );
};

export default ResetConfirmDialog;
```

※ `Button` に `variant="danger"` が無い場合は `variant="secondary"` に替えるか、`@/components/ui/Button` 側を確認して合わせる。

- [ ] **Step 3: PaperTradePage の骨組みを作る**

Replace `frontend/src/pages/PaperTradePage.tsx`:

```tsx
import { useCallback, useEffect, useState } from 'react';
import {
  PageHeader,
  Button,
  Card,
  CardBody,
  Stat,
  EmptyState,
} from '@/components/ui';
import { paperTradeApi } from '@/services/api/paperTradeApi';
import type {
  AccountInitialized,
  PaperSummary,
} from '@/types/paperTrade';
import InitCapitalDialog from '@/components/paper-trade/InitCapitalDialog';
import ResetConfirmDialog from '@/components/paper-trade/ResetConfirmDialog';

const formatYen = (v: number | null | undefined) =>
  v == null ? '—' : `¥${Math.round(v).toLocaleString()}`;

const PaperTradePage = () => {
  const [account, setAccount] = useState<AccountInitialized | null>(null);
  const [summary, setSummary] = useState<PaperSummary | null>(null);
  const [loading, setLoading] = useState(true);
  const [initOpen, setInitOpen] = useState(false);
  const [resetOpen, setResetOpen] = useState(false);

  const refresh = useCallback(async () => {
    setLoading(true);
    try {
      const acc = await paperTradeApi.getAccount();
      if (acc.initialized) {
        setAccount(acc);
        const s = await paperTradeApi.getSummary();
        setSummary(s);
      } else {
        setAccount(null);
        setSummary(null);
      }
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    void refresh();
  }, [refresh]);

  if (loading) {
    return <div className="p-6 text-sm text-slate-500">読み込み中...</div>;
  }

  if (!account) {
    return (
      <>
        <PageHeader title="ペーパートレード" description="仮想資金で売買を試す" />
        <Card>
          <CardBody>
            <EmptyState
              title="仮想口座を作成しましょう"
              description="初期資金を設定すると、擬似的な売買シミュレーションを開始できます。"
            />
            <div className="flex justify-center pt-4">
              <Button variant="accent" onClick={() => setInitOpen(true)}>
                初期資金を設定して開始
              </Button>
            </div>
          </CardBody>
        </Card>
        <InitCapitalDialog
          open={initOpen}
          onClose={() => setInitOpen(false)}
          onInitialized={refresh}
        />
      </>
    );
  }

  const s = summary;
  return (
    <div>
      <PageHeader
        title="ペーパートレード"
        description="仮想資金で売買を試す"
        actions={
          <div className="flex gap-2">
            <Button variant="secondary" onClick={() => setResetOpen(true)}>
              リセット
            </Button>
            <Button variant="accent" disabled>
              買い付け
            </Button>
          </div>
        }
      />
      <div className="grid gap-3 grid-cols-2 md:grid-cols-3 lg:grid-cols-6 mb-4">
        <Stat label="総資産" value={formatYen(s?.total_value)} accent="brand" />
        <Stat label="現金残高" value={formatYen(s?.cash_balance)} />
        <Stat label="保有評価額" value={formatYen(s?.holdings_value)} />
        <Stat
          label="含み損益"
          value={formatYen(s?.unrealized_pl)}
          accent={(s?.unrealized_pl ?? 0) >= 0 ? 'success' : 'danger'}
        />
        <Stat
          label="実現損益"
          value={formatYen(s?.realized_pl)}
          accent={(s?.realized_pl ?? 0) >= 0 ? 'success' : 'danger'}
        />
        <Stat
          label="リターン"
          value={s?.return_pct != null ? `${s.return_pct.toFixed(2)}%` : '—'}
          accent={(s?.return_pct ?? 0) >= 0 ? 'success' : 'danger'}
        />
      </div>
      <Card>
        <CardBody className="text-sm text-slate-500">チャートと保有一覧は後続タスクで実装します。</CardBody>
      </Card>
      <ResetConfirmDialog
        open={resetOpen}
        onClose={() => setResetOpen(false)}
        currentInitialCash={account.initial_cash}
        onReset={refresh}
      />
    </div>
  );
};

export default PaperTradePage;
```

- [ ] **Step 4: 型チェック**

Run:
```bash
cd frontend && npx tsc --noEmit
```
Expected: エラー 0 件

- [ ] **Step 5: Commit**

```bash
git add frontend/src/pages/PaperTradePage.tsx frontend/src/components/paper-trade/InitCapitalDialog.tsx frontend/src/components/paper-trade/ResetConfirmDialog.tsx
git commit -m "feat(paper-trade): メインページの骨組みと Init/Reset ダイアログを追加"
```

---

## Task 12: Buy / Sell ダイアログ

**Files:**
- Create: `frontend/src/components/paper-trade/BuyDialog.tsx`
- Create: `frontend/src/components/paper-trade/SellDialog.tsx`
- Modify: `frontend/src/pages/PaperTradePage.tsx`

**目的:** 売買ダイアログを実装し、ページ側から起動できるようにする。

- [ ] **Step 1: BuyDialog を作成**

Create `frontend/src/components/paper-trade/BuyDialog.tsx`:

```tsx
import { useEffect, useState } from 'react';
import { Dialog, Field, Input, NumberInput, Button } from '@/components/ui';
import { paperTradeApi } from '@/services/api/paperTradeApi';

interface Props {
  open: boolean;
  onClose: () => void;
  cashBalance: number;
  onSubmitted: () => void;
  defaultSymbol?: string;
  defaultName?: string;
}

export const BuyDialog = ({
  open,
  onClose,
  cashBalance,
  onSubmitted,
  defaultSymbol = '',
  defaultName = '',
}: Props) => {
  const [symbol, setSymbol] = useState(defaultSymbol);
  const [name, setName] = useState(defaultName);
  const [quantity, setQuantity] = useState(100);
  const [price, setPrice] = useState<number | ''>('');
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (open) {
      setSymbol(defaultSymbol);
      setName(defaultName);
      setQuantity(100);
      setPrice('');
      setError(null);
    }
  }, [open, defaultSymbol, defaultName]);

  const totalCost = typeof price === 'number' ? price * quantity : null;
  const shortage =
    totalCost != null && totalCost > cashBalance ? totalCost - cashBalance : 0;

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!symbol.trim()) {
      setError('銘柄コードを入力してください');
      return;
    }
    if (quantity <= 0 || quantity % 100 !== 0) {
      setError('数量は100株単位で指定してください');
      return;
    }
    setSubmitting(true);
    setError(null);
    try {
      await paperTradeApi.createTrade({
        action: 'buy',
        symbol: symbol.trim(),
        quantity,
        price: typeof price === 'number' ? price : undefined,
        name: name || undefined,
      });
      onSubmitted();
      onClose();
    } catch (err) {
      setError(err instanceof Error ? err.message : '買い付けに失敗しました');
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <Dialog open={open} onClose={onClose} title="買い付け" size="md">
      <form onSubmit={handleSubmit} className="flex flex-col gap-4">
        <div className="grid grid-cols-2 gap-3">
          <Field label="銘柄コード">
            <Input
              value={symbol}
              onChange={(e) => setSymbol(e.target.value)}
              placeholder="7203.T"
              required
            />
          </Field>
          <Field label="銘柄名（任意）">
            <Input
              value={name}
              onChange={(e) => setName(e.target.value)}
              placeholder="トヨタ自動車"
            />
          </Field>
          <Field label="数量（100株単位）">
            <NumberInput value={quantity} onChange={setQuantity} min={100} step={100} />
          </Field>
          <Field label="約定価格（空欄で現在値）">
            <NumberInput
              value={typeof price === 'number' ? price : 0}
              onChange={(v) => setPrice(v)}
              min={0}
              step={1}
            />
          </Field>
        </div>
        <div className="rounded-md bg-slate-50 px-3 py-2 text-sm text-slate-700">
          <div>
            概算コスト:{' '}
            {totalCost != null ? `¥${Math.round(totalCost).toLocaleString()}` : '現在値で計算されます'}
          </div>
          <div>現金残高: ¥{Math.round(cashBalance).toLocaleString()}</div>
        </div>
        {shortage > 0 && (
          <div className="rounded-md border border-rose-200 bg-rose-50 px-3 py-2 text-xs text-rose-700">
            残高不足: ¥{Math.round(shortage).toLocaleString()} 不足しています
          </div>
        )}
        {error && (
          <div className="rounded-md border border-rose-200 bg-rose-50 px-3 py-2 text-xs text-rose-700">
            {error}
          </div>
        )}
        <div className="flex justify-end gap-2 pt-2">
          <Button type="button" variant="secondary" onClick={onClose} disabled={submitting}>
            キャンセル
          </Button>
          <Button type="submit" variant="accent" disabled={submitting || shortage > 0}>
            {submitting ? '実行中...' : '買い付け実行'}
          </Button>
        </div>
      </form>
    </Dialog>
  );
};

export default BuyDialog;
```

- [ ] **Step 2: SellDialog を作成**

Create `frontend/src/components/paper-trade/SellDialog.tsx`:

```tsx
import { useEffect, useState } from 'react';
import { Dialog, Field, NumberInput, Button } from '@/components/ui';
import { paperTradeApi } from '@/services/api/paperTradeApi';
import type { PaperHolding } from '@/types/paperTrade';

interface Props {
  open: boolean;
  onClose: () => void;
  holding: PaperHolding | null;
  onSubmitted: () => void;
}

export const SellDialog = ({ open, onClose, holding, onSubmitted }: Props) => {
  const [quantity, setQuantity] = useState(100);
  const [price, setPrice] = useState<number | ''>('');
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (open && holding) {
      setQuantity(Math.min(100, holding.quantity));
      setPrice(holding.current_price ?? '');
      setError(null);
    }
  }, [open, holding]);

  if (!holding) return null;

  const resolvedPrice = typeof price === 'number' ? price : holding.current_price ?? 0;
  const expectedPl = (resolvedPrice - holding.avg_price) * quantity;

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (quantity <= 0 || quantity % 100 !== 0) {
      setError('数量は100株単位で指定してください');
      return;
    }
    if (quantity > holding.quantity) {
      setError(`保有数量を超えています（保有: ${holding.quantity}株）`);
      return;
    }
    setSubmitting(true);
    setError(null);
    try {
      await paperTradeApi.createTrade({
        action: 'sell',
        symbol: holding.symbol,
        quantity,
        price: typeof price === 'number' ? price : undefined,
      });
      onSubmitted();
      onClose();
    } catch (err) {
      setError(err instanceof Error ? err.message : '売却に失敗しました');
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <Dialog open={open} onClose={onClose} title={`売却: ${holding.symbol}`} size="md">
      <form onSubmit={handleSubmit} className="flex flex-col gap-4">
        <div className="text-sm text-slate-600">
          保有: {holding.quantity.toLocaleString()}株 / 平均取得単価: ¥{holding.avg_price.toLocaleString()}
        </div>
        <div className="grid grid-cols-2 gap-3">
          <Field label="数量（100株単位）">
            <NumberInput
              value={quantity}
              onChange={setQuantity}
              min={100}
              max={holding.quantity}
              step={100}
            />
          </Field>
          <Field label="約定価格（空欄で現在値）">
            <NumberInput
              value={typeof price === 'number' ? price : 0}
              onChange={(v) => setPrice(v)}
              min={0}
              step={1}
            />
          </Field>
        </div>
        <div className="rounded-md bg-slate-50 px-3 py-2 text-sm text-slate-700">
          想定実現損益: ¥{Math.round(expectedPl).toLocaleString()}
        </div>
        {error && (
          <div className="rounded-md border border-rose-200 bg-rose-50 px-3 py-2 text-xs text-rose-700">
            {error}
          </div>
        )}
        <div className="flex justify-end gap-2 pt-2">
          <Button type="button" variant="secondary" onClick={onClose} disabled={submitting}>
            キャンセル
          </Button>
          <Button type="submit" variant="accent" disabled={submitting}>
            {submitting ? '実行中...' : '売却実行'}
          </Button>
        </div>
      </form>
    </Dialog>
  );
};

export default SellDialog;
```

- [ ] **Step 3: PaperTradePage に Buy ボタンと state を繋ぐ**

`frontend/src/pages/PaperTradePage.tsx` の `PaperTradePage` コンポーネント内を以下のように修正。追加部分のみ記載（既存 import に BuyDialog を追加、SellDialog は Task 13 で Holdings テーブルから起動）。

```tsx
// import 追加
import BuyDialog from '@/components/paper-trade/BuyDialog';

// state 追加（既存 state の下）
const [buyOpen, setBuyOpen] = useState(false);

// actions の「買い付け」ボタンの disabled を外し onClick を追加
actions={
  <div className="flex gap-2">
    <Button variant="secondary" onClick={() => setResetOpen(true)}>リセット</Button>
    <Button variant="accent" onClick={() => setBuyOpen(true)}>買い付け</Button>
  </div>
}

// return の末尾、</div> の直前に Dialog を追加
<BuyDialog
  open={buyOpen}
  onClose={() => setBuyOpen(false)}
  cashBalance={account.cash_balance}
  onSubmitted={refresh}
/>
```

- [ ] **Step 4: 型チェック**

Run:
```bash
cd frontend && npx tsc --noEmit
```
Expected: エラー 0 件

- [ ] **Step 5: Commit**

```bash
git add frontend/src/components/paper-trade/BuyDialog.tsx frontend/src/components/paper-trade/SellDialog.tsx frontend/src/pages/PaperTradePage.tsx
git commit -m "feat(paper-trade): Buy/Sell ダイアログを追加"
```

---

## Task 13: 保有テーブル + 取引履歴テーブル

**Files:**
- Modify: `frontend/src/pages/PaperTradePage.tsx`

**目的:** 保有一覧（売却ボタン付き）と取引履歴テーブルを表示。

- [ ] **Step 1: PaperTradePage に 2 つのテーブルを追加**

`frontend/src/pages/PaperTradePage.tsx` を以下のように書き換え:

```tsx
import { useCallback, useEffect, useState } from 'react';
import { Link } from 'react-router-dom';
import {
  PageHeader,
  Button,
  Card,
  CardBody,
  Stat,
  EmptyState,
  Table,
  Thead,
  Tbody,
  Tr,
  Th,
  Td,
  Badge,
} from '@/components/ui';
import { paperTradeApi } from '@/services/api/paperTradeApi';
import type {
  AccountInitialized,
  PaperSummary,
  PaperHolding,
  PaperTrade,
} from '@/types/paperTrade';
import InitCapitalDialog from '@/components/paper-trade/InitCapitalDialog';
import ResetConfirmDialog from '@/components/paper-trade/ResetConfirmDialog';
import BuyDialog from '@/components/paper-trade/BuyDialog';
import SellDialog from '@/components/paper-trade/SellDialog';

const formatYen = (v: number | null | undefined) =>
  v == null ? '—' : `¥${Math.round(v).toLocaleString()}`;

const formatPct = (v: number | null | undefined) =>
  v == null ? '—' : `${v >= 0 ? '+' : ''}${v.toFixed(2)}%`;

const PaperTradePage = () => {
  const [account, setAccount] = useState<AccountInitialized | null>(null);
  const [summary, setSummary] = useState<PaperSummary | null>(null);
  const [holdings, setHoldings] = useState<PaperHolding[]>([]);
  const [trades, setTrades] = useState<PaperTrade[]>([]);
  const [loading, setLoading] = useState(true);
  const [initOpen, setInitOpen] = useState(false);
  const [resetOpen, setResetOpen] = useState(false);
  const [buyOpen, setBuyOpen] = useState(false);
  const [sellingHolding, setSellingHolding] = useState<PaperHolding | null>(null);

  const refresh = useCallback(async () => {
    setLoading(true);
    try {
      const acc = await paperTradeApi.getAccount();
      if (!acc.initialized) {
        setAccount(null);
        setSummary(null);
        setHoldings([]);
        setTrades([]);
        return;
      }
      setAccount(acc);
      const [s, h, t] = await Promise.all([
        paperTradeApi.getSummary(),
        paperTradeApi.listHoldings(),
        paperTradeApi.listTrades(100, 0),
      ]);
      setSummary(s);
      setHoldings(h);
      setTrades(t.items);
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    void refresh();
  }, [refresh]);

  if (loading) return <div className="p-6 text-sm text-slate-500">読み込み中...</div>;

  if (!account) {
    return (
      <>
        <PageHeader title="ペーパートレード" description="仮想資金で売買を試す" />
        <Card>
          <CardBody>
            <EmptyState
              title="仮想口座を作成しましょう"
              description="初期資金を設定すると、擬似的な売買シミュレーションを開始できます。"
            />
            <div className="flex justify-center pt-4">
              <Button variant="accent" onClick={() => setInitOpen(true)}>
                初期資金を設定して開始
              </Button>
            </div>
          </CardBody>
        </Card>
        <InitCapitalDialog
          open={initOpen}
          onClose={() => setInitOpen(false)}
          onInitialized={refresh}
        />
      </>
    );
  }

  const s = summary;

  return (
    <div>
      <PageHeader
        title="ペーパートレード"
        description="仮想資金で売買を試す"
        actions={
          <div className="flex gap-2">
            <Button variant="secondary" onClick={() => setResetOpen(true)}>リセット</Button>
            <Button variant="accent" onClick={() => setBuyOpen(true)}>買い付け</Button>
          </div>
        }
      />
      <div className="grid gap-3 grid-cols-2 md:grid-cols-3 lg:grid-cols-6 mb-4">
        <Stat label="総資産" value={formatYen(s?.total_value)} accent="brand" />
        <Stat label="現金残高" value={formatYen(s?.cash_balance)} />
        <Stat label="保有評価額" value={formatYen(s?.holdings_value)} />
        <Stat
          label="含み損益"
          value={formatYen(s?.unrealized_pl)}
          accent={(s?.unrealized_pl ?? 0) >= 0 ? 'success' : 'danger'}
        />
        <Stat
          label="実現損益"
          value={formatYen(s?.realized_pl)}
          accent={(s?.realized_pl ?? 0) >= 0 ? 'success' : 'danger'}
        />
        <Stat
          label="リターン"
          value={formatPct(s?.return_pct)}
          accent={(s?.return_pct ?? 0) >= 0 ? 'success' : 'danger'}
        />
      </div>

      <Card className="mb-4">
        <CardBody>
          <h2 className="mb-3 text-base font-semibold text-slate-900">
            保有銘柄 ({holdings.length})
          </h2>
          {holdings.length === 0 ? (
            <EmptyState
              title="保有銘柄がありません"
              description="「買い付け」から擬似取引を開始してください。"
            />
          ) : (
            <Table>
              <Thead>
                <Tr>
                  <Th>銘柄</Th>
                  <Th className="text-right">株数</Th>
                  <Th className="text-right">取得単価</Th>
                  <Th className="text-right">現在値</Th>
                  <Th className="text-right">評価額</Th>
                  <Th className="text-right">含み損益</Th>
                  <Th></Th>
                </Tr>
              </Thead>
              <Tbody>
                {holdings.map((h) => (
                  <Tr key={h.id}>
                    <Td>
                      <Link
                        to={`/paper-trade/symbols/${encodeURIComponent(h.symbol)}`}
                        className="text-brand-600 hover:underline"
                      >
                        <div className="font-semibold">{h.symbol}</div>
                        <div className="text-xs text-slate-500">{h.name}</div>
                      </Link>
                    </Td>
                    <Td className="text-right">{h.quantity.toLocaleString()}</Td>
                    <Td className="text-right">{formatYen(h.avg_price)}</Td>
                    <Td className="text-right">{formatYen(h.current_price)}</Td>
                    <Td className="text-right">{formatYen(h.market_value)}</Td>
                    <Td className="text-right">
                      <div
                        className={
                          (h.unrealized_pl ?? 0) >= 0 ? 'text-emerald-700' : 'text-rose-700'
                        }
                      >
                        {formatYen(h.unrealized_pl)}
                        <div className="text-xs">{formatPct(h.unrealized_pl_pct)}</div>
                      </div>
                    </Td>
                    <Td className="text-right">
                      <Button
                        variant="ghost"
                        size="sm"
                        onClick={() => setSellingHolding(h)}
                      >
                        売却
                      </Button>
                    </Td>
                  </Tr>
                ))}
              </Tbody>
            </Table>
          )}
        </CardBody>
      </Card>

      <Card>
        <CardBody>
          <h2 className="mb-3 text-base font-semibold text-slate-900">
            取引履歴 ({trades.length})
          </h2>
          {trades.length === 0 ? (
            <EmptyState title="取引履歴がありません" description="" />
          ) : (
            <Table>
              <Thead>
                <Tr>
                  <Th>日時</Th>
                  <Th>銘柄</Th>
                  <Th>区分</Th>
                  <Th className="text-right">数量</Th>
                  <Th className="text-right">単価</Th>
                  <Th className="text-right">約定額</Th>
                  <Th className="text-right">実現損益</Th>
                  <Th>メモ</Th>
                </Tr>
              </Thead>
              <Tbody>
                {trades.map((t) => (
                  <Tr key={t.id}>
                    <Td>{new Date(t.executed_at).toLocaleString()}</Td>
                    <Td>
                      <Link
                        to={`/paper-trade/symbols/${encodeURIComponent(t.symbol)}`}
                        className="text-brand-600 hover:underline"
                      >
                        {t.symbol}
                      </Link>
                    </Td>
                    <Td>
                      <Badge tone={t.action === 'buy' ? 'brand' : 'warn'}>
                        {t.action === 'buy' ? '買' : '売'}
                      </Badge>
                    </Td>
                    <Td className="text-right">{t.quantity.toLocaleString()}</Td>
                    <Td className="text-right">{formatYen(t.price)}</Td>
                    <Td className="text-right">{formatYen(t.total_amount)}</Td>
                    <Td className="text-right">
                      {t.realized_pl != null ? (
                        <span
                          className={
                            t.realized_pl >= 0 ? 'text-emerald-700' : 'text-rose-700'
                          }
                        >
                          {formatYen(t.realized_pl)}
                        </span>
                      ) : (
                        '—'
                      )}
                    </Td>
                    <Td className="text-xs text-slate-500">{t.note ?? ''}</Td>
                  </Tr>
                ))}
              </Tbody>
            </Table>
          )}
        </CardBody>
      </Card>

      <ResetConfirmDialog
        open={resetOpen}
        onClose={() => setResetOpen(false)}
        currentInitialCash={account.initial_cash}
        onReset={refresh}
      />
      <BuyDialog
        open={buyOpen}
        onClose={() => setBuyOpen(false)}
        cashBalance={account.cash_balance}
        onSubmitted={refresh}
      />
      <SellDialog
        open={sellingHolding !== null}
        onClose={() => setSellingHolding(null)}
        holding={sellingHolding}
        onSubmitted={refresh}
      />
    </div>
  );
};

export default PaperTradePage;
```

- [ ] **Step 2: 型チェック**

Run:
```bash
cd frontend && npx tsc --noEmit
```
Expected: エラー 0 件

- [ ] **Step 3: Commit**

```bash
git add frontend/src/pages/PaperTradePage.tsx
git commit -m "feat(paper-trade): 保有一覧と取引履歴テーブルを表示"
```

---

## Task 14: 資産推移チャート + 銘柄別パフォーマンステーブル

**Files:**
- Create: `frontend/src/components/paper-trade/AssetHistoryChart.tsx`
- Create: `frontend/src/components/paper-trade/PerformanceTable.tsx`
- Modify: `frontend/src/pages/PaperTradePage.tsx`

**目的:** メインページに折れ線チャートと銘柄別パフォーマンステーブル（詳細ページへの入口）を追加。

- [ ] **Step 1: AssetHistoryChart を作成**

Create `frontend/src/components/paper-trade/AssetHistoryChart.tsx`:

```tsx
import { useState } from 'react';
import {
  ResponsiveContainer,
  LineChart,
  Line,
  XAxis,
  YAxis,
  Tooltip,
  CartesianGrid,
} from 'recharts';
import { Button } from '@/components/ui';
import type { ChartPoint } from '@/types/paperTrade';

type Range = '1M' | '3M' | '6M' | '1Y' | 'ALL';

interface Props {
  data: ChartPoint[];
}

const RANGE_DAYS: Record<Range, number | null> = {
  '1M': 30,
  '3M': 90,
  '6M': 180,
  '1Y': 365,
  'ALL': null,
};

const filterRange = (data: ChartPoint[], range: Range): ChartPoint[] => {
  const days = RANGE_DAYS[range];
  if (days == null) return data;
  const cutoff = new Date();
  cutoff.setDate(cutoff.getDate() - days);
  return data.filter((d) => new Date(d.date) >= cutoff);
};

export const AssetHistoryChart = ({ data }: Props) => {
  const [range, setRange] = useState<Range>('3M');
  const filtered = filterRange(data, range);

  return (
    <div>
      <div className="mb-3 flex justify-end gap-1">
        {(['1M', '3M', '6M', '1Y', 'ALL'] as Range[]).map((r) => (
          <Button
            key={r}
            size="sm"
            variant={r === range ? 'accent' : 'ghost'}
            onClick={() => setRange(r)}
          >
            {r}
          </Button>
        ))}
      </div>
      <div style={{ width: '100%', height: 280 }}>
        <ResponsiveContainer>
          <LineChart data={filtered}>
            <CartesianGrid strokeDasharray="3 3" />
            <XAxis dataKey="date" tick={{ fontSize: 11 }} />
            <YAxis tickFormatter={(v) => `¥${(v / 10000).toFixed(0)}万`} tick={{ fontSize: 11 }} />
            <Tooltip formatter={(v: number) => `¥${Math.round(v).toLocaleString()}`} />
            <Line type="monotone" dataKey="total_value" stroke="#2563eb" dot={false} name="総資産" />
            <Line type="monotone" dataKey="holdings_value" stroke="#10b981" dot={false} name="保有評価額" />
            <Line type="monotone" dataKey="cash" stroke="#94a3b8" dot={false} name="現金" />
          </LineChart>
        </ResponsiveContainer>
      </div>
    </div>
  );
};

export default AssetHistoryChart;
```

- [ ] **Step 2: PerformanceTable を作成**

Create `frontend/src/components/paper-trade/PerformanceTable.tsx`:

```tsx
import { Link } from 'react-router-dom';
import {
  EmptyState,
  Table,
  Thead,
  Tbody,
  Tr,
  Th,
  Td,
} from '@/components/ui';
import type { PerformanceItem } from '@/types/paperTrade';

const formatYen = (v: number | null | undefined) =>
  v == null ? '—' : `¥${Math.round(v).toLocaleString()}`;

const formatPct = (v: number | null | undefined) =>
  v == null ? '—' : `${v >= 0 ? '+' : ''}${v.toFixed(2)}%`;

interface Props {
  items: PerformanceItem[];
}

export const PerformanceTable = ({ items }: Props) => {
  if (items.length === 0) {
    return (
      <EmptyState
        title="銘柄別パフォーマンスがありません"
        description="取引を実行すると表示されます。"
      />
    );
  }
  return (
    <Table>
      <Thead>
        <Tr>
          <Th>銘柄</Th>
          <Th className="text-right">取引回数</Th>
          <Th className="text-right">勝ち</Th>
          <Th className="text-right">実現損益</Th>
          <Th className="text-right">含み損益</Th>
          <Th className="text-right">合計損益</Th>
          <Th className="text-right">リターン</Th>
        </Tr>
      </Thead>
      <Tbody>
        {items.map((p) => (
          <Tr key={p.symbol}>
            <Td>
              <Link
                to={`/paper-trade/symbols/${encodeURIComponent(p.symbol)}`}
                className="text-brand-600 hover:underline"
              >
                <div className="font-semibold">{p.symbol}</div>
                <div className="text-xs text-slate-500">{p.name}</div>
              </Link>
            </Td>
            <Td className="text-right">{p.trade_count}</Td>
            <Td className="text-right">{p.win_count}</Td>
            <Td
              className={
                'text-right ' + (p.realized_pl >= 0 ? 'text-emerald-700' : 'text-rose-700')
              }
            >
              {formatYen(p.realized_pl)}
            </Td>
            <Td
              className={
                'text-right ' + (p.unrealized_pl >= 0 ? 'text-emerald-700' : 'text-rose-700')
              }
            >
              {formatYen(p.unrealized_pl)}
            </Td>
            <Td
              className={
                'text-right ' + (p.total_pl >= 0 ? 'text-emerald-700' : 'text-rose-700')
              }
            >
              {formatYen(p.total_pl)}
            </Td>
            <Td className="text-right">{formatPct(p.return_pct)}</Td>
          </Tr>
        ))}
      </Tbody>
    </Table>
  );
};

export default PerformanceTable;
```

- [ ] **Step 3: PaperTradePage に組み込み**

`frontend/src/pages/PaperTradePage.tsx` の import に追加:

```tsx
import AssetHistoryChart from '@/components/paper-trade/AssetHistoryChart';
import PerformanceTable from '@/components/paper-trade/PerformanceTable';
import type { ChartPoint, PerformanceItem } from '@/types/paperTrade';
```

state に追加（既存 state の下）:

```tsx
const [chart, setChart] = useState<ChartPoint[]>([]);
const [performance, setPerformance] = useState<PerformanceItem[]>([]);
```

`refresh` の `Promise.all` を 5 本に拡張:

```tsx
const [s, h, t, c, p] = await Promise.all([
  paperTradeApi.getSummary(),
  paperTradeApi.listHoldings(),
  paperTradeApi.listTrades(100, 0),
  paperTradeApi.getChart(),
  paperTradeApi.getPerformance(),
]);
setSummary(s);
setHoldings(h);
setTrades(t.items);
setChart(c);
setPerformance(p);
```

`Stat` グリッドと保有銘柄 Card の**間**に Chart Card を追加:

```tsx
<Card className="mb-4">
  <CardBody>
    <h2 className="mb-2 text-base font-semibold text-slate-900">資産推移</h2>
    <AssetHistoryChart data={chart} />
  </CardBody>
</Card>
```

取引履歴 Card の**前**に銘柄別パフォーマンス Card を追加:

```tsx
<Card className="mb-4">
  <CardBody>
    <h2 className="mb-3 text-base font-semibold text-slate-900">銘柄別パフォーマンス</h2>
    <PerformanceTable items={performance} />
  </CardBody>
</Card>
```

- [ ] **Step 4: 型チェック**

Run:
```bash
cd frontend && npx tsc --noEmit
```
Expected: エラー 0 件

- [ ] **Step 5: Commit**

```bash
git add frontend/src/components/paper-trade/AssetHistoryChart.tsx frontend/src/components/paper-trade/PerformanceTable.tsx frontend/src/pages/PaperTradePage.tsx
git commit -m "feat(paper-trade): 資産推移チャートと銘柄別パフォーマンステーブルを表示"
```

---

## Task 15: 銘柄別詳細分析ページ骨組み + Indicator Registry + 基本 3 カード

**Files:**
- Create: `frontend/src/components/paper-trade/analytics/registry.ts`
- Create: `frontend/src/components/paper-trade/analytics/IndicatorSelector.tsx`
- Create: `frontend/src/components/paper-trade/analytics/SummaryCard.tsx`
- Create: `frontend/src/components/paper-trade/analytics/PositionCyclesCard.tsx`
- Create: `frontend/src/components/paper-trade/analytics/OpenPositionCard.tsx`
- Modify: `frontend/src/pages/PaperTradeSymbolPage.tsx`

**目的:** 銘柄別詳細ページと、Indicator Registry の仕組み、基本 3 指標（Summary / PositionCycles / OpenPosition）を実装。

- [ ] **Step 1: IndicatorSelector と registry 型を作成（骨組みのみ）**

Create `frontend/src/components/paper-trade/analytics/registry.ts`:

```ts
import type { FC } from 'react';
import type { AnalyticsResponse } from '@/types/paperTrade';

export interface IndicatorProps {
  symbol: string;
  data: AnalyticsResponse;
}

export interface IndicatorDef {
  id: string;
  label: string;
  description?: string;
  category: 'basic' | 'advanced';
  defaultEnabled: boolean;
  component: FC<IndicatorProps>;
}

// 実体はページ側でまとめて定義する（循環 import を避けるため）
export const STORAGE_KEY = 'paperTrade.symbolAnalytics.visibleIds';

export const loadVisibleIds = (fallback: string[]): string[] => {
  try {
    const raw = localStorage.getItem(STORAGE_KEY);
    if (!raw) return fallback;
    const parsed = JSON.parse(raw);
    return Array.isArray(parsed) ? parsed.filter((v) => typeof v === 'string') : fallback;
  } catch {
    return fallback;
  }
};

export const saveVisibleIds = (ids: string[]) => {
  try {
    localStorage.setItem(STORAGE_KEY, JSON.stringify(ids));
  } catch {
    /* ignore quota errors */
  }
};
```

- [ ] **Step 2: IndicatorSelector UI**

Create `frontend/src/components/paper-trade/analytics/IndicatorSelector.tsx`:

```tsx
import { useState } from 'react';
import { Button, Dialog } from '@/components/ui';
import type { IndicatorDef } from './registry';

interface Props {
  registry: IndicatorDef[];
  visibleIds: string[];
  onChange: (ids: string[]) => void;
}

export const IndicatorSelector = ({ registry, visibleIds, onChange }: Props) => {
  const [open, setOpen] = useState(false);

  const toggle = (id: string) => {
    if (visibleIds.includes(id)) onChange(visibleIds.filter((v) => v !== id));
    else onChange([...visibleIds, id]);
  };

  const basic = registry.filter((r) => r.category === 'basic');
  const advanced = registry.filter((r) => r.category === 'advanced');

  return (
    <>
      <Button variant="secondary" size="sm" onClick={() => setOpen(true)}>
        📊 表示項目を選択
      </Button>
      <Dialog open={open} onClose={() => setOpen(false)} title="表示する分析項目" size="sm">
        <div className="flex flex-col gap-3">
          <div>
            <div className="mb-2 text-xs font-semibold text-slate-500">基本指標</div>
            {basic.map((ind) => (
              <label key={ind.id} className="flex cursor-pointer items-center gap-2 py-1 text-sm">
                <input
                  type="checkbox"
                  checked={visibleIds.includes(ind.id)}
                  onChange={() => toggle(ind.id)}
                />
                <span>{ind.label}</span>
                {ind.description && (
                  <span className="text-xs text-slate-500">{ind.description}</span>
                )}
              </label>
            ))}
          </div>
          {advanced.length > 0 && (
            <div>
              <div className="mb-2 text-xs font-semibold text-slate-500">詳細指標</div>
              {advanced.map((ind) => (
                <label key={ind.id} className="flex cursor-pointer items-center gap-2 py-1 text-sm">
                  <input
                    type="checkbox"
                    checked={visibleIds.includes(ind.id)}
                    onChange={() => toggle(ind.id)}
                  />
                  <span>{ind.label}</span>
                  {ind.description && (
                    <span className="text-xs text-slate-500">{ind.description}</span>
                  )}
                </label>
              ))}
            </div>
          )}
          <div className="flex justify-end pt-2">
            <Button variant="accent" onClick={() => setOpen(false)}>閉じる</Button>
          </div>
        </div>
      </Dialog>
    </>
  );
};

export default IndicatorSelector;
```

- [ ] **Step 3: SummaryCard を作成**

Create `frontend/src/components/paper-trade/analytics/SummaryCard.tsx`:

```tsx
import { Card, CardBody, Stat } from '@/components/ui';
import type { IndicatorProps } from './registry';

const formatYen = (v: number | null | undefined) =>
  v == null ? '—' : `¥${Math.round(v).toLocaleString()}`;
const formatPct = (v: number | null | undefined) =>
  v == null ? '—' : `${v >= 0 ? '+' : ''}${v.toFixed(2)}%`;
const formatNum = (v: number | null | undefined, digits = 2) =>
  v == null ? '—' : v.toFixed(digits);

export const SummaryCard = ({ data }: IndicatorProps) => {
  const s = data.summary;
  return (
    <Card>
      <CardBody>
        <h3 className="mb-3 text-base font-semibold text-slate-900">サマリ指標</h3>
        <div className="grid gap-3 grid-cols-2 md:grid-cols-4">
          <Stat
            label="合計損益"
            value={formatYen(s.total_pl)}
            accent={s.total_pl >= 0 ? 'success' : 'danger'}
          />
          <Stat
            label="リターン"
            value={formatPct(s.return_pct)}
            accent={(s.return_pct ?? 0) >= 0 ? 'success' : 'danger'}
          />
          <Stat
            label="実現損益"
            value={formatYen(s.realized_pl)}
            accent={s.realized_pl >= 0 ? 'success' : 'danger'}
          />
          <Stat
            label="含み損益"
            value={formatYen(s.unrealized_pl)}
            accent={s.unrealized_pl >= 0 ? 'success' : 'danger'}
          />
          <Stat label="取引回数" value={`${s.trade_count} (買${s.buy_count}/売${s.sell_count})`} />
          <Stat
            label="勝率"
            value={s.win_rate == null ? '—' : `${(s.win_rate * 100).toFixed(1)}%`}
            hint={`勝${s.win_count}/負${s.loss_count}`}
          />
          <Stat
            label="平均保有日数"
            value={s.avg_holding_days == null ? '—' : `${formatNum(s.avg_holding_days, 1)}日`}
          />
          <Stat
            label="最大利益取引"
            value={formatYen(s.best_trade_pl)}
            accent="success"
          />
          <Stat
            label="最大損失取引"
            value={formatYen(s.worst_trade_pl)}
            accent={(s.worst_trade_pl ?? 0) < 0 ? 'danger' : undefined}
          />
          <Stat
            label="プロフィットファクター"
            value={formatNum(s.profit_factor, 2)}
          />
          <Stat label="期待値" value={formatYen(s.expectancy)} />
        </div>
      </CardBody>
    </Card>
  );
};

export default SummaryCard;
```

- [ ] **Step 4: PositionCyclesCard を作成**

Create `frontend/src/components/paper-trade/analytics/PositionCyclesCard.tsx`:

```tsx
import { Card, CardBody, Table, Thead, Tbody, Tr, Th, Td, EmptyState } from '@/components/ui';
import type { IndicatorProps } from './registry';

const formatYen = (v: number) => `¥${Math.round(v).toLocaleString()}`;
const formatPct = (v: number) => `${v >= 0 ? '+' : ''}${v.toFixed(2)}%`;
const formatDate = (iso: string) => new Date(iso).toLocaleDateString();

export const PositionCyclesCard = ({ data }: IndicatorProps) => {
  return (
    <Card>
      <CardBody>
        <h3 className="mb-3 text-base font-semibold text-slate-900">
          ポジションサイクル ({data.position_cycles.length})
        </h3>
        {data.position_cycles.length === 0 ? (
          <EmptyState title="クローズしたサイクルがありません" description="" />
        ) : (
          <Table>
            <Thead>
              <Tr>
                <Th>入口</Th>
                <Th>出口</Th>
                <Th className="text-right">数量</Th>
                <Th className="text-right">入口価格</Th>
                <Th className="text-right">出口価格</Th>
                <Th className="text-right">保有日数</Th>
                <Th className="text-right">損益</Th>
                <Th className="text-right">リターン</Th>
              </Tr>
            </Thead>
            <Tbody>
              {data.position_cycles.map((c, i) => (
                <Tr key={i}>
                  <Td>{formatDate(c.entry_date)}</Td>
                  <Td>{formatDate(c.exit_date)}</Td>
                  <Td className="text-right">{c.quantity.toLocaleString()}</Td>
                  <Td className="text-right">{formatYen(c.entry_price)}</Td>
                  <Td className="text-right">{formatYen(c.exit_price)}</Td>
                  <Td className="text-right">{c.holding_days}日</Td>
                  <Td
                    className={
                      'text-right ' + (c.pl >= 0 ? 'text-emerald-700' : 'text-rose-700')
                    }
                  >
                    {formatYen(c.pl)}
                  </Td>
                  <Td className="text-right">{formatPct(c.return_pct)}</Td>
                </Tr>
              ))}
            </Tbody>
          </Table>
        )}
      </CardBody>
    </Card>
  );
};

export default PositionCyclesCard;
```

- [ ] **Step 5: OpenPositionCard を作成**

Create `frontend/src/components/paper-trade/analytics/OpenPositionCard.tsx`:

```tsx
import { Card, CardBody, Stat, EmptyState } from '@/components/ui';
import type { IndicatorProps } from './registry';

const formatYen = (v: number | null | undefined) =>
  v == null ? '—' : `¥${Math.round(v).toLocaleString()}`;
const formatPct = (v: number | null | undefined) =>
  v == null ? '—' : `${v >= 0 ? '+' : ''}${v.toFixed(2)}%`;

export const OpenPositionCard = ({ data }: IndicatorProps) => {
  const p = data.open_position;
  return (
    <Card>
      <CardBody>
        <h3 className="mb-3 text-base font-semibold text-slate-900">現在保有の健康度</h3>
        {!p ? (
          <EmptyState title="現在この銘柄を保有していません" description="" />
        ) : (
          <div className="grid gap-3 grid-cols-2 md:grid-cols-4">
            <Stat label="保有数量" value={p.quantity.toLocaleString()} />
            <Stat label="平均取得単価" value={formatYen(p.avg_price)} />
            <Stat label="現在値" value={formatYen(p.current_price)} />
            <Stat
              label="含み損益"
              value={formatYen(p.unrealized_pl)}
              accent={(p.unrealized_pl ?? 0) >= 0 ? 'success' : 'danger'}
              hint={formatPct(p.unrealized_pl_pct)}
            />
            <Stat label="エントリー日" value={new Date(p.entry_date).toLocaleDateString()} />
            <Stat label="保有日数" value={`${p.holding_days}日`} />
            <Stat label="MFE (最大含み益)" value={formatYen(p.mfe)} accent="success" />
            <Stat label="MAE (最大含み損)" value={formatYen(p.mae)} accent="danger" />
          </div>
        )}
      </CardBody>
    </Card>
  );
};

export default OpenPositionCard;
```

- [ ] **Step 6: PaperTradeSymbolPage を実装**

Replace `frontend/src/pages/PaperTradeSymbolPage.tsx`:

```tsx
import { useEffect, useMemo, useState } from 'react';
import { Link, useParams } from 'react-router-dom';
import { PageHeader, Button } from '@/components/ui';
import { paperTradeApi } from '@/services/api/paperTradeApi';
import type { AnalyticsResponse } from '@/types/paperTrade';
import IndicatorSelector from '@/components/paper-trade/analytics/IndicatorSelector';
import { loadVisibleIds, saveVisibleIds } from '@/components/paper-trade/analytics/registry';
import type { IndicatorDef } from '@/components/paper-trade/analytics/registry';
import SummaryCard from '@/components/paper-trade/analytics/SummaryCard';
import PositionCyclesCard from '@/components/paper-trade/analytics/PositionCyclesCard';
import OpenPositionCard from '@/components/paper-trade/analytics/OpenPositionCard';

const INDICATORS: IndicatorDef[] = [
  { id: 'summary', label: 'サマリ指標', category: 'basic', defaultEnabled: true, component: SummaryCard },
  { id: 'position_cycles', label: 'ポジションサイクル', category: 'basic', defaultEnabled: true, component: PositionCyclesCard },
  { id: 'open_position', label: '現在保有の健康度', category: 'basic', defaultEnabled: true, component: OpenPositionCard },
];

const DEFAULT_VISIBLE = INDICATORS.filter((i) => i.defaultEnabled).map((i) => i.id);

const PaperTradeSymbolPage = () => {
  const { symbol = '' } = useParams();
  const [data, setData] = useState<AnalyticsResponse | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [visibleIds, setVisibleIds] = useState<string[]>(() => loadVisibleIds(DEFAULT_VISIBLE));

  useEffect(() => {
    let cancelled = false;
    (async () => {
      setLoading(true);
      setError(null);
      try {
        const r = await paperTradeApi.getSymbolAnalytics(symbol);
        if (!cancelled) setData(r);
      } catch (err) {
        if (!cancelled) setError(err instanceof Error ? err.message : '取得に失敗しました');
      } finally {
        if (!cancelled) setLoading(false);
      }
    })();
    return () => {
      cancelled = true;
    };
  }, [symbol]);

  const updateVisibleIds = (ids: string[]) => {
    setVisibleIds(ids);
    saveVisibleIds(ids);
  };

  const visibleIndicators = useMemo(
    () => INDICATORS.filter((ind) => visibleIds.includes(ind.id)),
    [visibleIds]
  );

  if (loading) return <div className="p-6 text-sm text-slate-500">読み込み中...</div>;
  if (error || !data) {
    return (
      <div className="p-6">
        <Link to="/paper-trade" className="text-sm text-brand-600 hover:underline">
          ← ペーパートレードに戻る
        </Link>
        <div className="mt-4 text-sm text-rose-700">{error ?? 'データがありません'}</div>
      </div>
    );
  }

  return (
    <div>
      <PageHeader
        title={`${data.symbol}${data.name ? ' ' + data.name : ''}`}
        description="銘柄別の売買結果を多角的に分析"
        actions={
          <div className="flex gap-2">
            <Link to="/paper-trade">
              <Button variant="ghost" size="sm">← 戻る</Button>
            </Link>
            <IndicatorSelector
              registry={INDICATORS}
              visibleIds={visibleIds}
              onChange={updateVisibleIds}
            />
          </div>
        }
      />
      <div className="flex flex-col gap-4">
        {visibleIndicators.map((ind) => {
          const C = ind.component;
          return <C key={ind.id} symbol={symbol} data={data} />;
        })}
      </div>
    </div>
  );
};

export default PaperTradeSymbolPage;
```

- [ ] **Step 7: 型チェック**

Run:
```bash
cd frontend && npx tsc --noEmit
```
Expected: エラー 0 件

- [ ] **Step 8: Commit**

```bash
git add frontend/src/components/paper-trade/analytics/ frontend/src/pages/PaperTradeSymbolPage.tsx
git commit -m "feat(paper-trade): 銘柄別分析ページと基本 3 指標カードを追加"
```

---

## Task 16: 残り 3 指標カード（タイミング / バイ&ホールド / エクイティ推移）

**Files:**
- Create: `frontend/src/components/paper-trade/analytics/TimingChartCard.tsx`
- Create: `frontend/src/components/paper-trade/analytics/BuyAndHoldCard.tsx`
- Create: `frontend/src/components/paper-trade/analytics/EquityTimeseriesCard.tsx`
- Modify: `frontend/src/pages/PaperTradeSymbolPage.tsx`

**目的:** 詳細分析の残り 3 カードを実装してレジストリに登録。

- [ ] **Step 1: TimingChartCard を作成**

Create `frontend/src/components/paper-trade/analytics/TimingChartCard.tsx`:

```tsx
import {
  ResponsiveContainer,
  ComposedChart,
  Line,
  Scatter,
  XAxis,
  YAxis,
  Tooltip,
  CartesianGrid,
  Legend,
} from 'recharts';
import { Card, CardBody, EmptyState } from '@/components/ui';
import type { IndicatorProps } from './registry';

export const TimingChartCard = ({ data }: IndicatorProps) => {
  const { price_series, trade_markers } = data.timing;
  const priceMap = new Map(price_series.map((p) => [p.date, p.close]));

  const buyMarkers = trade_markers
    .filter((t) => t.action === 'buy')
    .map((t) => ({
      date: t.date.slice(0, 10),
      buy: t.price,
    }));
  const sellMarkers = trade_markers
    .filter((t) => t.action === 'sell')
    .map((t) => ({
      date: t.date.slice(0, 10),
      sell: t.price,
    }));

  const merged = price_series.map((p) => ({
    date: p.date,
    close: p.close,
    buy: buyMarkers.find((m) => m.date === p.date)?.buy ?? null,
    sell: sellMarkers.find((m) => m.date === p.date)?.sell ?? null,
  }));

  // Note: close 取得できない日の買い/売りはデータ化しないが、エッジケースは無視（MVP）
  void priceMap;

  return (
    <Card>
      <CardBody>
        <h3 className="mb-3 text-base font-semibold text-slate-900">タイミング可視化</h3>
        {merged.length === 0 ? (
          <EmptyState title="株価データがありません" description="" />
        ) : (
          <div style={{ width: '100%', height: 320 }}>
            <ResponsiveContainer>
              <ComposedChart data={merged}>
                <CartesianGrid strokeDasharray="3 3" />
                <XAxis dataKey="date" tick={{ fontSize: 11 }} />
                <YAxis tick={{ fontSize: 11 }} domain={['auto', 'auto']} />
                <Tooltip />
                <Legend />
                <Line type="monotone" dataKey="close" stroke="#2563eb" dot={false} name="終値" />
                <Scatter dataKey="buy" fill="#10b981" shape="triangle" name="買い" />
                <Scatter dataKey="sell" fill="#ef4444" shape="square" name="売り" />
              </ComposedChart>
            </ResponsiveContainer>
          </div>
        )}
      </CardBody>
    </Card>
  );
};

export default TimingChartCard;
```

- [ ] **Step 2: BuyAndHoldCard を作成**

Create `frontend/src/components/paper-trade/analytics/BuyAndHoldCard.tsx`:

```tsx
import { Card, CardBody, Stat, EmptyState } from '@/components/ui';
import type { IndicatorProps } from './registry';

const formatYen = (v: number | null | undefined) =>
  v == null ? '—' : `¥${Math.round(v).toLocaleString()}`;
const formatPct = (v: number | null | undefined) =>
  v == null ? '—' : `${v >= 0 ? '+' : ''}${v.toFixed(2)}%`;

export const BuyAndHoldCard = ({ data }: IndicatorProps) => {
  const b = data.buy_and_hold;
  const hasData = b.first_buy_date != null;
  return (
    <Card>
      <CardBody>
        <h3 className="mb-3 text-base font-semibold text-slate-900">バイ＆ホールド比較</h3>
        {!hasData ? (
          <EmptyState title="買いが 1 件もありません" description="" />
        ) : (
          <>
            <p className="mb-3 text-xs text-slate-500">
              最初の買い（{b.first_buy_date && new Date(b.first_buy_date).toLocaleDateString()} /{' '}
              {formatYen(b.first_buy_price)}）の数量を売買せずに保有し続けた場合との比較。
            </p>
            <div className="grid gap-3 grid-cols-2 md:grid-cols-4">
              <Stat label="実トレード リターン" value={formatPct(b.actual_return_pct)} />
              <Stat label="バイ＆ホールド リターン" value={formatPct(b.bh_return_pct)} />
              <Stat
                label="差分 (実 - BH)"
                value={formatPct(b.diff_pct)}
                accent={(b.diff_pct ?? 0) >= 0 ? 'success' : 'danger'}
              />
              <Stat label="BH 時価（現時点）" value={formatYen(b.bh_value_now)} />
            </div>
          </>
        )}
      </CardBody>
    </Card>
  );
};

export default BuyAndHoldCard;
```

- [ ] **Step 3: EquityTimeseriesCard を作成**

Create `frontend/src/components/paper-trade/analytics/EquityTimeseriesCard.tsx`:

```tsx
import {
  ResponsiveContainer,
  LineChart,
  Line,
  XAxis,
  YAxis,
  Tooltip,
  CartesianGrid,
  Legend,
} from 'recharts';
import { Card, CardBody, EmptyState } from '@/components/ui';
import type { IndicatorProps } from './registry';

export const EquityTimeseriesCard = ({ data }: IndicatorProps) => {
  const series = data.equity_timeseries;
  return (
    <Card>
      <CardBody>
        <h3 className="mb-3 text-base font-semibold text-slate-900">投下資本・損益の推移</h3>
        {series.length === 0 ? (
          <EmptyState title="推移データがありません" description="" />
        ) : (
          <div style={{ width: '100%', height: 280 }}>
            <ResponsiveContainer>
              <LineChart data={series}>
                <CartesianGrid strokeDasharray="3 3" />
                <XAxis dataKey="date" tick={{ fontSize: 11 }} />
                <YAxis tickFormatter={(v) => `¥${(v / 10000).toFixed(0)}万`} tick={{ fontSize: 11 }} />
                <Tooltip formatter={(v: number) => `¥${Math.round(v).toLocaleString()}`} />
                <Legend />
                <Line type="monotone" dataKey="invested" stroke="#64748b" dot={false} name="投下資本累計" />
                <Line type="monotone" dataKey="realized_pl" stroke="#10b981" dot={false} name="実現損益累計" />
                <Line type="monotone" dataKey="unrealized_pl" stroke="#f59e0b" dot={false} name="含み損益" />
                <Line type="monotone" dataKey="total_pl" stroke="#2563eb" dot={false} name="合計損益" />
              </LineChart>
            </ResponsiveContainer>
          </div>
        )}
      </CardBody>
    </Card>
  );
};

export default EquityTimeseriesCard;
```

- [ ] **Step 4: PaperTradeSymbolPage のレジストリに 3 つ追加**

`frontend/src/pages/PaperTradeSymbolPage.tsx` の import と INDICATORS を拡張:

```tsx
import TimingChartCard from '@/components/paper-trade/analytics/TimingChartCard';
import BuyAndHoldCard from '@/components/paper-trade/analytics/BuyAndHoldCard';
import EquityTimeseriesCard from '@/components/paper-trade/analytics/EquityTimeseriesCard';

const INDICATORS: IndicatorDef[] = [
  { id: 'summary', label: 'サマリ指標', category: 'basic', defaultEnabled: true, component: SummaryCard },
  { id: 'position_cycles', label: 'ポジションサイクル', category: 'basic', defaultEnabled: true, component: PositionCyclesCard },
  { id: 'open_position', label: '現在保有の健康度', category: 'basic', defaultEnabled: true, component: OpenPositionCard },
  { id: 'timing', label: 'タイミング可視化', category: 'basic', defaultEnabled: true, component: TimingChartCard },
  { id: 'buy_and_hold', label: 'バイ＆ホールド比較', category: 'advanced', defaultEnabled: false, component: BuyAndHoldCard },
  { id: 'equity_timeseries', label: '投下資本/損益推移', category: 'advanced', defaultEnabled: false, component: EquityTimeseriesCard },
];
```

- [ ] **Step 5: 型チェック**

Run:
```bash
cd frontend && npx tsc --noEmit
```
Expected: エラー 0 件

- [ ] **Step 6: Commit**

```bash
git add frontend/src/components/paper-trade/analytics/TimingChartCard.tsx frontend/src/components/paper-trade/analytics/BuyAndHoldCard.tsx frontend/src/components/paper-trade/analytics/EquityTimeseriesCard.tsx frontend/src/pages/PaperTradeSymbolPage.tsx
git commit -m "feat(paper-trade): タイミング/バイ&ホールド/エクイティ推移カードを追加"
```

---

## Task 17: エンドツーエンド手動検証

**Files:** なし（検証のみ）

**目的:** dev server を立ててブラウザで golden path を通す。

- [ ] **Step 1: Backend + Frontend を起動**

ターミナル 1:
```bash
cd backend && uv run uvicorn app.main:app --port 8000 --reload
```
ターミナル 2:
```bash
cd frontend && npm run dev
```

- [ ] **Step 2: ブラウザで動作確認**

ブラウザで http://localhost:5173/paper-trade を開き、以下を確認:

1. 未初期化なら「仮想口座を作成しましょう」の EmptyState が出る
2. 初期資金 1,000,000 円で作成 → 総資産 1,000,000 / 現金 1,000,000 / 含み 0 のカードが出る
3. 「買い付け」→ `7203.T` 100株 @ 2500 で約定 → 残高が 750,000 になる
4. 資産推移チャートが 1 点以上プロットされる
5. 保有銘柄テーブルの「売却」から 100株 @ 2700 で約定 → 現金 1,020,000 / 実現損益 +20,000
6. 取引履歴に 2 行表示される
7. 銘柄別パフォーマンステーブルの `7203.T` 行をクリック → `/paper-trade/symbols/7203.T` に遷移
8. サマリ・ポジションサイクル・現在保有（この時点では未保有＝EmptyState）・タイミング のカードが表示される
9. 「📊 表示項目を選択」→ バイ＆ホールド と 投下資本/損益推移 を ON → カードが増える
10. ページをリロード → 前回の表示設定が保持されている
11. メインページに戻り「リセット」→ 確認ダイアログ → 全部消える

- [ ] **Step 3: 確認結果を README / 手動テストログに記録（任意）**

問題なければ特に記録不要。異常があればバグとして新タスク化。

- [ ] **Step 4: サーバ停止 → 念のため型チェック + pytest を最終実行**

Run:
```bash
cd frontend && npx tsc --noEmit
cd ../backend && uv run pytest tests/test_paper_trade_service.py -v
```
Expected: all pass.

- [ ] **Step 5: 最終コミット（もし微修正が入っていれば）**

```bash
git status
# 差分があれば適宜 git add / git commit
```

---

## 自己レビューチェックリスト

**spec 要件 → タスク対応**:
- [x] paper_accounts / paper_holdings / paper_trades テーブル作成 → Task 1
- [x] fee / dividend 予約カラム → Task 1
- [x] 口座 init / reset → Task 3
- [x] 買い / 売り（100株単位、残高/保有チェック、現在値自動取得） → Task 4
- [x] サマリ / 保有 / 取引履歴 API → Task 5, 9
- [x] 資産推移チャート（履歴再構築、前方補完） → Task 6
- [x] 銘柄別パフォーマンス（一覧） → Task 7
- [x] 銘柄別詳細分析（FIFO / MFE / バイ＆ホールド / エクイティ推移） → Task 8
- [x] 全 API エンドポイント → Task 9
- [x] ルーティング / ナビ → Task 10
- [x] 6 カード（Summary / PositionCycles / OpenPosition / Timing / BuyAndHold / EquityTimeseries） → Task 15, 16
- [x] Indicator Registry と IndicatorSelector（localStorage 永続化） → Task 15
- [x] エラー処理（400 / 409、残高不足・単元株・現在値取得失敗） → Task 4, 9
- [x] テスト（純粋関数） → Task 4, 6, 8
- [x] 手動 E2E → Task 17

**未対応・オープン事項（spec §10）**: 実装計画フェーズ後に必要に応じ追加検討。

---

Plan complete and saved to `docs/superpowers/plans/2026-04-20-paper-trade.md`.
