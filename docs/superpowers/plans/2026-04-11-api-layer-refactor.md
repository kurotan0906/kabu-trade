# API Layer Refactor Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** `scores.py` と `tradingview_signals.py` のAPIレイヤに直接書かれたDBクエリをServiceレイヤに移譲し、CLAUDE.mdにアーキテクチャ原則を追記する。

**Architecture:** `analysis_axes_service.py` と同じパターンに揃える。APIレイヤはHTTPの入出力に専念し、DBアクセスはServiceに委譲する。既存のAPIコントラクト（エンドポイント・レスポンス形式）は変更しない。

**Tech Stack:** Python, FastAPI, SQLAlchemy 2 (Async), pytest-asyncio

---

## ファイルマップ

| 操作 | パス |
|------|------|
| 新規作成 | `backend/app/services/score_service.py` |
| 新規作成 | `backend/app/services/tradingview_signal_service.py` |
| 修正 | `backend/app/api/v1/scores.py` |
| 修正 | `backend/app/api/v1/tradingview_signals.py` |
| 修正 | `CLAUDE.md` |
| 既存テスト（変更なし、通過確認のみ） | `backend/tests/test_scores_api.py` |
| 既存テスト（変更なし、通過確認のみ） | `backend/tests/test_tradingview_signals_api.py` |

---

### Task 1: score_service.py を作成し、scores.py を更新する

**Files:**
- Create: `backend/app/services/score_service.py`
- Modify: `backend/app/api/v1/scores.py`

- [ ] **Step 1: 既存テストが通ることを確認（ベースライン）**

```bash
cd backend && python -m pytest tests/test_scores_api.py -v
```

期待: 全テスト PASSED

- [ ] **Step 2: `score_service.py` を作成する**

`backend/app/services/score_service.py` を新規作成:

```python
"""スコアサービス"""

from typing import List, Optional

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, desc, func

from app.models.stock_score import StockScore


async def list_scores(
    db: AsyncSession,
    sort: str = "total_score",
    limit: int = 100,
) -> List[StockScore]:
    """全銘柄スコア一覧（最新スコアのみ、指定軸で降順ソート）"""
    allowed_sorts = {"total_score", "fundamental_score", "technical_score", "kurotenko_score"}
    if sort not in allowed_sorts:
        sort = "total_score"

    subq = (
        select(StockScore.symbol, func.max(StockScore.scored_at).label("latest"))
        .group_by(StockScore.symbol)
        .subquery()
    )
    sort_col = getattr(StockScore, sort)
    stmt = (
        select(StockScore)
        .join(subq, (StockScore.symbol == subq.c.symbol) & (StockScore.scored_at == subq.c.latest))
        .where(StockScore.data_quality != "fetch_error")
        .order_by(desc(sort_col))
        .limit(limit)
    )
    result = await db.execute(stmt)
    return list(result.scalars().all())


async def get_score(db: AsyncSession, symbol: str) -> Optional[StockScore]:
    """銘柄の最新スコアを返す。存在しない場合は None。"""
    stmt = (
        select(StockScore)
        .where(StockScore.symbol == symbol)
        .order_by(desc(StockScore.scored_at))
        .limit(1)
    )
    result = await db.execute(stmt)
    return result.scalar_one_or_none()
```

- [ ] **Step 3: `scores.py` を更新する**

`backend/app/api/v1/scores.py` を以下で置き換える:

```python
"""スコアAPI"""

from typing import List

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.schemas.stock_score import StockScoreResponse, AnalysisAxesResponse
from app.services import score_service
from app.services.analysis_axes_service import get_analysis_axes

router = APIRouter()


@router.get("", response_model=List[StockScoreResponse])
async def list_scores(
    sort: str = Query("total_score", description="ソートカラム"),
    limit: int = Query(100, ge=1, le=500),
    db: AsyncSession = Depends(get_db),
):
    """全銘柄スコア一覧（最新スコアのみ、指定軸で降順ソート）"""
    return await score_service.list_scores(db, sort=sort, limit=limit)


@router.get("/{symbol}", response_model=StockScoreResponse)
async def get_score(symbol: str, db: AsyncSession = Depends(get_db)):
    """銘柄の最新スコアを返す"""
    score = await score_service.get_score(db, symbol)
    if not score:
        raise HTTPException(status_code=404, detail=f"銘柄 {symbol} のスコアが見つかりません")
    return score


@router.get("/{symbol}/axes", response_model=AnalysisAxesResponse)
async def get_axes(symbol: str, db: AsyncSession = Depends(get_db)):
    """銘柄の全分析軸集約を返す"""
    return await get_analysis_axes(symbol, db)
```

- [ ] **Step 4: テストを再実行して通ることを確認**

```bash
cd backend && python -m pytest tests/test_scores_api.py -v
```

期待: 全テスト PASSED（APIコントラクトは変わっていないので既存テストがそのまま通る）

- [ ] **Step 5: コミット**

