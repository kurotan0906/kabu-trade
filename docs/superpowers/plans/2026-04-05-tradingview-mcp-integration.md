# TradingView MCP 統合 Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** TradingView MCPで取得したリアルタイムテクニカル分析を DB に保存し、銘柄詳細の多軸分析パネル（5軸目）とスコアランキングの TVシグナル列に表示する。

**Architecture:** Claude が TradingView MCP（`get_technical_analysis`）を呼び出し、結果を `POST /api/v1/tradingview-signals/{symbol}` で保存する（ChartAnalysis と同パターン）。フロントエンドは既存の `AnalysisAxesPanel` が `/scores/{symbol}/axes` を経由して自動的に TradingView 軸を受け取る。

**Tech Stack:** FastAPI, SQLAlchemy (asyncpg), Alembic, PostgreSQL (JSONB), React, TypeScript, axios

---

## ファイル構成

```
backend/
  app/models/tradingview_signal.py          # NEW: SQLAlchemy モデル
  app/schemas/tradingview_signal.py         # NEW: Pydantic スキーマ
  app/api/v1/tradingview_signals.py         # NEW: POST/GET エンドポイント
  app/services/analysis_axes_service.py    # MODIFY: TradingView 軸を追加
  app/main.py                               # MODIFY: ルーター登録
  alembic/versions/004_add_tradingview_signals.py  # NEW: マイグレーション
  tests/test_tradingview_signals_api.py    # NEW: API テスト

frontend/
  src/types/tradingviewSignal.ts            # NEW: 型定義
  src/services/api/tradingviewApi.ts        # NEW: API クライアント
  src/components/stock/AnalysisAxesPanel.tsx  # MODIFY: TradingView 色追加
  src/pages/StockDetailPage.tsx             # MODIFY: TV更新ボタン
  src/pages/StockRankingPage.tsx            # MODIFY: TVシグナル列 + バッチボタン
```

**symbol フォーマット:** `tradingview_signals.symbol` は `.T` なしの4桁コード（例: `"7203"`）。URL ルーティングと `AnalysisAxesPanel` が `code`（`.T` なし）を使うため統一する。

---

### Task 1: DB モデル + マイグレーション

**Files:**
- Create: `backend/app/models/tradingview_signal.py`
- Create: `backend/alembic/versions/004_add_tradingview_signals.py`

- [ ] **Step 1: モデルファイルを作成**

```python
# backend/app/models/tradingview_signal.py
"""TradingViewSignal model - TradingView MCP テクニカル分析結果"""

from sqlalchemy import Column, Integer, Float, String, DateTime, JSON
from sqlalchemy.sql import func
from app.core.database import Base


class TradingViewSignal(Base):
    """TradingView MCP で取得したテクニカル分析結果"""

    __tablename__ = "tradingview_signals"

    id = Column(Integer, primary_key=True, autoincrement=True)
    symbol = Column(String(20), nullable=False, index=True, comment="銘柄コード（例: 7203、.T なし）")
    recommendation = Column(String(20), nullable=True, comment="STRONG_BUY/BUY/NEUTRAL/SELL/STRONG_SELL")
    score = Column(Float, nullable=True, comment="0-100 変換スコア")
    buy_count = Column(Integer, nullable=True, comment="買いシグナル数")
    sell_count = Column(Integer, nullable=True, comment="売りシグナル数")
    neutral_count = Column(Integer, nullable=True, comment="中立シグナル数")
    ma_recommendation = Column(String(20), nullable=True, comment="移動平均サマリー")
    osc_recommendation = Column(String(20), nullable=True, comment="オシレーターサマリー")
    details = Column(JSON, nullable=True, comment="全指標の生データ")
    updated_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now())

    def __repr__(self):
        return f"<TradingViewSignal(symbol={self.symbol}, recommendation={self.recommendation})>"
```

- [ ] **Step 2: マイグレーションファイルを作成**

