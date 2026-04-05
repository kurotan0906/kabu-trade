# TradingView MCP連携 実装プラン

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Claude Code から TradingView を MCP 経由で操作し、チャート分析結果を kabu-trade アプリに保存・表示できるようにする。

**Architecture:** Playwright ベースの tradingview-mcp をローカル MCP サーバーとして Claude Code に登録し、チャートスクリーンショットを Claude Vision で分析して FastAPI バックエンドに保存する。フロントエンドは既存の StockDetailPage に ChartAnalysisPanel を追加して分析結果を表示する。

**Tech Stack:** Python (tradingview-mcp, Playwright), FastAPI, SQLAlchemy, Alembic, PostgreSQL, React/TypeScript, Axios

---

## ファイル構成

### 新規作成
- `backend/app/models/chart_analysis.py` — ChartAnalysis SQLAlchemy モデル
- `backend/app/schemas/chart_analysis.py` — Pydantic スキーマ（リクエスト/レスポンス）
- `backend/app/api/v1/chart_analysis.py` — FastAPI ルーター（POST/GET エンドポイント）
- `backend/alembic/versions/002_add_chart_analyses.py` — DB マイグレーション
- `backend/tests/test_chart_analysis_api.py` — API テスト
- `frontend/src/types/chartAnalysis.ts` — TypeScript 型定義
- `frontend/src/services/api/chartAnalysisApi.ts` — Axios API クライアント
- `frontend/src/components/stock/ChartAnalysisPanel.tsx` — 分析結果表示コンポーネント

### 変更
- `.claude/settings.local.json` — MCP サーバー設定追加
- `backend/app/main.py` — chart_analysis ルーターを登録
- `frontend/src/components/stock/index.ts` — ChartAnalysisPanel をエクスポート
- `frontend/src/pages/StockDetailPage.tsx` — ChartAnalysisPanel を組み込む

---

## Task 1: MCPサーバーインストールと Claude Code 設定

**Files:**
- Modify: `.claude/settings.local.json`

- [ ] **Step 1: uv をインストールする（uvx コマンド用）**

```bash
curl -LsSf https://astral.sh/uv/install.sh | sh
```

インストール後、新しいシェルを開くか `source ~/.zshrc` を実行。

- [ ] **Step 2: tradingview-mcp が uvx で起動できるか確認する**

```bash
uvx tradingview-mcp --help
```

期待される出力: ヘルプテキストまたは起動メッセージ（エラーなし）

- [ ] **Step 3: .claude/settings.local.json に MCP サーバー設定を追加する**

現在のファイル内容に `mcpServers` キーを追加する。`"permissions"` と同じ階層に追記:

```json
{
  "permissions": {
    "allow": [
      "Bash(/Users/mfujii/.claude/plugins/cache/claude-plugins-official/superpowers/5.0.7/skills/brainstorming/scripts/start-server.sh:*)",
      "Bash(npm uninstall:*)",
      "Bash(npm install:*)",
      "Bash(npx tsc:*)",
      "Bash(npx eslint:*)",
      "Bash(ls /Users/mfujii/src/kabu-trade/frontend/.eslint*)",
      "Bash(ls /Users/mfujii/src/kabu-trade/.eslint*)",
      "Bash(python3 -c \"import sys,json; d=json.load\\(sys.stdin\\); print\\(d.get\\('version', 'unknown'\\)\\)\")",
      "Bash(node -e ':*)",
      "Bash(curl -sv http://localhost:8000/)",
      "Bash(docker compose up:*)",
      "Bash(curl -s http://localhost:8000/health)",
      "Bash(curl -s http://localhost:8000/)",
      "Bash(docker compose:*)",
      "WebSearch",
      "Bash(pip show:*)",
      "Bash(uvx tradingview-mcp:*)"
    ]
  },
  "mcpServers": {
    "tradingview": {
      "command": "uvx",
      "args": ["tradingview-mcp"],
      "env": {
        "TV_USERNAME": "YOUR_TRADINGVIEW_EMAIL",
        "TV_PASSWORD": "YOUR_TRADINGVIEW_PASSWORD"
      }
    }
  }
}
```