```bash
git add backend/app/services/score_service.py backend/app/api/v1/scores.py
git commit -m "refactor: scores APIのDBクエリをServiceレイヤに移譲"
```

---

### Task 2: tradingview_signal_service.py を作成し、tradingview_signals.py を更新する

**Files:**
- Create: `backend/app/services/tradingview_signal_service.py`
- Modify: `backend/app/api/v1/tradingview_signals.py`

- [ ] **Step 1: 既存テストが通ることを確認（ベースライン）**

```bash
cd backend && python -m pytest tests/test_tradingview_signals_api.py -v
```

期待: 全テスト PASSED

- [ ] **Step 2: `tradingview_signal_service.py` を作成する**

`backend/app/services/tradingview_signal_service.py` を新規作成:

```python
"""TradingView シグナルサービス"""

from typing import List, Optional

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, desc, func

from app.models.tradingview_signal import TradingViewSignal
from app.schemas.tradingview_signal import TradingViewSignalCreate


async def create_signal(
    db: AsyncSession,
    symbol: str,
    payload: TradingViewSignalCreate,
) -> TradingViewSignal:
    """TradingView 分析結果を保存して返す。"""
    data = payload.model_dump()
    data["symbol"] = symbol
    signal = TradingViewSignal(**data)
    db.add(signal)
    await db.commit()
    await db.refresh(signal)
    return signal


async def get_signal(db: AsyncSession, symbol: str) -> Optional[TradingViewSignal]:
    """銘柄の最新 TradingView シグナルを返す。存在しない場合は None。"""
    stmt = (
        select(TradingViewSignal)
        .where(TradingViewSignal.symbol == symbol)
        .order_by(desc(TradingViewSignal.updated_at))
        .limit(1)
    )
    result = await db.execute(stmt)
    return result.scalar_one_or_none()


async def list_signals(db: AsyncSession) -> List[TradingViewSignal]:
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
    return list(result.scalars().all())
```

- [ ] **Step 3: `tradingview_signals.py` を更新する**

`backend/app/api/v1/tradingview_signals.py` を以下で置き換える:

```python
"""TradingView シグナル API"""

from typing import List

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.schemas.tradingview_signal import TradingViewSignalCreate, TradingViewSignalResponse
from app.services import tradingview_signal_service

router = APIRouter()


@router.post("/{symbol}", response_model=TradingViewSignalResponse, status_code=201)
async def create_signal(
    symbol: str,
    payload: TradingViewSignalCreate,
    db: AsyncSession = Depends(get_db),
):
    """TradingView 分析結果を保存（Claude が MCP 呼び出し後に POST する）"""
    return await tradingview_signal_service.create_signal(db, symbol, payload)


@router.get("/{symbol}", response_model=TradingViewSignalResponse)
async def get_signal(symbol: str, db: AsyncSession = Depends(get_db)):
    """銘柄の最新 TradingView シグナルを返す"""
    signal = await tradingview_signal_service.get_signal(db, symbol)
    if not signal:
        raise HTTPException(status_code=404, detail=f"銘柄 {symbol} の TradingView シグナルが見つかりません")
    return signal


@router.get("", response_model=List[TradingViewSignalResponse])
async def list_signals(db: AsyncSession = Depends(get_db)):
    """全銘柄の最新 TradingView シグナル一覧（ランキングページ用）"""
    return await tradingview_signal_service.list_signals(db)
```

- [ ] **Step 4: テストを再実行して通ることを確認**

```bash
cd backend && python -m pytest tests/test_tradingview_signals_api.py -v
```

期待: 全テスト PASSED

- [ ] **Step 5: コミット**

```bash
git add backend/app/services/tradingview_signal_service.py backend/app/api/v1/tradingview_signals.py
git commit -m "refactor: tradingview_signals APIのDBクエリをServiceレイヤに移譲"
```

---

### Task 3: CLAUDE.md にアーキテクチャ原則を追記する

**Files:**
- Modify: `CLAUDE.md`

- [ ] **Step 1: CLAUDE.md に追記する**

`CLAUDE.md` の `## Development Rules` セクションの末尾に以下を追加:

```markdown
## アーキテクチャ原則

- **レイヤの責務を守る（シンプルでも例外なし）**:
  コードを書く前に「この変更が必要になったとき、どこだけ直せばいいか」を問う。
  DBの構造変化 → Repository/Service に閉じる、HTTP仕様の変化 → API層に閉じる。
  処理が単純に見えるほどレイヤを飛ばしやすいが、それが負債の起点になる。
```

- [ ] **Step 2: コミット**

```bash
git add CLAUDE.md
git commit -m "docs: CLAUDE.mdにアーキテクチャ原則を追記"
```

---

### Task 4: 全テスト通過確認

- [ ] **Step 1: バックエンド全テストを実行**

```bash
cd backend && python -m pytest -v
```

期待: 全テスト PASSED（新規失敗なし）

- [ ] **Step 2: 完了確認**

全テストが通っていれば作業完了。