```python
# backend/alembic/versions/004_add_tradingview_signals.py
"""add tradingview_signals table

Revision ID: 004_add_tradingview_signals
Revises: 003_add_stock_scores
Create Date: 2026-04-05 00:00:00.000000
"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa

revision: str = '004_add_tradingview_signals'
down_revision: Union[str, None] = '003_add_stock_scores'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        'tradingview_signals',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('symbol', sa.String(length=20), nullable=False, comment='銘柄コード'),
        sa.Column('recommendation', sa.String(length=20), nullable=True),
        sa.Column('score', sa.Float(), nullable=True),
        sa.Column('buy_count', sa.Integer(), nullable=True),
        sa.Column('sell_count', sa.Integer(), nullable=True),
        sa.Column('neutral_count', sa.Integer(), nullable=True),
        sa.Column('ma_recommendation', sa.String(length=20), nullable=True),
        sa.Column('osc_recommendation', sa.String(length=20), nullable=True),
        sa.Column('details', sa.JSON(), nullable=True),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index(op.f('ix_tradingview_signals_symbol'), 'tradingview_signals', ['symbol'], unique=False)


def downgrade() -> None:
    op.drop_index(op.f('ix_tradingview_signals_symbol'), table_name='tradingview_signals')
    op.drop_table('tradingview_signals')
```

- [ ] **Step 3: マイグレーションを適用**

```bash
cd backend
python3 -m alembic upgrade head
```

Expected output:
```
INFO  [alembic.runtime.migration] Running upgrade 003_add_stock_scores -> 004_add_tradingview_signals, add tradingview_signals table
```

- [ ] **Step 4: コミット**

```bash
git add backend/app/models/tradingview_signal.py backend/alembic/versions/004_add_tradingview_signals.py
git commit -m "feat: TradingViewSignal モデルとマイグレーションを追加"
```

---

### Task 2: Pydantic スキーマ + API エンドポイント + テスト

**Files:**
- Create: `backend/app/schemas/tradingview_signal.py`
- Create: `backend/app/api/v1/tradingview_signals.py`
- Modify: `backend/app/main.py`
- Create: `backend/tests/test_tradingview_signals_api.py`

- [ ] **Step 1: テストファイルを先に作成（TDD）**

```python
# backend/tests/test_tradingview_signals_api.py
"""TradingView シグナル API のテスト"""
import pytest
from httpx import AsyncClient, ASGITransport
from app.main import app


@pytest.mark.asyncio
async def test_list_signals_empty():
    """シグナルなし時は空リストを返す"""
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        response = await client.get("/api/v1/tradingview-signals")
    assert response.status_code == 200
    assert isinstance(response.json(), list)


@pytest.mark.asyncio
async def test_get_signal_not_found():
    """存在しない銘柄は 404"""
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        response = await client.get("/api/v1/tradingview-signals/9999")
    assert response.status_code == 404


@pytest.mark.asyncio
async def test_create_and_get_signal():
    """POST で保存した後 GET で取得できる"""
    payload = {
        "recommendation": "BUY",
        "score": 75.0,
        "buy_count": 12,
        "sell_count": 4,
        "neutral_count": 6,
        "ma_recommendation": "BUY",
        "osc_recommendation": "NEUTRAL",
        "details": {"RSI": 58.5},
    }
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        post_res = await client.post("/api/v1/tradingview-signals/7203", json=payload)
        assert post_res.status_code == 201
        created = post_res.json()
        assert created["symbol"] == "7203"
        assert created["recommendation"] == "BUY"

        get_res = await client.get("/api/v1/tradingview-signals/7203")
        assert get_res.status_code == 200
        fetched = get_res.json()
        assert fetched["symbol"] == "7203"
        assert fetched["score"] == 75.0


@pytest.mark.asyncio
async def test_list_signals_returns_latest_per_symbol():
    """同一銘柄を2回 POST → GET一覧は最新1件のみ"""
    payload_old = {"recommendation": "SELL", "score": 25.0}
    payload_new = {"recommendation": "STRONG_BUY", "score": 100.0}
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        await client.post("/api/v1/tradingview-signals/1234", json=payload_old)
        await client.post("/api/v1/tradingview-signals/1234", json=payload_new)
        list_res = await client.get("/api/v1/tradingview-signals")
    signals = list_res.json()
    matching = [s for s in signals if s["symbol"] == "1234"]
    assert len(matching) == 1
    assert matching[0]["recommendation"] == "STRONG_BUY"
```