`YOUR_TRADINGVIEW_EMAIL` と `YOUR_TRADINGVIEW_PASSWORD` を実際の TradingView アカウント情報に置き換える。

- [ ] **Step 4: Claude Code を再起動して MCP サーバーを認識させる**

Claude Code を終了して再起動する（`/quit` → 再起動）。`/mcp` コマンドで `tradingview` が表示されることを確認。

- [ ] **Step 5: 動作確認（Claude Code の会話で実行）**

Claude Code に以下を話しかけて MCP ツールが動くか確認:

```
TradingViewで7203のチャートを開いて、日足に設定してスクリーンショットを撮ってください
```

MCP ツール `chart_set_symbol`, `chart_set_timeframe`, `chart_take_screenshot` が呼ばれることを確認。

- [ ] **Step 6: コミット**

```bash
git add .claude/settings.local.json
git commit -m "feat: Claude Code に TradingView MCP サーバーを設定"
```

---

## Task 2: ChartAnalysis モデルと DB マイグレーション

**Files:**
- Create: `backend/app/models/chart_analysis.py`
- Create: `backend/alembic/versions/002_add_chart_analyses.py`

- [ ] **Step 1: モデルファイルを作成する**

```python
# backend/app/models/chart_analysis.py
"""ChartAnalysis model"""

from sqlalchemy import Column, Integer, String, DateTime, Text, JSON
from sqlalchemy.sql import func
from app.core.database import Base


class ChartAnalysis(Base):
    """ChartAnalysis model - チャート分析結果"""

    __tablename__ = "chart_analyses"

    id = Column(Integer, primary_key=True, autoincrement=True, comment="ID")
    symbol = Column(
        String(10),
        nullable=False,
        index=True,
        comment="銘柄コード（例: 7203）",
    )
    timeframe = Column(String(10), nullable=False, comment="時間足（例: 1D, 1W）")
    screenshot_path = Column(
        String(500), nullable=True, comment="スクリーンショットパス"
    )
    trend = Column(
        String(20), nullable=False, comment="トレンド（bullish/bearish/neutral）"
    )
    signals = Column(JSON, nullable=True, comment="シグナル詳細（JSON）")
    summary = Column(Text, nullable=False, comment="Claudeが生成したサマリー")
    recommendation = Column(
        String(10), nullable=False, comment="推奨（buy/sell/hold）"
    )
    created_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
        comment="作成日時",
    )

    def __repr__(self):
        return (
            f"<ChartAnalysis(id={self.id}, symbol={self.symbol}, "
            f"timeframe={self.timeframe}, recommendation={self.recommendation})>"
        )
```

- [ ] **Step 2: Alembic マイグレーションファイルを作成する**

```python
# backend/alembic/versions/002_add_chart_analyses.py
"""add chart_analyses table

Revision ID: 002_add_chart_analyses
Revises: 001_initial
Create Date: 2026-04-05 00:00:00.000000

"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa

revision: str = '002_add_chart_analyses'
down_revision: Union[str, None] = '001_initial'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        'chart_analyses',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False, comment='ID'),
        sa.Column('symbol', sa.String(length=10), nullable=False, comment='銘柄コード'),
        sa.Column('timeframe', sa.String(length=10), nullable=False, comment='時間足'),
        sa.Column('screenshot_path', sa.String(length=500), nullable=True, comment='スクリーンショットパス'),
        sa.Column('trend', sa.String(length=20), nullable=False, comment='トレンド'),
        sa.Column('signals', sa.JSON(), nullable=True, comment='シグナル詳細'),
        sa.Column('summary', sa.Text(), nullable=False, comment='サマリー'),
        sa.Column('recommendation', sa.String(length=10), nullable=False, comment='推奨'),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False, comment='作成日時'),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index('ix_chart_analyses_symbol', 'chart_analyses', ['symbol'], unique=False)


def downgrade() -> None:
    op.drop_index('ix_chart_analyses_symbol', table_name='chart_analyses')
    op.drop_table('chart_analyses')
```