- [ ] **Step 2: テストが失敗することを確認**

```bash
cd backend
python3 -m pytest tests/test_tradingview_signals_api.py -v 2>&1 | head -20
```

Expected: FAIL（ルーターが未登録のため404等）

- [ ] **Step 3: スキーマファイルを作成**

```python
# backend/app/schemas/tradingview_signal.py
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
```

- [ ] **Step 4: API エンドポイントを作成**

```python
# backend/app/api/v1/tradingview_signals.py
"""TradingView シグナル API"""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, desc, func

from app.core.database import get_db
from app.models.tradingview_signal import TradingViewSignal
from app.schemas.tradingview_signal import TradingViewSignalCreate, TradingViewSignalResponse

router = APIRouter()


@router.post("/{symbol}", response_model=TradingViewSignalResponse, status_code=201)
async def create_signal(
    symbol: str,
    payload: TradingViewSignalCreate,
    db: AsyncSession = Depends(get_db),
):
    """TradingView 分析結果を保存（Claude が MCP 呼び出し後に POST する）"""
    data = payload.model_dump()
    data["symbol"] = symbol
    signal = TradingViewSignal(**data)
    db.add(signal)
    await db.commit()
    await db.refresh(signal)
    return signal


@router.get("/{symbol}", response_model=TradingViewSignalResponse)
async def get_signal(symbol: str, db: AsyncSession = Depends(get_db)):
    """銘柄の最新 TradingView シグナルを返す"""
    stmt = (
        select(TradingViewSignal)
        .where(TradingViewSignal.symbol == symbol)
        .order_by(desc(TradingViewSignal.updated_at))
        .limit(1)
    )
    result = await db.execute(stmt)
    signal = result.scalar_one_or_none()
    if not signal:
        raise HTTPException(status_code=404, detail=f"銘柄 {symbol} の TradingView シグナルが見つかりません")
    return signal


@router.get("", response_model=list)
async def list_signals(db: AsyncSession = Depends(get_db)):
    """全銘柄の最新 TradingView シグナル一覧（ランキングページ用）"""
    subq = (
        select(TradingViewSignal.symbol, func.max(TradingViewSignal.updated_at).label("latest"))
        .group_by(TradingViewSignal.symbol)
        .subquery()
    )
    stmt = (
        select(TradingViewSignal)
        .join(
            subq,
            (TradingViewSignal.symbol == subq.c.symbol)
            & (TradingViewSignal.updated_at == subq.c.latest),
        )
        .order_by(desc(TradingViewSignal.updated_at))
    )
    result = await db.execute(stmt)
    return result.scalars().all()
```

- [ ] **Step 5: main.py にルーターを登録**

`backend/app/main.py` の末尾（`# 将来の拡張用` の直前）に追加:

```python
# TradingView シグナル API
from app.api.v1 import tradingview_signals
app.include_router(tradingview_signals.router, prefix="/api/v1/tradingview-signals", tags=["tradingview-signals"])
```

- [ ] **Step 6: テストが通ることを確認**

```bash
cd backend
python3 -m pytest tests/test_tradingview_signals_api.py -v
```

Expected:
```
PASSED tests/test_tradingview_signals_api.py::test_list_signals_empty
PASSED tests/test_tradingview_signals_api.py::test_get_signal_not_found
PASSED tests/test_tradingview_signals_api.py::test_create_and_get_signal
PASSED tests/test_tradingview_signals_api.py::test_list_signals_returns_latest_per_symbol
```

- [ ] **Step 7: コミット**