- [ ] **Step 3: DB が起動している状態でマイグレーションを実行する**

```bash
cd /Users/mfujii/src/kabu-trade/backend
docker compose up -d postgres
alembic upgrade head
```

期待される出力:
```
INFO  [alembic.runtime.migration] Running upgrade 001_initial -> 002_add_chart_analyses, add chart_analyses table
```

- [ ] **Step 4: テーブルが作成されたことを確認する**

```bash
docker compose exec postgres psql -U postgres -d kabu_trade -c "\d chart_analyses"
```

期待される出力: `chart_analyses` テーブルの列一覧が表示される。

- [ ] **Step 5: コミット**

```bash
git add backend/app/models/chart_analysis.py backend/alembic/versions/002_add_chart_analyses.py
git commit -m "feat: ChartAnalysis モデルと DB マイグレーションを追加"
```

---

## Task 3: Pydantic スキーマ

**Files:**
- Create: `backend/app/schemas/chart_analysis.py`
- Test: `backend/tests/test_chart_analysis_api.py`（スキーマ検証部分）

- [ ] **Step 1: スキーマファイルを作成する**

```python
# backend/app/schemas/chart_analysis.py
"""ChartAnalysis schemas"""

from datetime import datetime
from typing import Optional, Dict, Any
from pydantic import BaseModel, Field


class ChartAnalysisCreate(BaseModel):
    """チャート分析結果の作成リクエスト"""

    symbol: str = Field(..., description="銘柄コード（例: 7203）")
    timeframe: str = Field(..., description="時間足（例: 1D, 1W, 4H）")
    screenshot_path: Optional[str] = Field(None, description="スクリーンショットパス")
    trend: str = Field(..., description="トレンド（bullish/bearish/neutral）")
    signals: Optional[Dict[str, Any]] = Field(None, description="シグナル詳細")
    summary: str = Field(..., description="Claudeが生成したサマリー")
    recommendation: str = Field(..., description="推奨（buy/sell/hold）")


class ChartAnalysisResponse(BaseModel):
    """チャート分析結果のレスポンス"""

    id: int = Field(..., description="ID")
    symbol: str = Field(..., description="銘柄コード")
    timeframe: str = Field(..., description="時間足")
    screenshot_path: Optional[str] = Field(None, description="スクリーンショットパス")
    trend: str = Field(..., description="トレンド")
    signals: Optional[Dict[str, Any]] = Field(None, description="シグナル詳細")
    summary: str = Field(..., description="サマリー")
    recommendation: str = Field(..., description="推奨")
    created_at: datetime = Field(..., description="作成日時")

    class Config:
        from_attributes = True
```

- [ ] **Step 2: スキーマのユニットテストを書く**

```python
# backend/tests/test_chart_analysis_api.py
"""ChartAnalysis API tests"""

import pytest
from app.schemas.chart_analysis import ChartAnalysisCreate, ChartAnalysisResponse
from datetime import datetime


def test_chart_analysis_create_requires_symbol():
    with pytest.raises(Exception):
        ChartAnalysisCreate(
            timeframe="1D",
            trend="bullish",
            summary="テストサマリー",
            recommendation="buy",
        )


def test_chart_analysis_create_valid():
    data = ChartAnalysisCreate(
        symbol="7203",
        timeframe="1D",
        trend="bullish",
        signals={"rsi": "oversold_recovery", "ma": "golden_cross_approaching"},
        summary="日足チャートでは上昇トレンドが継続中",
        recommendation="buy",
    )
    assert data.symbol == "7203"
    assert data.timeframe == "1D"
    assert data.trend == "bullish"
    assert data.recommendation == "buy"
    assert data.signals["rsi"] == "oversold_recovery"
    assert data.screenshot_path is None


def test_chart_analysis_create_optional_fields():
    data = ChartAnalysisCreate(
        symbol="9984",
        timeframe="1W",
        trend="neutral",
        summary="週足チャートではもみ合い継続",
        recommendation="hold",
    )
    assert data.signals is None
    assert data.screenshot_path is None
```

- [ ] **Step 3: テストを実行して PASS することを確認する**

```bash
cd /Users/mfujii/src/kabu-trade/backend
pytest tests/test_chart_analysis_api.py::test_chart_analysis_create_valid \
       tests/test_chart_analysis_api.py::test_chart_analysis_create_optional_fields \
       tests/test_chart_analysis_api.py::test_chart_analysis_create_requires_symbol \
       -v
```

期待される出力: 3 tests PASSED

- [ ] **Step 4: コミット**

```bash
git add backend/app/schemas/chart_analysis.py backend/tests/test_chart_analysis_api.py
git commit -m "feat: ChartAnalysis Pydantic スキーマを追加"
```

---

## Task 4: FastAPI エンドポイント

**Files:**
- Create: `backend/app/api/v1/chart_analysis.py`
- Modify: `backend/app/main.py`（ルーター登録）
- Modify: `backend/tests/test_chart_analysis_api.py`（API テスト追加）

- [ ] **Step 1: API ルーターを作成する**

```python
# backend/app/api/v1/chart_analysis.py
"""ChartAnalysis API routes"""

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, desc
from typing import Optional
from app.core.database import get_db
from app.models.chart_analysis import ChartAnalysis
from app.schemas.chart_analysis import ChartAnalysisCreate, ChartAnalysisResponse

router = APIRouter()


@router.post("", response_model=ChartAnalysisResponse, status_code=201)
async def create_chart_analysis(
    data: ChartAnalysisCreate,
    db: AsyncSession = Depends(get_db),
):
    """
    チャート分析結果を保存

    - **symbol**: 銘柄コード（例: 7203）
    - **timeframe**: 時間足（例: 1D, 1W）
    - **trend**: トレンド（bullish/bearish/neutral）
    - **recommendation**: 推奨（buy/sell/hold）
    - **summary**: Claudeが生成したサマリー
    """
    analysis = ChartAnalysis(
        symbol=data.symbol,
        timeframe=data.timeframe,
        screenshot_path=data.screenshot_path,
        trend=data.trend,
        signals=data.signals,
        summary=data.summary,
        recommendation=data.recommendation,
    )
    db.add(analysis)
    await db.commit()
    await db.refresh(analysis)
    return analysis


@router.get("/{symbol}/latest", response_model=ChartAnalysisResponse)
async def get_latest_chart_analysis(
    symbol: str,
    timeframe: Optional[str] = Query(None, description="時間足でフィルタ"),
    db: AsyncSession = Depends(get_db),
):
    """
    銘柄の最新チャート分析を取得

    - **symbol**: 銘柄コード（例: 7203）
    - **timeframe**: 時間足でフィルタ（オプション）
    """
    stmt = select(ChartAnalysis).where(ChartAnalysis.symbol == symbol)
    if timeframe:
        stmt = stmt.where(ChartAnalysis.timeframe == timeframe)
    stmt = stmt.order_by(desc(ChartAnalysis.created_at)).limit(1)

    result = await db.execute(stmt)
    analysis = result.scalar_one_or_none()

    if not analysis:
        raise HTTPException(
            status_code=404,
            detail=f"銘柄 {symbol} のチャート分析が見つかりません",
        )
    return analysis


@router.get("/{symbol}/history", response_model=list[ChartAnalysisResponse])
async def list_chart_analyses(
    symbol: str,
    timeframe: Optional[str] = Query(None, description="時間足でフィルタ"),
    limit: int = Query(20, ge=1, le=100, description="取得件数"),
    db: AsyncSession = Depends(get_db),
):
    """
    銘柄のチャート分析履歴を取得

    - **symbol**: 銘柄コード（例: 7203）
    - **timeframe**: 時間足でフィルタ（オプション）
    - **limit**: 取得件数（最大100）
    """
    stmt = select(ChartAnalysis).where(ChartAnalysis.symbol == symbol)
    if timeframe:
        stmt = stmt.where(ChartAnalysis.timeframe == timeframe)
    stmt = stmt.order_by(desc(ChartAnalysis.created_at)).limit(limit)

    result = await db.execute(stmt)
    return result.scalars().all()
```