```bash
git add backend/app/schemas/tradingview_signal.py \
        backend/app/api/v1/tradingview_signals.py \
        backend/app/main.py \
        backend/tests/test_tradingview_signals_api.py
git commit -m "feat: TradingView シグナル API を追加（POST/GET/list）"
```

---

### Task 3: analysis_axes_service に TradingView 軸を追加

**Files:**
- Modify: `backend/app/services/analysis_axes_service.py`

- [ ] **Step 1: テストを追加（既存の `test_tradingview_signals_api.py` に追記）**

`backend/tests/test_tradingview_signals_api.py` の末尾に追加:

```python
@pytest.mark.asyncio
async def test_axes_includes_tradingview_after_post():
    """TradingView シグナルを POST した後、/scores/{symbol}/axes に TradingView 軸が含まれる"""
    payload = {
        "recommendation": "BUY",
        "score": 75.0,
        "buy_count": 10,
        "sell_count": 3,
        "neutral_count": 5,
    }
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        await client.post("/api/v1/tradingview-signals/5555", json=payload)
        axes_res = await client.get("/api/v1/scores/5555/axes")
    assert axes_res.status_code == 200
    axes = axes_res.json()["axes"]
    tv_axes = [a for a in axes if a["name"] == "TradingView"]
    assert len(tv_axes) == 1
    assert tv_axes[0]["score"] == 75.0
    assert tv_axes[0]["recommendation"] == "BUY"
```

- [ ] **Step 2: テストが失敗することを確認**

```bash
cd backend
python3 -m pytest tests/test_tradingview_signals_api.py::test_axes_includes_tradingview_after_post -v
```

Expected: FAIL（TradingView 軸が返らない）

- [ ] **Step 3: analysis_axes_service.py を更新**

`backend/app/services/analysis_axes_service.py` を以下の内容に置き換え:

```python
"""多軸分析集約サービス

stock_scores（最新1件）、chart_analyses（最新1件）、tradingview_signals（最新1件）を
symbol で結合して返す。
"""

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, desc

from app.models.stock_score import StockScore
from app.models.chart_analysis import ChartAnalysis
from app.models.tradingview_signal import TradingViewSignal
from app.schemas.stock_score import AnalysisAxesResponse, AnalysisAxis


async def get_analysis_axes(symbol: str, db: AsyncSession) -> AnalysisAxesResponse:
    """symbol の全分析軸を集約して返す。"""

    score_stmt = (
        select(StockScore)
        .where(StockScore.symbol == symbol)
        .order_by(desc(StockScore.scored_at))
        .limit(1)
    )
    score_result = await db.execute(score_stmt)
    stock_score = score_result.scalar_one_or_none()

    chart_stmt = (
        select(ChartAnalysis)
        .where(ChartAnalysis.symbol == symbol)
        .order_by(desc(ChartAnalysis.created_at))
        .limit(1)
    )
    chart_result = await db.execute(chart_stmt)
    chart_analysis = chart_result.scalar_one_or_none()

    tv_stmt = (
        select(TradingViewSignal)
        .where(TradingViewSignal.symbol == symbol)
        .order_by(desc(TradingViewSignal.updated_at))
        .limit(1)
    )
    tv_result = await db.execute(tv_stmt)
    tv_signal = tv_result.scalar_one_or_none()

    axes = []

    if stock_score:
        axes.append(AnalysisAxis(
            name="ファンダメンタル",
            score=stock_score.fundamental_score,
            detail={
                "per": stock_score.per,
                "pbr": stock_score.pbr,
                "roe": stock_score.roe,
                "dividend_yield": stock_score.dividend_yield,
                "revenue_growth": stock_score.revenue_growth,
            },
        ))
        axes.append(AnalysisAxis(
            name="テクニカル",
            score=stock_score.technical_score,
            detail={
                "ma_score": stock_score.ma_score,
                "rsi_score": stock_score.rsi_score,
                "macd_score": stock_score.macd_score,
            },
        ))
        criteria = stock_score.kurotenko_criteria or {}
        criteria_met = sum(1 for v in criteria.values() if v is True)
        axes.append(AnalysisAxis(
            name="黒点子",
            score=stock_score.kurotenko_score,
            detail={
                "criteria_met": criteria_met,
                "criteria_total": 8,
                **criteria,
            },
        ))

    if chart_analysis:
        axes.append(AnalysisAxis(
            name="チャート分析",
            score=None,
            recommendation=chart_analysis.recommendation,
            detail={
                "trend": chart_analysis.trend,
                "summary": chart_analysis.summary,
                "signals": chart_analysis.signals,
                "analyzed_at": chart_analysis.created_at.isoformat(),
            },
        ))

    if tv_signal:
        axes.append(AnalysisAxis(
            name="TradingView",
            score=tv_signal.score,
            recommendation=tv_signal.recommendation,
            detail={
                "buy_count": tv_signal.buy_count,
                "sell_count": tv_signal.sell_count,
                "neutral_count": tv_signal.neutral_count,
                "ma_recommendation": tv_signal.ma_recommendation,
                "osc_recommendation": tv_signal.osc_recommendation,
                "updated_at": tv_signal.updated_at.isoformat(),
            },
        ))

    return AnalysisAxesResponse(symbol=symbol, axes=axes)
```