- [ ] **Step 2: main.py にルーターを登録する**

`backend/app/main.py` の末尾（`# 将来の拡張用` の前）に追記:

```python
# チャート分析機能
from app.api.v1 import chart_analysis
app.include_router(chart_analysis.router, prefix="/api/v1/chart-analysis", tags=["chart-analysis"])
```

- [ ] **Step 3: サーバーを起動してエンドポイントを確認する**

```bash
cd /Users/mfujii/src/kabu-trade/backend
docker compose up -d postgres
uvicorn app.main:app --reload
```

別ターミナルで:
```bash
curl -s http://localhost:8000/docs | grep -q "chart-analysis" && echo "OK" || echo "NG"
```

期待: `OK`

- [ ] **Step 4: API テストを追加する**

`backend/tests/test_chart_analysis_api.py` に以下を追記:

```python
import pytest
from httpx import AsyncClient, ASGITransport
from app.main import app


@pytest.mark.asyncio
async def test_create_chart_analysis():
    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as client:
        response = await client.post(
            "/api/v1/chart-analysis",
            json={
                "symbol": "7203",
                "timeframe": "1D",
                "trend": "bullish",
                "signals": {"rsi": "oversold_recovery"},
                "summary": "日足チャートでは上昇トレンドが継続中",
                "recommendation": "buy",
            },
        )
    assert response.status_code == 201
    data = response.json()
    assert data["symbol"] == "7203"
    assert data["recommendation"] == "buy"
    assert "id" in data
    assert "created_at" in data


@pytest.mark.asyncio
async def test_get_latest_not_found():
    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as client:
        response = await client.get("/api/v1/chart-analysis/9999/latest")
    assert response.status_code == 404
```

- [ ] **Step 5: スキーマテストを再実行して全テストが通ることを確認する**

```bash
cd /Users/mfujii/src/kabu-trade/backend
pytest tests/test_chart_analysis_api.py -v
```

期待: 5 tests PASSED（スキーマ 3 + API 2）

> 注意: `test_create_chart_analysis` と `test_get_latest_not_found` は DB 接続が必要なため、DB が起動していない環境ではスキップされるか失敗する。スキーマテスト 3 件だけ通れば OK。

- [ ] **Step 6: コミット**

```bash
git add backend/app/api/v1/chart_analysis.py backend/app/main.py backend/tests/test_chart_analysis_api.py
git commit -m "feat: ChartAnalysis API エンドポイントを追加"
```

---

## Task 5: フロントエンド — 型定義と API クライアント

**Files:**
- Create: `frontend/src/types/chartAnalysis.ts`
- Create: `frontend/src/services/api/chartAnalysisApi.ts`

- [ ] **Step 1: TypeScript 型定義ファイルを作成する**

```typescript
// frontend/src/types/chartAnalysis.ts

export interface ChartSignals {
  rsi?: string;
  ma?: string;
  macd?: string;
  bollinger?: string;
  [key: string]: string | undefined;
}

export interface ChartAnalysis {
  id: number;
  symbol: string;
  timeframe: string;
  screenshot_path: string | null;
  trend: 'bullish' | 'bearish' | 'neutral';
  signals: ChartSignals | null;
  summary: string;
  recommendation: 'buy' | 'sell' | 'hold';
  created_at: string;
}

export interface ChartAnalysisCreate {
  symbol: string;
  timeframe: string;
  screenshot_path?: string;
  trend: 'bullish' | 'bearish' | 'neutral';
  signals?: ChartSignals;
  summary: string;
  recommendation: 'buy' | 'sell' | 'hold';
}
```

- [ ] **Step 2: API クライアントファイルを作成する**

```typescript
// frontend/src/services/api/chartAnalysisApi.ts

import axios from 'axios';
import type { ChartAnalysis, ChartAnalysisCreate } from '@/types/chartAnalysis';

const API_BASE_URL = '/api/v1';

const apiClient = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
});

export const chartAnalysisApi = {
  async saveAnalysis(data: ChartAnalysisCreate): Promise<ChartAnalysis> {
    const response = await apiClient.post<ChartAnalysis>('/chart-analysis', data);
    return response.data;
  },

  async getLatest(symbol: string, timeframe?: string): Promise<ChartAnalysis> {
    const params = timeframe ? { timeframe } : undefined;
    const response = await apiClient.get<ChartAnalysis>(
      `/chart-analysis/${symbol}/latest`,
      { params }
    );
    return response.data;
  },

  async getHistory(
    symbol: string,
    timeframe?: string,
    limit: number = 20
  ): Promise<ChartAnalysis[]> {
    const params: Record<string, string | number> = { limit };
    if (timeframe) params.timeframe = timeframe;
    const response = await apiClient.get<ChartAnalysis[]>(
      `/chart-analysis/${symbol}/history`,
      { params }
    );
    return response.data;
  },
};
```

- [ ] **Step 3: TypeScript のコンパイルエラーがないことを確認する**

```bash
cd /Users/mfujii/src/kabu-trade/frontend
npx tsc --noEmit
```

期待: エラーなし（警告のみ許容）

- [ ] **Step 4: コミット**

```bash
git add frontend/src/types/chartAnalysis.ts frontend/src/services/api/chartAnalysisApi.ts
git commit -m "feat: ChartAnalysis の TypeScript 型定義と API クライアントを追加"
```

---

## Task 6: ChartAnalysisPanel コンポーネント

**Files:**
- Create: `frontend/src/components/stock/ChartAnalysisPanel.tsx`
- Modify: `frontend/src/components/stock/index.ts`

- [ ] **Step 1: ChartAnalysisPanel コンポーネントを作成する**

```typescript
// frontend/src/components/stock/ChartAnalysisPanel.tsx

import type { ChartAnalysis } from '@/types/chartAnalysis';

interface ChartAnalysisPanelProps {
  analysis: ChartAnalysis;
}

const trendLabel: Record<string, string> = {
  bullish: '強気 (Bullish)',
  bearish: '弱気 (Bearish)',
  neutral: '中立 (Neutral)',
};

const trendColor: Record<string, string> = {
  bullish: '#4caf50',
  bearish: '#f44336',
  neutral: '#ff9800',
};

const recommendationLabel: Record<string, string> = {
  buy: '買い (Buy)',
  sell: '売り (Sell)',
  hold: '様子見 (Hold)',
};

const recommendationColor: Record<string, string> = {
  buy: '#4caf50',
  sell: '#f44336',
  hold: '#ff9800',
};

const ChartAnalysisPanel = ({ analysis }: ChartAnalysisPanelProps) => {
  const formattedDate = new Date(analysis.created_at).toLocaleString('ja-JP');

  return (
    <div
      style={{
        border: '1px solid #e0e0e0',
        borderRadius: '8px',
        padding: '1.5rem',
        marginTop: '1rem',
      }}
    >
      <div
        style={{
          display: 'flex',
          justifyContent: 'space-between',
          alignItems: 'center',
          marginBottom: '1rem',
        }}
      >
        <h3 style={{ margin: 0 }}>AI チャート分析</h3>
        <span style={{ fontSize: '0.85rem', color: '#757575' }}>
          最終更新: {formattedDate}
        </span>
      </div>

      <div
        style={{
          display: 'grid',
          gridTemplateColumns: 'repeat(2, 1fr)',
          gap: '1rem',
          marginBottom: '1rem',
        }}
      >
        <div
          style={{
            padding: '1rem',
            backgroundColor: '#f5f5f5',
            borderRadius: '4px',
          }}
        >
          <div style={{ fontSize: '0.85rem', color: '#757575' }}>トレンド</div>
          <div
            style={{
              fontWeight: 'bold',
              color: trendColor[analysis.trend] ?? '#757575',
            }}
          >
            {trendLabel[analysis.trend] ?? analysis.trend}
          </div>
        </div>
        <div
          style={{
            padding: '1rem',
            backgroundColor: '#f5f5f5',
            borderRadius: '4px',
          }}
        >
          <div style={{ fontSize: '0.85rem', color: '#757575' }}>推奨</div>
          <div
            style={{
              fontWeight: 'bold',
              color: recommendationColor[analysis.recommendation] ?? '#757575',
            }}
          >
            {recommendationLabel[analysis.recommendation] ?? analysis.recommendation}
          </div>
        </div>
      </div>

      {analysis.signals && Object.keys(analysis.signals).length > 0 && (
        <div style={{ marginBottom: '1rem' }}>
          <h4 style={{ marginTop: 0, marginBottom: '0.5rem' }}>シグナル</h4>
          <ul style={{ margin: 0, paddingLeft: '1.5rem' }}>
            {Object.entries(analysis.signals).map(([key, value]) =>
              value ? (
                <li key={key} style={{ marginBottom: '0.25rem' }}>
                  <strong>{key.toUpperCase()}:</strong> {value}
                </li>
              ) : null
            )}
          </ul>
        </div>
      )}

      <div>
        <h4 style={{ marginTop: 0, marginBottom: '0.5rem' }}>サマリー</h4>
        <p style={{ margin: 0, lineHeight: 1.6, color: '#333' }}>
          {analysis.summary}
        </p>
      </div>
    </div>
  );
};

export default ChartAnalysisPanel;
```