- [ ] **Step 4: テストが通ることを確認**

```bash
cd backend
python3 -m pytest tests/test_tradingview_signals_api.py -v
```

Expected: 5件すべて PASSED

- [ ] **Step 5: コミット**

```bash
git add backend/app/services/analysis_axes_service.py \
        backend/tests/test_tradingview_signals_api.py
git commit -m "feat: analysis_axes_service に TradingView 軸を追加"
```

---

### Task 4: フロントエンド型定義 + API クライアント

**Files:**
- Create: `frontend/src/types/tradingviewSignal.ts`
- Create: `frontend/src/services/api/tradingviewApi.ts`

- [ ] **Step 1: 型定義ファイルを作成**

```typescript
// frontend/src/types/tradingviewSignal.ts
export interface TradingViewSignal {
  id: number;
  symbol: string;
  recommendation: string | null;
  score: number | null;
  buy_count: number | null;
  sell_count: number | null;
  neutral_count: number | null;
  ma_recommendation: string | null;
  osc_recommendation: string | null;
  details: Record<string, unknown> | null;
  updated_at: string;
}

export interface TradingViewSignalCreate {
  recommendation?: string | null;
  score?: number | null;
  buy_count?: number | null;
  sell_count?: number | null;
  neutral_count?: number | null;
  ma_recommendation?: string | null;
  osc_recommendation?: string | null;
  details?: Record<string, unknown> | null;
}
```

- [ ] **Step 2: API クライアントを作成**

```typescript
// frontend/src/services/api/tradingviewApi.ts
import axios from 'axios';
import type { TradingViewSignal, TradingViewSignalCreate } from '@/types/tradingviewSignal';

const apiClient = axios.create({
  baseURL: '/api/v1',
  headers: { 'Content-Type': 'application/json' },
});

export const tradingviewApi = {
  async getSignal(symbol: string): Promise<TradingViewSignal> {
    const response = await apiClient.get<TradingViewSignal>(`/tradingview-signals/${symbol}`);
    return response.data;
  },

  async listSignals(): Promise<TradingViewSignal[]> {
    const response = await apiClient.get<TradingViewSignal[]>('/tradingview-signals');
    return response.data;
  },

  async createSignal(symbol: string, data: TradingViewSignalCreate): Promise<TradingViewSignal> {
    const response = await apiClient.post<TradingViewSignal>(`/tradingview-signals/${symbol}`, data);
    return response.data;
  },
};
```

- [ ] **Step 3: TypeScript 型チェックを実行**

```bash
cd frontend
npx tsc --noEmit 2>&1 | head -30
```

Expected: エラーなし（または既存エラーのみ）

- [ ] **Step 4: コミット**

```bash
git add frontend/src/types/tradingviewSignal.ts \
        frontend/src/services/api/tradingviewApi.ts
git commit -m "feat: TradingView シグナルの型定義と API クライアントを追加"
```

---

### Task 5: AnalysisAxesPanel に TradingView 色を追加 + StockDetailPage に TV 更新ボタンを追加

**Files:**
- Modify: `frontend/src/components/stock/AnalysisAxesPanel.tsx`
- Modify: `frontend/src/pages/StockDetailPage.tsx`

- [ ] **Step 1: AnalysisAxesPanel.tsx の AXIS_COLORS に TradingView を追加**

`frontend/src/components/stock/AnalysisAxesPanel.tsx` の `AXIS_COLORS` を以下に変更:

```typescript
const AXIS_COLORS: Record<string, string> = {
  'ファンダメンタル': '#3b82f6',
  'テクニカル': '#10b981',
  '黒点子': '#8b5cf6',
  'チャート分析': '#f59e0b',
  'TradingView': '#f97316',
};
```

- [ ] **Step 2: StockDetailPage.tsx に axesRefreshKey state と TV 更新ボタンを追加**

`frontend/src/pages/StockDetailPage.tsx` を以下の手順で修正する。

まず `useState` のインポート部分はすでに `useState` を使用しているので変更不要。

`const [chartAnalysisError, setChartAnalysisError] = useState<string | null>(null);` の直後に追加:

```typescript
const [axesRefreshKey, setAxesRefreshKey] = useState(0);
```

`「チャート分析を更新」ボタン` の直後（`marginLeft: '1rem'` のボタンの後）に以下を追加:

```typescript
<button
  onClick={() => setAxesRefreshKey((k) => k + 1)}
  style={{
    padding: '0.75rem 1.5rem',
    fontSize: '1rem',
    backgroundColor: '#ea580c',
    color: 'white',
    border: 'none',
    borderRadius: '4px',
    cursor: 'pointer',
    marginLeft: '1rem',
  }}
>
  TradingView 更新
</button>
```

`{code && <AnalysisAxesPanel symbol={code} />}` を以下に変更:

```typescript
{code && <AnalysisAxesPanel key={axesRefreshKey} symbol={code} />}
```

- [ ] **Step 3: TypeScript 型チェックを実行**

```bash
cd frontend
npx tsc --noEmit 2>&1 | head -30
```

Expected: エラーなし

- [ ] **Step 4: コミット**

```bash
git add frontend/src/components/stock/AnalysisAxesPanel.tsx \
        frontend/src/pages/StockDetailPage.tsx
git commit -m "feat: AnalysisAxesPanel に TradingView 色追加・StockDetailPage に TV 更新ボタンを追加"
```

---

### Task 6: StockRankingPage に TVシグナル列とバッチ分析ボタンを追加

**Files:**
- Modify: `frontend/src/pages/StockRankingPage.tsx`

- [ ] **Step 1: TradingView 関連のインポートと state を追加**

`frontend/src/pages/StockRankingPage.tsx` の先頭インポートに追加:

```typescript
import { tradingviewApi } from '@/services/api/tradingviewApi';
import type { TradingViewSignal } from '@/types/tradingviewSignal';
```

`const [triggering, setTriggering] = useState(false);` の直後に追加:

```typescript
const [tvSignals, setTvSignals] = useState<Record<string, TradingViewSignal>>({});
```

- [ ] **Step 2: TV シグナル定数と useEffect 更新**

`RATING_COLORS` 定数の直後に追加:

```typescript
const TV_COLORS: Record<string, string> = {
  'STRONG_BUY': '#10b981',
  'BUY': '#3b82f6',
  'NEUTRAL': '#9ca3af',
  'SELL': '#f59e0b',
  'STRONG_SELL': '#ef4444',
};
```

`useEffect` 内の `Promise.all` を以下に変更:

```typescript
useEffect(() => {
  Promise.all([
    scoresApi.listScores('total_score', 100),
    scoresApi.getBatchStatus(),
    tradingviewApi.listSignals(),
  ]).then(([s, b, tv]) => {
    setScores(s);
    setBatchStatus(b);
    const map: Record<string, TradingViewSignal> = {};
    tv.forEach((sig) => { map[sig.symbol] = sig; });
    setTvSignals(map);
  }).finally(() => setLoading(false));
}, []);
```