- [ ] **Step 2: index.ts に ChartAnalysisPanel をエクスポート追加する**

`frontend/src/components/stock/index.ts` の末尾に追記:

```typescript
export { default as ChartAnalysisPanel } from './ChartAnalysisPanel';
```

- [ ] **Step 3: TypeScript エラーがないことを確認する**

```bash
cd /Users/mfujii/src/kabu-trade/frontend
npx tsc --noEmit
```

期待: エラーなし

- [ ] **Step 4: コミット**

```bash
git add frontend/src/components/stock/ChartAnalysisPanel.tsx frontend/src/components/stock/index.ts
git commit -m "feat: ChartAnalysisPanel コンポーネントを追加"
```

---

## Task 7: StockDetailPage への統合

**Files:**
- Modify: `frontend/src/pages/StockDetailPage.tsx`

- [ ] **Step 1: StockDetailPage.tsx に ChartAnalysisPanel を統合する**

`frontend/src/pages/StockDetailPage.tsx` を以下のように修正する:

インポートを追加（既存 import 群の末尾に）:

```typescript
import ChartAnalysisPanel from '@/components/stock/ChartAnalysisPanel';
import { chartAnalysisApi } from '@/services/api/chartAnalysisApi';
import type { ChartAnalysis } from '@/types/chartAnalysis';
```

state を追加（既存の `evaluation` state の下に）:

```typescript
const [chartAnalysis, setChartAnalysis] = useState<ChartAnalysis | null>(null);
const [chartAnalysisLoading, setChartAnalysisLoading] = useState(false);
const [chartAnalysisError, setChartAnalysisError] = useState<string | null>(null);
```

既存の `useEffect` 内（`fetchPrices` の後）に追記:

```typescript
  // 最新のチャート分析があれば取得
  chartAnalysisApi.getLatest(code).then(setChartAnalysis).catch(() => {
    // 未分析の場合はエラーを無視
  });
```

`handleEvaluate` の後に `handleChartAnalysis` 関数を追加:

```typescript
  const handleChartAnalysis = async () => {
    if (!code) return;
    setChartAnalysisLoading(true);
    setChartAnalysisError(null);
    try {
      const result = await chartAnalysisApi.getLatest(code);
      setChartAnalysis(result);
    } catch {
      setChartAnalysisError(
        '分析結果が見つかりません。Claude Code でチャート分析を実行してください。'
      );
    } finally {
      setChartAnalysisLoading(false);
    }
  };
```