- [ ] **Step 3: バッチ分析ボタンを追加**

「▶ スコアリング実行」ボタンを含む `<button>` の直後に追加:

```typescript
<button
  onClick={() =>
    alert(
      'Claude Code で「スコア上位100銘柄をTradingView一括分析して /api/v1/tradingview-signals に保存して」と依頼してください'
    )
  }
  style={{
    padding: '8px 16px',
    background: '#ea580c',
    color: 'white',
    border: 'none',
    borderRadius: 8,
    fontWeight: 600,
    cursor: 'pointer',
    fontSize: 13,
    marginLeft: 8,
  }}
>
  📡 TVバッチ分析
</button>
```

- [ ] **Step 4: テーブルヘッダーに TVシグナル列を追加**

`<th>黒点子</th>` の直後に追加:

```typescript
<th style={{ padding: '8px 12px', textAlign: 'left', color: '#fb923c', fontWeight: 600 }}>TVシグナル</th>
```

- [ ] **Step 5: テーブル行に TVシグナル列を追加**

`黒田子` の `<td>` の直後に追加:

```typescript
<td style={{ padding: '10px 12px' }}>
  {tvSignals[s.symbol.replace('.T', '')] ? (
    <span
      style={{
        padding: '2px 8px',
        borderRadius: 12,
        fontSize: 11,
        fontWeight: 600,
        background: `${TV_COLORS[tvSignals[s.symbol.replace('.T', '')].recommendation ?? ''] ?? '#6b7280'}22`,
        color: TV_COLORS[tvSignals[s.symbol.replace('.T', '')].recommendation ?? ''] ?? '#6b7280',
      }}
    >
      {(tvSignals[s.symbol.replace('.T', '')].recommendation ?? '—').replace('_', ' ')}
    </span>
  ) : (
    <span style={{ color: '#4b5563', fontSize: 12 }}>—</span>
  )}
</td>
```

- [ ] **Step 6: TypeScript 型チェックを実行**

```bash
cd frontend
npx tsc --noEmit 2>&1 | head -30
```

Expected: エラーなし

- [ ] **Step 7: コミット**

```bash
git add frontend/src/pages/StockRankingPage.tsx
git commit -m "feat: StockRankingPage に TVシグナル列とバッチ分析ボタンを追加"
```

---

## Claude ワークフロー（実装後の使い方）

### 個別銘柄のTradingView分析

1. TradingView MCP で分析を実行:
   ```
   get_technical_analysis("7203.T")  ← .T 付きで呼ぶ
   ```

2. 結果を kabu-trade API に保存（symbol は .T なし）:
   ```
   POST /api/v1/tradingview-signals/7203
   {
     "recommendation": "BUY",
     "score": 75.0,
     "buy_count": 12,
     "sell_count": 4,
     "neutral_count": 6,
     "ma_recommendation": "BUY",
     "osc_recommendation": "NEUTRAL",
     "details": { ...全指標データ... }
   }
   ```

3. フロントエンドの銘柄詳細ページで「TradingView 更新」ボタンを押すと 5 軸目に表示される。

### 上位銘柄の一括分析

1. スコアランキングを取得: `GET /api/v1/scores?limit=50`
2. 各銘柄の symbol（`.T` なし → `.T` 付きに変換して MCP 呼び出し）に対して `get_technical_analysis` を実行
3. 各結果を `POST /api/v1/tradingview-signals/{symbol}` で保存（symbol は `.T` なし）

---

## スコア変換ルール

TradingView MCP の `recommendation` を `score`（0–100）に変換する際の基準:

| recommendation | score |
|---|---|
| STRONG_BUY | 100 |
| BUY | 75 |
| NEUTRAL | 50 |
| SELL | 25 |
| STRONG_SELL | 0 |