評価ボタンの隣に「チャート分析を更新」ボタンを追加（`{evaluationError && ...}` の前）:

```tsx
        <button
          onClick={handleChartAnalysis}
          disabled={chartAnalysisLoading}
          style={{
            padding: '0.75rem 1.5rem',
            fontSize: '1rem',
            backgroundColor: '#6200ea',
            color: 'white',
            border: 'none',
            borderRadius: '4px',
            cursor: chartAnalysisLoading ? 'not-allowed' : 'pointer',
            opacity: chartAnalysisLoading ? 0.6 : 1,
            marginLeft: '1rem',
          }}
        >
          {chartAnalysisLoading ? '取得中...' : 'チャート分析を更新'}
        </button>
```

`{evaluation && <EvaluationResult ... />}` の後に ChartAnalysisPanel を追加:

```tsx
        {chartAnalysisError && (
          <ErrorMessage
            message={chartAnalysisError}
            onClose={() => setChartAnalysisError(null)}
          />
        )}
        {chartAnalysis && <ChartAnalysisPanel analysis={chartAnalysis} />}
```

- [ ] **Step 2: TypeScript エラーがないことを確認する**

```bash
cd /Users/mfujii/src/kabu-trade/frontend
npx tsc --noEmit
```

期待: エラーなし

- [ ] **Step 3: ESLint を実行する**

```bash
cd /Users/mfujii/src/kabu-trade/frontend
npx eslint src/pages/StockDetailPage.tsx src/components/stock/ChartAnalysisPanel.tsx --max-warnings 0
```

期待: エラーなし（警告 0）

- [ ] **Step 4: 開発サーバーで動作確認する**

```bash
cd /Users/mfujii/src/kabu-trade/frontend
npm run dev
```

ブラウザで `http://localhost:5173/stocks/7203` を開き、「チャート分析を更新」ボタンが表示されることを確認する。

- [ ] **Step 5: コミット**

```bash
git add frontend/src/pages/StockDetailPage.tsx
git commit -m "feat: StockDetailPage に ChartAnalysisPanel を統合"
```

---

## Task 8: E2E フロー確認

**Files:** 変更なし（動作確認のみ）

- [ ] **Step 1: バックエンドと DB を起動する**

```bash
cd /Users/mfujii/src/kabu-trade
docker compose up -d postgres redis
cd backend && uvicorn app.main:app --reload &
cd ../frontend && npm run dev &
```

- [ ] **Step 2: Claude Code に以下を話しかけてフルフローを確認する**

```
7203（トヨタ）の日足チャートをTradingViewで分析して、
結果を http://localhost:8000/api/v1/chart-analysis に POST してください。

POSTするJSONの形式:
{
  "symbol": "7203",
  "timeframe": "1D",
  "trend": "bullish または bearish または neutral",
  "signals": {"rsi": "...", "ma": "..."},
  "summary": "チャートの分析サマリー",
  "recommendation": "buy または sell または hold"
}
```

- [ ] **Step 3: フロントエンドで結果が表示されることを確認する**

ブラウザで `http://localhost:5173/stocks/7203` を開き、「チャート分析を更新」ボタンをクリック。ChartAnalysisPanel にトレンド・推奨・シグナル・サマリーが表示されることを確認。

- [ ] **Step 4: 最終コミット**

```bash
git add -p  # 未コミットのファイルがあれば
git commit -m "feat: TradingView MCP連携 Phase 1 完了"
```

---

## 付録: 分析プロンプトのテンプレート

Claude Code に話しかける際のプロンプト例（コピー用）:

```
{symbol}（{company_name}）の{timeframe}チャートをTradingViewで分析してください。

手順:
1. TradingViewで銘柄を{symbol}に設定
2. 時間足を{timeframe}に設定
3. チャートタイプをローソク足（Candles）に設定
4. スクリーンショットを取得して分析
5. 以下のエンドポイントに結果を保存:
   POST http://localhost:8000/api/v1/chart-analysis

分析ではトレンド方向、RSI、移動平均線のクロス、出来高の変化に注目してください。
```
