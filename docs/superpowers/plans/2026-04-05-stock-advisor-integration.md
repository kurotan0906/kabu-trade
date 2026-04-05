# stock-advisor × kabu-trade 統合 Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** stock-advisor のスコアリング機能を kabu-trade に統合し、全銘柄バッチスコアリング・多軸分析表示・ランキング一覧を実現する。

**Architecture:** kabu-trade（FastAPI + PostgreSQL + React）をベースに、stock-advisor の analyzer/ モジュールをそのまま移植。yfinance によるバッチ取得は APScheduler で毎日 18:00 JST に自動実行。スコアは `stock_scores` テーブルに保存し、`/api/v1/scores` で提供する。フロントエンドは `AnalysisAxesPanel`（4軸カード）と `StockRankingPage`（スコアランキング一覧）を追加する。

**Tech Stack:** FastAPI, SQLAlchemy (async), Alembic, PostgreSQL (JSONB), Redis, yfinance, ta, APScheduler, React, TypeScript, Axios

---

## ファイルマップ

### 新規作成（バックエンド）
- `backend/app/models/stock_score.py` — StockScore SQLAlchemy モデル
- `backend/alembic/versions/003_add_stock_scores.py` — DB マイグレーション
- `backend/app/analyzer/__init__.py` — パッケージ init
- `backend/app/analyzer/technical.py` — MA/RSI/MACD スコア（stock-advisor から移植）
- `backend/app/analyzer/fundamental.py` — PER/PBR/ROE スコア（stock-advisor から移植）
- `backend/app/analyzer/kurotenko_screener.py` — 黒点子スクリーナー（stock-advisor から移植、DB依存除去）
- `backend/app/analyzer/scorer.py` — 総合スコア・レーティング計算（stock-advisor から移植）
- `backend/app/external/yfinance_client.py` — yfinance 同期ラッパー
- `backend/app/services/scoring_service.py` — バッチスコアリング制御 + JPX銘柄マスター取得
- `backend/app/services/analysis_axes_service.py` — 多軸分析集約
- `backend/app/schemas/stock_score.py` — Pydantic スキーマ
- `backend/app/api/v1/scores.py` — GET /scores API
- `backend/app/api/v1/batch.py` — POST/GET /batch/scoring API
- `backend/tests/test_scoring.py` — スコアリングロジックのテスト
- `backend/tests/test_scores_api.py` — scores API のテスト

### 変更（バックエンド）
- `backend/requirements.txt` — yfinance, ta, apscheduler, curl-cffi, openpyxl, requests 追加
- `backend/app/main.py` — APScheduler 起動 + 新ルーター登録

### 新規作成（フロントエンド）
- `frontend/src/types/stockScore.ts` — TypeScript 型定義
- `frontend/src/services/api/scoresApi.ts` — scores/batch API クライアント
- `frontend/src/components/stock/AnalysisAxesPanel.tsx` — 多軸スコア表示コンポーネント
- `frontend/src/pages/StockRankingPage.tsx` — スコアランキング一覧ページ

### 変更（フロントエンド）
- `frontend/src/components/stock/index.ts` — AnalysisAxesPanel エクスポート追加
- `frontend/src/pages/StockDetailPage.tsx` — AnalysisAxesPanel 組み込み
- `frontend/src/App.tsx` — /ranking ルート追加

---

## Task 1: Python 依存追加 + DB モデル + マイグレーション

**Files:**
- Modify: `backend/requirements.txt`
- Create: `backend/app/models/stock_score.py`
- Create: `backend/alembic/versions/003_add_stock_scores.py`

- [ ] **Step 1: requirements.txt に依存を追加**

`backend/requirements.txt` の末尾に追加：

```
# Stock scoring (stock-advisor integration)
yfinance>=0.2.40
ta>=0.10.2
apscheduler>=3.10.4
curl-cffi>=0.6.0
openpyxl>=3.1.0
requests>=2.31.0
```

- [ ] **Step 2: 依存をインストールしてエラーがないか確認**

```bash
cd backend
pip install -r requirements.txt
```

期待: エラーなく完了。`import yfinance; import ta; import apscheduler` が成功する。

- [ ] **Step 3: StockScore モデルを作成**

`backend/app/models/stock_score.py` を新規作成：

```python
"""StockScore model - バッチスコアリング結果"""

from sqlalchemy import Column, Integer, Float, String, DateTime, JSON
from sqlalchemy.sql import func
from app.core.database import Base


class StockScore(Base):
    """StockScore model - 全銘柄バッチスコアリング結果"""

    __tablename__ = "stock_scores"

    id = Column(Integer, primary_key=True, autoincrement=True)
    symbol = Column(String(10), nullable=False, index=True, comment="銘柄コード（例: 7203.T）")
    name = Column(String(100), nullable=True, comment="銘柄名")
    sector = Column(String(100), nullable=True, comment="セクター")
    scored_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now(), comment="スコア算出日時")
    # 総合
    total_score = Column(Float, nullable=True, comment="総合スコア（0-100）")
    rating = Column(String(20), nullable=True, comment="レーティング（強い買い/買い/中立/売り/強い売り）")
    # 軸別スコア
    fundamental_score = Column(Float, nullable=True, comment="ファンダメンタルスコア（0-50）")
    technical_score = Column(Float, nullable=True, comment="テクニカルスコア（0-50）")
    kurotenko_score = Column(Float, nullable=True, comment="黒点子スコア（0-100）")
    kurotenko_criteria = Column(JSON, nullable=True, comment="黒点子条件合否")
    # 内訳
    per = Column(Float, nullable=True)
    pbr = Column(Float, nullable=True)
    roe = Column(Float, nullable=True)
    dividend_yield = Column(Float, nullable=True)
    revenue_growth = Column(Float, nullable=True)
    ma_score = Column(Float, nullable=True)
    rsi_score = Column(Float, nullable=True)
    macd_score = Column(Float, nullable=True)
    data_quality = Column(String(20), nullable=False, default="ok", comment="ok/fetch_error/partial")

    def __repr__(self):
        return f"<StockScore(symbol={self.symbol}, total_score={self.total_score}, rating={self.rating})>"
```

- [ ] **Step 4: Alembic マイグレーションを作成**

`backend/alembic/versions/003_add_stock_scores.py` を新規作成：

```python
"""add stock_scores table

Revision ID: 003_add_stock_scores
Revises: 002_add_chart_analyses
Create Date: 2026-04-05 00:00:00.000000
"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa

revision: str = '003_add_stock_scores'
down_revision: Union[str, None] = '002_add_chart_analyses'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        'stock_scores',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('symbol', sa.String(length=10), nullable=False, comment='銘柄コード'),
        sa.Column('name', sa.String(length=100), nullable=True, comment='銘柄名'),
        sa.Column('sector', sa.String(length=100), nullable=True, comment='セクター'),
        sa.Column('scored_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('total_score', sa.Float(), nullable=True),
        sa.Column('rating', sa.String(length=20), nullable=True),
        sa.Column('fundamental_score', sa.Float(), nullable=True),
        sa.Column('technical_score', sa.Float(), nullable=True),
        sa.Column('kurotenko_score', sa.Float(), nullable=True),
        sa.Column('kurotenko_criteria', sa.JSON(), nullable=True),
        sa.Column('per', sa.Float(), nullable=True),
        sa.Column('pbr', sa.Float(), nullable=True),
        sa.Column('roe', sa.Float(), nullable=True),
        sa.Column('dividend_yield', sa.Float(), nullable=True),
        sa.Column('revenue_growth', sa.Float(), nullable=True),
        sa.Column('ma_score', sa.Float(), nullable=True),
        sa.Column('rsi_score', sa.Float(), nullable=True),
        sa.Column('macd_score', sa.Float(), nullable=True),
        sa.Column('data_quality', sa.String(length=20), nullable=False, server_default='ok'),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index(op.f('ix_stock_scores_symbol'), 'stock_scores', ['symbol'], unique=False)


def downgrade() -> None:
    op.drop_index(op.f('ix_stock_scores_symbol'), table_name='stock_scores')
    op.drop_table('stock_scores')
```

- [ ] **Step 5: マイグレーションを実行**

```bash
cd backend
alembic upgrade head
```

期待: `Running upgrade 002_add_chart_analyses -> 003_add_stock_scores` が表示されてエラーなく完了。

- [ ] **Step 6: Commit**

```bash
git add backend/requirements.txt backend/app/models/stock_score.py backend/alembic/versions/003_add_stock_scores.py
git commit -m "feat: stock_scores モデルとマイグレーションを追加"
```

---

## Task 2: analyzer/ モジュールを stock-advisor から移植

**Files:**
- Create: `backend/app/analyzer/__init__.py`
- Create: `backend/app/analyzer/technical.py`
- Create: `backend/app/analyzer/fundamental.py`
- Create: `backend/app/analyzer/kurotenko_screener.py`
- Create: `backend/app/analyzer/scorer.py`
- Create: `backend/tests/test_scoring.py`

- [ ] **Step 1: パッケージ init を作成**

`backend/app/analyzer/__init__.py`：

```python
"""Analyzer package - stock-advisor から移植したスコアリングモジュール"""
```

- [ ] **Step 2: technical.py を移植**

`backend/app/analyzer/technical.py`：

```python
"""テクニカルスコア計算 - stock-advisor/analyzer/technical.py から移植"""

import pandas as pd
import ta


def score_ma(history: pd.DataFrame) -> int:
    if len(history) < 75:
        return 6
    close = history["Close"]
    ma25 = close.rolling(25).mean().iloc[-1]
    ma75 = close.rolling(75).mean().iloc[-1]
    price = close.iloc[-1]
    if price > ma25 and ma25 > ma75:
        return 20
    if price > ma25:
        return 12
    if price < ma25 and ma25 < ma75:
        return 0
    return 6


def score_rsi(rsi_value) -> int:
    if rsi_value is None:
        return 8
    if rsi_value <= 30:
        return 15
    if rsi_value <= 39:
        return 10
    if rsi_value <= 60:
        return 8
    if rsi_value <= 69:
        return 4
    return 0


def score_macd(recent_cross: bool, macd_above: bool) -> int:
    if recent_cross and macd_above:
        return 15
    if not recent_cross and macd_above:
        return 8
    if recent_cross and not macd_above:
        return 0
    return 3


def _calc_macd_state(history: pd.DataFrame):
    if len(history) < 35:
        return False, False
    close = history["Close"]
    macd_line = ta.trend.MACD(close, window_slow=26, window_fast=12, window_sign=9).macd()
    signal_line = ta.trend.MACD(close, window_slow=26, window_fast=12, window_sign=9).macd_signal()
    if macd_line is None or macd_line.empty:
        return False, False
    macd_above = macd_line.iloc[-1] > signal_line.iloc[-1]
    recent_cross = False
    for i in range(1, 4):
        if i >= len(macd_line):
            break
        if (macd_line.iloc[-i] > signal_line.iloc[-i] and
                macd_line.iloc[-(i + 1)] <= signal_line.iloc[-(i + 1)]):
            recent_cross = True
            break
    return recent_cross, macd_above


def calc_technical_score(history: pd.DataFrame) -> dict:
    """テクニカルスコアを計算して返す。

    Returns:
        dict: technical_score (0-50), ma_score, rsi_score, macd_score
    """
    ma_s = score_ma(history)

    rsi_val = None
    if len(history) >= 14:
        rsi_series = ta.momentum.RSIIndicator(history["Close"], window=14).rsi()
        if rsi_series is not None and not rsi_series.empty:
            val = rsi_series.iloc[-1]
            if not pd.isna(val):
                rsi_val = val
    rsi_s = score_rsi(rsi_val)

    recent_cross, macd_above = _calc_macd_state(history)
    macd_s = score_macd(recent_cross, macd_above)

    return {
        "technical_score": float(ma_s + rsi_s + macd_s),
        "ma_score": float(ma_s),
        "rsi_score": float(rsi_s),
        "macd_score": float(macd_s),
    }
```

- [ ] **Step 3: fundamental.py を移植**

`backend/app/analyzer/fundamental.py`：

```python
"""ファンダメンタルスコア計算 - stock-advisor/analyzer/fundamental.py から移植"""


def score_per(value) -> int:
    if value is None:
        return 5
    if value <= 0:
        return 0
    if value <= 10:
        return 10
    if value <= 15:
        return 7
    if value <= 25:
        return 4
    return 0


def score_pbr(value) -> int:
    if value is None or value <= 0:
        return 5
    if value <= 0.8:
        return 10
    if value <= 1.0:
        return 7
    if value <= 1.5:
        return 4
    return 0


def score_roe(value) -> int:
    if value is None:
        return 5
    if value >= 0.20:
        return 10
    if value >= 0.15:
        return 7
    if value >= 0.10:
        return 4
    return 0


def score_dividend(value) -> int:
    if value is None:
        return 5
    if value >= 0.04:
        return 10
    if value >= 0.03:
        return 7
    if value >= 0.02:
        return 4
    return 0


def score_revenue_growth(value) -> int:
    if value is None:
        return 5
    if value >= 0.20:
        return 10
    if value >= 0.10:
        return 7
    if value >= 0.0:
        return 4
    return 0


def _to_float(value):
    if value is None:
        return None
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def calc_fundamental_score(info: dict) -> dict:
    """yfinance の ticker.info dict からファンダメンタルスコアを計算して返す。

    Returns:
        dict: fundamental_score (0-50), per, pbr, roe, dividend_yield, revenue_growth, data_quality
    """
    per = _to_float(info.get("trailingPE"))
    pbr = _to_float(info.get("priceToBook"))
    roe = _to_float(info.get("returnOnEquity"))
    div = _to_float(info.get("dividendYield"))
    rev = _to_float(info.get("revenueGrowth"))

    total = float(score_per(per) + score_pbr(pbr) + score_roe(roe) + score_dividend(div) + score_revenue_growth(rev))

    has_any = any(v is not None for v in [per, pbr, roe, div, rev])
    data_quality = "ok" if has_any else "partial"

    return {
        "fundamental_score": total,
        "per": per,
        "pbr": pbr,
        "roe": roe,
        "dividend_yield": div,
        "revenue_growth": rev,
        "data_quality": data_quality,
    }
```

- [ ] **Step 4: kurotenko_screener.py を移植（DB依存を除去）**

`backend/app/analyzer/kurotenko_screener.py`：

```python
"""黒点子スクリーナー - stock-advisor/analyzer/kurotenko_screener.py から移植
DB依存（StockMaster lookup）を除去し、純粋な yfinance ベースの評価のみ残す。
"""

import pandas as pd


def _is_valid(v):
    if v is None:
        return False
    try:
        return not pd.isna(v)
    except (TypeError, ValueError):
        return True


_OP_INCOME_KEYS = ["Operating Income", "EBIT", "Net Income"]
_REVENUE_KEYS = ["Total Revenue", "Revenue"]


def _find_row(df, keys):
    if df is None:
        return None
    for k in keys:
        if k in df.index:
            return df.loc[k]
    return None


try:
    from curl_cffi import requests as _cffi_requests
    _YF_SESSION = _cffi_requests.Session(impersonate="chrome")
except Exception:
    _YF_SESSION = None


def evaluate_candidate(symbol: str, interval_sec: float = 0) -> dict | None:
    """symbol に対して黒点子の8条件を評価して返す。

    Returns:
        dict with keys: year_end_turnaround, consec_quarters_profit, sales_yoy,
                        equity_ratio, cf_positive, cash_over_debt, avg_volume,
                        market_cap, rating (int 0-8)
        None if yfinance raises an exception.
    """
    import yfinance as yf
    import time
    if interval_sec:
        time.sleep(interval_sec)
    try:
        ticker = yf.Ticker(symbol, session=_YF_SESSION)
        info = ticker.info or {}
        fin = ticker.financials
        qfin = ticker.quarterly_income_stmt
        if qfin is None or (hasattr(qfin, 'empty') and qfin.empty):
            qfin = ticker.quarterly_financials
        bs = ticker.balance_sheet
        cf = ticker.cashflow

        # 1. Year-end turnaround (前期赤字→今期黒字)
        year_end_turnaround = None
        if fin is not None and "Operating Income" in fin.index and fin.shape[1] >= 2:
            prev = fin.loc["Operating Income"].iloc[1]
            curr = fin.loc["Operating Income"].iloc[0]
            if _is_valid(prev) and _is_valid(curr):
                year_end_turnaround = bool(prev < 0 and curr > 0)

        # 2. Consecutive quarterly profit (2四半期連続黒字)
        consec_quarters_profit = None
        op_row = _find_row(qfin, _OP_INCOME_KEYS)
        if op_row is not None and len(op_row) >= 2:
            q0 = op_row.iloc[0]
            q1 = op_row.iloc[1]
            if _is_valid(q0) and _is_valid(q1):
                consec_quarters_profit = bool(q0 > 0 and q1 > 0)

        # 3. Sales YoY growth
        sales_yoy = None
        rev_row = _find_row(fin, _REVENUE_KEYS)
        if rev_row is not None and len(rev_row) >= 2:
            r_prev = rev_row.iloc[1]
            r_curr = rev_row.iloc[0]
            if _is_valid(r_prev) and _is_valid(r_curr) and r_prev > 0:
                sales_yoy = bool(r_curr > r_prev)

        # 4. Equity ratio >= 30%
        equity_ratio = None
        if bs is not None and "Total Stockholder Equity" in bs.index and "Total Assets" in bs.index:
            eq = bs.loc["Total Stockholder Equity"].iloc[0]
            ta_val = bs.loc["Total Assets"].iloc[0]
            if _is_valid(eq) and _is_valid(ta_val) and ta_val > 0:
                equity_ratio = bool((eq / ta_val) >= 0.30)

        # 5. Operating cash flow positive
        cf_positive = None
        if cf is not None and "Operating Cash Flow" in cf.index and cf.shape[1] >= 1:
            val = cf.loc["Operating Cash Flow"].iloc[0]
            if _is_valid(val):
                cf_positive = bool(val > 0)

        # 6. Cash > total debt
        cash_over_debt = None
        if bs is not None:
            cash_keys = ["Cash And Cash Equivalents", "Cash"]
            debt_keys = ["Total Debt", "Long Term Debt"]
            cash_row = _find_row(bs, cash_keys)
            debt_row = _find_row(bs, debt_keys)
            if cash_row is not None and debt_row is not None:
                cash_val = cash_row.iloc[0]
                debt_val = debt_row.iloc[0]
                if _is_valid(cash_val) and _is_valid(debt_val):
                    cash_over_debt = bool(cash_val > debt_val)

        # 7. Average volume >= 100,000
        avg_volume = None
        avg_vol = info.get("averageVolume")
        if avg_vol is not None:
            avg_volume = bool(avg_vol >= 100_000)

        # 8. Market cap >= 10B JPY (approx)
        market_cap = None
        mc = info.get("marketCap")
        if mc is not None:
            market_cap = bool(mc >= 10_000_000_000)

        bool_criteria = [
            year_end_turnaround, consec_quarters_profit, sales_yoy,
            equity_ratio, cf_positive, cash_over_debt, avg_volume, market_cap,
        ]
        rating = sum(1 for v in bool_criteria if v is True)

        return {
            "year_end_turnaround": year_end_turnaround,
            "consec_quarters_profit": consec_quarters_profit,
            "sales_yoy": sales_yoy,
            "equity_ratio": equity_ratio,
            "cf_positive": cf_positive,
            "cash_over_debt": cash_over_debt,
            "avg_volume": avg_volume,
            "market_cap": market_cap,
            "rating": rating,
        }
    except Exception:
        import logging
        logging.getLogger(__name__).exception("%s: evaluate_candidate 失敗", symbol)
        return None
```

- [ ] **Step 5: scorer.py を移植**

`backend/app/analyzer/scorer.py`：

```python
"""総合スコア・レーティング計算 - stock-advisor/analyzer/scorer.py から移植"""


def get_rating(score: float) -> str:
    if score >= 80:
        return "強い買い"
    if score >= 60:
        return "買い"
    if score >= 40:
        return "中立"
    if score >= 20:
        return "売り"
    return "強い売り"


def build_stock_result(
    symbol: str,
    name: str | None,
    sector: str | None,
    fundamental: dict,
    technical: dict,
    kurotenko: dict | None = None,
) -> dict:
    """各スコアを統合して stock_scores レコード用の dict を返す。

    Args:
        symbol: 銘柄コード（例: "7203.T"）
        name: 銘柄名
        sector: セクター
        fundamental: calc_fundamental_score() の返り値
        technical: calc_technical_score() の返り値
        kurotenko: evaluate_candidate() の返り値（None なら kurotenko_score=None）

    Returns:
        stock_scores テーブルに INSERT できる dict
    """
    total = fundamental["fundamental_score"] + technical["technical_score"]

    kurotenko_score = None
    kurotenko_criteria = None
    if kurotenko is not None:
        criteria_met = kurotenko["rating"]  # 0-8
        kurotenko_score = (criteria_met / 8) * 100
        kurotenko_criteria = {
            k: v for k, v in kurotenko.items() if k != "rating"
        }

    return {
        "symbol": symbol,
        "name": name,
        "sector": sector,
        "total_score": total,
        "rating": get_rating(total),
        "fundamental_score": fundamental["fundamental_score"],
        "technical_score": technical["technical_score"],
        "kurotenko_score": kurotenko_score,
        "kurotenko_criteria": kurotenko_criteria,
        "per": fundamental.get("per"),
        "pbr": fundamental.get("pbr"),
        "roe": fundamental.get("roe"),
        "dividend_yield": fundamental.get("dividend_yield"),
        "revenue_growth": fundamental.get("revenue_growth"),
        "ma_score": technical.get("ma_score"),
        "rsi_score": technical.get("rsi_score"),
        "macd_score": technical.get("macd_score"),
        "data_quality": fundamental.get("data_quality", "ok"),
    }
```

- [ ] **Step 6: テストを書く**

`backend/tests/test_scoring.py`：

```python
"""スコアリングロジックのユニットテスト"""
import pytest
import pandas as pd
import numpy as np

from app.analyzer.fundamental import calc_fundamental_score, score_per, score_pbr, score_roe
from app.analyzer.scorer import get_rating, build_stock_result


class TestFundamentalScore:
    def test_score_per_low(self):
        assert score_per(8.0) == 10

    def test_score_per_high(self):
        assert score_per(30.0) == 0

    def test_score_per_none(self):
        assert score_per(None) == 5

    def test_score_pbr_under_1(self):
        assert score_pbr(0.9) == 7

    def test_score_roe_high(self):
        assert score_roe(0.25) == 10

    def test_calc_fundamental_score_full(self):
        info = {
            "trailingPE": 8.0,
            "priceToBook": 0.9,
            "returnOnEquity": 0.20,
            "dividendYield": 0.03,
            "revenueGrowth": 0.10,
        }
        result = calc_fundamental_score(info)
        assert result["fundamental_score"] == float(10 + 7 + 10 + 7 + 7)
        assert result["per"] == 8.0
        assert result["data_quality"] == "ok"

    def test_calc_fundamental_score_empty_info(self):
        result = calc_fundamental_score({})
        assert result["data_quality"] == "partial"


class TestRating:
    def test_rating_strong_buy(self):
        assert get_rating(85) == "強い買い"

    def test_rating_buy(self):
        assert get_rating(65) == "買い"

    def test_rating_neutral(self):
        assert get_rating(45) == "中立"

    def test_rating_sell(self):
        assert get_rating(25) == "売り"

    def test_rating_strong_sell(self):
        assert get_rating(10) == "強い売り"


class TestBuildStockResult:
    def test_build_result_without_kurotenko(self):
        fundamental = {
            "fundamental_score": 35.0, "per": 10.0, "pbr": 1.0,
            "roe": 0.15, "dividend_yield": 0.02, "revenue_growth": 0.05, "data_quality": "ok"
        }
        technical = {"technical_score": 40.0, "ma_score": 20.0, "rsi_score": 10.0, "macd_score": 10.0}
        result = build_stock_result("7203.T", "トヨタ", "輸送用機器", fundamental, technical)
        assert result["total_score"] == 75.0
        assert result["rating"] == "買い"
        assert result["kurotenko_score"] is None

    def test_build_result_with_kurotenko(self):
        fundamental = {"fundamental_score": 40.0, "per": 8.0, "pbr": 0.9, "roe": 0.20, "dividend_yield": 0.03, "revenue_growth": 0.10, "data_quality": "ok"}
        technical = {"technical_score": 45.0, "ma_score": 20.0, "rsi_score": 15.0, "macd_score": 10.0}
        kurotenko = {"rating": 6, "year_end_turnaround": True, "consec_quarters_profit": True, "sales_yoy": True, "equity_ratio": False, "cf_positive": True, "cash_over_debt": True, "avg_volume": None, "market_cap": True}
        result = build_stock_result("7203.T", "トヨタ", "輸送用機器", fundamental, technical, kurotenko)
        assert result["kurotenko_score"] == pytest.approx(75.0)
        assert result["kurotenko_criteria"]["year_end_turnaround"] is True
```

- [ ] **Step 7: テストを実行して全て PASS することを確認**

```bash
cd backend
PYTHONPATH=/Users/mfujii/src/kabu-trade/backend python3 -m pytest tests/test_scoring.py -v
```

期待：全テスト PASS。

- [ ] **Step 8: Commit**

```bash
git add backend/app/analyzer/ backend/tests/test_scoring.py
git commit -m "feat: analyzer/ モジュールを stock-advisor から移植"
```

---

## Task 3: yfinance_client + scoring_service

**Files:**
- Create: `backend/app/external/yfinance_client.py`
- Create: `backend/app/services/scoring_service.py`

- [ ] **Step 1: yfinance_client.py を作成**

`backend/app/external/yfinance_client.py`：

```python
"""yfinance 同期ラッパー - バッチスコアリング専用

yfinance は同期ライブラリ。async 環境からは run_in_executor 経由で呼ぶこと。
"""

import logging
import time

logger = logging.getLogger(__name__)

MAX_RETRIES = 2
RETRY_SLEEP = 1.0

try:
    from curl_cffi import requests as _cffi_requests
    _YF_SESSION = _cffi_requests.Session(impersonate="chrome")
    logger.info("yfinance_client: curl-cffi セッションを使用")
except Exception:
    _YF_SESSION = None


def fetch_stock_data(symbol: str) -> dict | None:
    """symbol の yfinance データを取得して返す。失敗時は None。

    Returns:
        {"symbol": str, "history": pd.DataFrame, "info": dict} or None
    """
    import yfinance as yf

    for attempt in range(MAX_RETRIES + 1):
        try:
            ticker = yf.Ticker(symbol, session=_YF_SESSION)
            history = ticker.history(period="1y")
            if history.empty:
                logger.warning("%s: 履歴データが空", symbol)
                return None
            return {"symbol": symbol, "history": history, "info": ticker.info or {}}
        except Exception as e:
            if attempt < MAX_RETRIES:
                logger.warning("%s: 取得失敗 (%d/%d) - %s", symbol, attempt + 1, MAX_RETRIES + 1, e)
                time.sleep(RETRY_SLEEP)
            else:
                logger.error("%s: 取得断念 - %s", symbol, e)
                return None


def load_jpx_symbols() -> list[dict]:
    """JPX 銘柄マスター Excel をダウンロードして銘柄リストを返す。

    Returns:
        [{"symbol": "7203.T", "name": "トヨタ自動車", "market": "プライム（内国株式）"}, ...]
    """
    import io
    import requests
    import pandas as pd

    JPX_EXCEL_URL = (
        "https://www.jpx.co.jp/markets/statistics-equities/misc/"
        "tvdivq0000001vg2-att/data_j.xls"
    )
    resp = requests.get(JPX_EXCEL_URL, timeout=30)
    resp.raise_for_status()
    df = pd.read_excel(io.BytesIO(resp.content), dtype=str)
    rows = []
    for _, row in df.iterrows():
        code = str(row.get("コード", "")).strip()
        name = str(row.get("銘柄名", "")).strip()
        market = str(row.get("市場・商品区分", "")).strip()
        if not code or code == "nan":
            continue
        rows.append({"symbol": f"{code}.T", "name": name, "market": market})
    return rows
```

- [ ] **Step 2: scoring_service.py を作成**

`backend/app/services/scoring_service.py`：

```python
"""バッチスコアリングサービス

JPX 全銘柄を yfinance で取得してスコアリングし、stock_scores テーブルに保存する。
進捗は Redis の batch:scoring:status キーに JSON で保存する。
"""

import json
import logging
from datetime import datetime, timezone
from concurrent.futures import ThreadPoolExecutor, as_completed

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, desc

from app.external.yfinance_client import fetch_stock_data, load_jpx_symbols
from app.analyzer.fundamental import calc_fundamental_score
from app.analyzer.technical import calc_technical_score
from app.analyzer.kurotenko_screener import evaluate_candidate
from app.analyzer.scorer import build_stock_result
from app.models.stock_score import StockScore

logger = logging.getLogger(__name__)

BATCH_REDIS_KEY = "batch:scoring:status"
MAX_WORKERS = 10  # 並列フェッチ数（yfinance レート制限に注意）


def _score_symbol(symbol: str, name: str | None, sector: str | None) -> dict | None:
    """1銘柄をスコアリングして dict を返す。失敗時は None。（同期関数）"""
    data = fetch_stock_data(symbol)
    if data is None:
        return None
    try:
        fundamental = calc_fundamental_score(data["info"])
        technical = calc_technical_score(data["history"])
        kurotenko = evaluate_candidate(symbol)
        return build_stock_result(symbol, name, sector, fundamental, technical, kurotenko)
    except Exception as e:
        logger.error("%s: スコアリング失敗 - %s", symbol, e)
        return None


def run_batch_scoring_sync(redis_client) -> dict:
    """バッチスコアリングを同期で実行する（ThreadPoolExecutor 内で呼ぶ）。

    Args:
        redis_client: sync redis client（asyncio 非対応の同期版）

    Returns:
        {"processed": int, "failed": int, "total": int}
    """
    from sqlalchemy import create_engine
    from sqlalchemy.orm import Session
    from app.core.config import settings

    # 同期エンジンを使用（スレッド内なので asyncpg は使えない）
    sync_url = settings.DATABASE_URL.replace("+asyncpg", "+psycopg2")
    engine = create_engine(sync_url)

    # JPX銘柄リストを取得
    logger.info("JPX 銘柄マスターを取得中...")
    try:
        symbols_data = load_jpx_symbols()
    except Exception as e:
        logger.error("JPX銘柄マスター取得失敗: %s", e)
        return {"processed": 0, "failed": 0, "total": 0}

    total = len(symbols_data)
    processed = 0
    failed = 0

    # Redis に開始状態を記録
    _set_status(redis_client, "running", total=total, processed=0, failed=0)
    logger.info("バッチスコアリング開始: %d 銘柄", total)

    symbol_map = {row["symbol"]: row for row in symbols_data}

    with ThreadPoolExecutor(max_workers=MAX_WORKERS) as executor:
        futures = {
            executor.submit(_score_symbol, row["symbol"], row["name"], row["market"]): row["symbol"]
            for row in symbols_data
        }
        with Session(engine) as session:
            for future in as_completed(futures):
                sym = futures[future]
                try:
                    result = future.result()
                except Exception as e:
                    logger.error("%s: 予期せぬエラー - %s", sym, e)
                    result = None

                if result is not None:
                    record = StockScore(**result)
                    session.add(record)
                    processed += 1
                else:
                    error_record = StockScore(
                        symbol=sym,
                        name=symbol_map[sym]["name"],
                        data_quality="fetch_error",
                    )
                    session.add(error_record)
                    failed += 1

                # 100件ごとに commit + Redis 更新
                if (processed + failed) % 100 == 0:
                    session.commit()
                    _set_status(redis_client, "running", total=total, processed=processed, failed=failed)
                    logger.info("進捗: %d/%d (失敗: %d)", processed + failed, total, failed)

            session.commit()

    _set_status(redis_client, "done", total=total, processed=processed, failed=failed, finished=True)
    logger.info("バッチスコアリング完了: 成功 %d / 失敗 %d", processed, failed)
    return {"processed": processed, "failed": failed, "total": total}


def _set_status(redis_client, status: str, total: int = 0, processed: int = 0, failed: int = 0, finished: bool = False):
    """Redis に進捗を書き込む（同期版）"""
    data = {
        "status": status,
        "total": total,
        "processed": processed,
        "failed": failed,
        "started_at": datetime.now(timezone.utc).isoformat(),
        "finished_at": datetime.now(timezone.utc).isoformat() if finished else None,
    }
    try:
        redis_client.set(BATCH_REDIS_KEY, json.dumps(data))
    except Exception as e:
        logger.warning("Redis 書き込み失敗: %s", e)


async def get_batch_status(redis_client) -> dict:
    """Redis から現在のバッチ進捗を取得する（非同期版）。"""
    try:
        raw = await redis_client.get(BATCH_REDIS_KEY)
        if raw:
            return json.loads(raw)
    except Exception:
        pass
    return {"status": "idle", "total": 0, "processed": 0, "failed": 0, "started_at": None, "finished_at": None}
```

- [ ] **Step 3: Commit**

```bash
git add backend/app/external/yfinance_client.py backend/app/services/scoring_service.py
git commit -m "feat: yfinance_client と scoring_service を追加"
```

---

## Task 4: APScheduler + Batch API

**Files:**
- Create: `backend/app/api/v1/batch.py`
- Modify: `backend/app/main.py`

- [ ] **Step 1: batch.py を作成**

`backend/app/api/v1/batch.py`：

```python
"""バッチスコアリング API"""

import asyncio
from fastapi import APIRouter, HTTPException
from app.core.redis_client import get_redis
from app.services.scoring_service import run_batch_scoring_sync, get_batch_status, BATCH_REDIS_KEY

router = APIRouter()

# 実行中フラグ（同一プロセス内の多重実行防止）
_running = False


@router.post("/scoring/run", status_code=202)
async def trigger_batch_scoring():
    """バッチスコアリングを手動トリガーする（非同期で開始して即返す）"""
    global _running
    if _running:
        raise HTTPException(status_code=409, detail="バッチスコアリングは既に実行中です")

    _running = True
    redis = await get_redis()

    async def _run():
        global _running
        try:
            import redis as sync_redis_lib
            from app.core.config import settings
            sync_redis = sync_redis_lib.from_url(settings.REDIS_URL, decode_responses=True)
            loop = asyncio.get_event_loop()
            await loop.run_in_executor(None, run_batch_scoring_sync, sync_redis)
        finally:
            _running = False

    asyncio.create_task(_run())
    return {"message": "バッチスコアリングを開始しました", "status": "accepted"}


@router.get("/scoring/status")
async def get_scoring_status():
    """バッチスコアリングの現在の進捗を返す"""
    redis = await get_redis()
    return await get_batch_status(redis)
```

- [ ] **Step 2: main.py に APScheduler + 新ルーターを追加**

`backend/app/main.py` を修正。`lifespan` 関数と末尾のルーター登録部分を更新：

```python
# lifespan の yield の前（起動時）に追加：
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger
import pytz

_scheduler = BackgroundScheduler(timezone=pytz.timezone("Asia/Tokyo"))


def _scheduled_batch():
    """APScheduler から呼ばれるバッチ実行（同期）"""
    import redis as sync_redis_lib
    from app.core.config import settings
    from app.services.scoring_service import run_batch_scoring_sync
    sync_redis = sync_redis_lib.from_url(settings.REDIS_URL, decode_responses=True)
    run_batch_scoring_sync(sync_redis)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """アプリケーションのライフサイクル管理"""
    try:
        await get_redis()
    except Exception as e:
        print(f"⚠ Redis接続エラー（無視）: {e}")
    # APScheduler: 毎日 18:00 JST
    _scheduler.add_job(_scheduled_batch, CronTrigger(hour=18, minute=0))
    _scheduler.start()
    yield
    _scheduler.shutdown(wait=False)
    try:
        await close_redis()
    except Exception:
        pass
```

末尾のルーター登録に追加：

```python
from app.api.v1 import batch
app.include_router(batch.router, prefix="/api/v1/batch", tags=["batch"])
```

また `requirements.txt` に `pytz>=2023.3` を追加（APScheduler のタイムゾーン指定に必要）。

- [ ] **Step 3: サーバーを起動してエンドポイントを確認**

```bash
cd backend
uvicorn app.main:app --reload
```

別ターミナルで：

```bash
curl -X POST http://localhost:8000/api/v1/batch/scoring/run
# 期待: {"message": "バッチスコアリングを開始しました", "status": "accepted"}

curl http://localhost:8000/api/v1/batch/scoring/status
# 期待: {"status": "running" or "idle", ...}
```

- [ ] **Step 4: Commit**

```bash
git add backend/app/api/v1/batch.py backend/app/main.py backend/requirements.txt
git commit -m "feat: APScheduler と batch API を追加（毎日 18:00 JST 自動実行）"
```

---

## Task 5: Scores API + analysis_axes_service + Pydantic スキーマ

**Files:**
- Create: `backend/app/schemas/stock_score.py`
- Create: `backend/app/services/analysis_axes_service.py`
- Create: `backend/app/api/v1/scores.py`
- Create: `backend/tests/test_scores_api.py`

- [ ] **Step 1: Pydantic スキーマを作成**

`backend/app/schemas/stock_score.py`：

```python
"""StockScore Pydantic スキーマ"""

from datetime import datetime
from typing import Optional, Any
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
    kurotenko_criteria: Optional[dict[str, Any]] = None
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
    detail: dict[str, Any] = Field(default_factory=dict)


class AnalysisAxesResponse(BaseModel):
    symbol: str
    axes: list[AnalysisAxis]
```

- [ ] **Step 2: analysis_axes_service.py を作成**

`backend/app/services/analysis_axes_service.py`：

```python
"""多軸分析集約サービス

stock_scores（最新1件）と chart_analyses（最新1件）を symbol で結合して返す。
"""

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, desc

from app.models.stock_score import StockScore
from app.models.chart_analysis import ChartAnalysis
from app.schemas.stock_score import AnalysisAxesResponse, AnalysisAxis


async def get_analysis_axes(symbol: str, db: AsyncSession) -> AnalysisAxesResponse:
    """symbol の全分析軸を集約して返す。"""

    # 最新の StockScore を取得
    score_stmt = (
        select(StockScore)
        .where(StockScore.symbol == symbol)
        .order_by(desc(StockScore.scored_at))
        .limit(1)
    )
    score_result = await db.execute(score_stmt)
    stock_score = score_result.scalar_one_or_none()

    # 最新の ChartAnalysis を取得
    chart_stmt = (
        select(ChartAnalysis)
        .where(ChartAnalysis.symbol == symbol)
        .order_by(desc(ChartAnalysis.created_at))
        .limit(1)
    )
    chart_result = await db.execute(chart_stmt)
    chart_analysis = chart_result.scalar_one_or_none()

    axes: list[AnalysisAxis] = []

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

    return AnalysisAxesResponse(symbol=symbol, axes=axes)
```

- [ ] **Step 3: scores.py（API）を作成**

`backend/app/api/v1/scores.py`：

```python
"""スコアAPI"""

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, desc, func
from typing import Literal

from app.core.database import get_db
from app.models.stock_score import StockScore
from app.schemas.stock_score import StockScoreResponse, AnalysisAxesResponse
from app.services.analysis_axes_service import get_analysis_axes

router = APIRouter()


@router.get("", response_model=list[StockScoreResponse])
async def list_scores(
    sort: Literal["total_score", "fundamental_score", "technical_score", "kurotenko_score"] = "total_score",
    limit: int = Query(100, ge=1, le=500),
    db: AsyncSession = Depends(get_db),
):
    """全銘柄スコア一覧（最新スコアのみ、指定軸で降順ソート）"""
    # 銘柄ごとに最新の scored_at を持つレコードのみ返す
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
    return result.scalars().all()


@router.get("/{symbol}", response_model=StockScoreResponse)
async def get_score(symbol: str, db: AsyncSession = Depends(get_db)):
    """銘柄の最新スコアを返す"""
    stmt = (
        select(StockScore)
        .where(StockScore.symbol == symbol)
        .order_by(desc(StockScore.scored_at))
        .limit(1)
    )
    result = await db.execute(stmt)
    score = result.scalar_one_or_none()
    if not score:
        from fastapi import HTTPException
        raise HTTPException(status_code=404, detail=f"銘柄 {symbol} のスコアが見つかりません")
    return score


@router.get("/{symbol}/axes", response_model=AnalysisAxesResponse)
async def get_axes(symbol: str, db: AsyncSession = Depends(get_db)):
    """銘柄の全分析軸集約を返す"""
    return await get_analysis_axes(symbol, db)
```

- [ ] **Step 4: main.py にルーターを登録**

`backend/app/main.py` 末尾に追加：

```python
from app.api.v1 import scores
app.include_router(scores.router, prefix="/api/v1/scores", tags=["scores"])
```

- [ ] **Step 5: テストを書く**

`backend/tests/test_scores_api.py`：

```python
"""scores API のテスト"""
import pytest
from httpx import AsyncClient, ASGITransport
from app.main import app


@pytest.mark.asyncio
async def test_list_scores_empty():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        response = await client.get("/api/v1/scores")
    assert response.status_code == 200
    assert isinstance(response.json(), list)


@pytest.mark.asyncio
async def test_get_score_not_found():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        response = await client.get("/api/v1/scores/9999.T")
    assert response.status_code == 404


@pytest.mark.asyncio
async def test_get_axes_empty():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        response = await client.get("/api/v1/scores/9999.T/axes")
    assert response.status_code == 200
    data = response.json()
    assert data["symbol"] == "9999.T"
    assert data["axes"] == []


@pytest.mark.asyncio
async def test_batch_status():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        response = await client.get("/api/v1/batch/scoring/status")
    assert response.status_code == 200
    data = response.json()
    assert "status" in data
    assert "processed" in data
```

- [ ] **Step 6: テストを実行**

```bash
cd backend
PYTHONPATH=/Users/mfujii/src/kabu-trade/backend python3 -m pytest tests/test_scores_api.py -v
```

期待: 全テスト PASS。

- [ ] **Step 7: Commit**

```bash
git add backend/app/schemas/stock_score.py backend/app/services/analysis_axes_service.py backend/app/api/v1/scores.py backend/tests/test_scores_api.py backend/app/main.py
git commit -m "feat: scores API と analysis_axes_service を追加"
```

---

## Task 6: フロントエンド型定義 + API クライアント

**Files:**
- Create: `frontend/src/types/stockScore.ts`
- Create: `frontend/src/services/api/scoresApi.ts`

- [ ] **Step 1: TypeScript 型定義を作成**

`frontend/src/types/stockScore.ts`：

```typescript
export interface StockScore {
  id: number;
  symbol: string;
  name: string | null;
  sector: string | null;
  scored_at: string;
  total_score: number | null;
  rating: string | null;
  fundamental_score: number | null;
  technical_score: number | null;
  kurotenko_score: number | null;
  kurotenko_criteria: Record<string, boolean | null> | null;
  per: number | null;
  pbr: number | null;
  roe: number | null;
  dividend_yield: number | null;
  revenue_growth: number | null;
  ma_score: number | null;
  rsi_score: number | null;
  macd_score: number | null;
  data_quality: 'ok' | 'fetch_error' | 'partial';
}

export interface AnalysisAxis {
  name: string;
  score: number | null;
  recommendation: string | null;
  detail: Record<string, unknown>;
}

export interface AnalysisAxes {
  symbol: string;
  axes: AnalysisAxis[];
}

export interface BatchStatus {
  status: 'idle' | 'running' | 'done' | 'error';
  total: number;
  processed: number;
  failed: number;
  started_at: string | null;
  finished_at: string | null;
}
```

- [ ] **Step 2: API クライアントを作成**

`frontend/src/services/api/scoresApi.ts`：

```typescript
import axios from 'axios';
import type { StockScore, AnalysisAxes, BatchStatus } from '@/types/stockScore';

const API_BASE_URL = '/api/v1';

const apiClient = axios.create({
  baseURL: API_BASE_URL,
  headers: { 'Content-Type': 'application/json' },
});

type SortField = 'total_score' | 'fundamental_score' | 'technical_score' | 'kurotenko_score';

export const scoresApi = {
  async listScores(sort: SortField = 'total_score', limit = 100): Promise<StockScore[]> {
    const response = await apiClient.get<StockScore[]>('/scores', { params: { sort, limit } });
    return response.data;
  },

  async getScore(symbol: string): Promise<StockScore> {
    const response = await apiClient.get<StockScore>(`/scores/${symbol}`);
    return response.data;
  },

  async getAxes(symbol: string): Promise<AnalysisAxes> {
    const response = await apiClient.get<AnalysisAxes>(`/scores/${symbol}/axes`);
    return response.data;
  },

  async triggerBatch(): Promise<{ message: string; status: string }> {
    const response = await apiClient.post('/batch/scoring/run');
    return response.data;
  },

  async getBatchStatus(): Promise<BatchStatus> {
    const response = await apiClient.get<BatchStatus>('/batch/scoring/status');
    return response.data;
  },
};
```

- [ ] **Step 3: 型チェックを実行**

```bash
cd frontend
npx tsc --noEmit
```

期待: エラーなし。

- [ ] **Step 4: Commit**

```bash
git add frontend/src/types/stockScore.ts frontend/src/services/api/scoresApi.ts
git commit -m "feat: StockScore TypeScript 型定義と API クライアントを追加"
```

---

## Task 7: AnalysisAxesPanel + StockDetailPage 統合

**Files:**
- Create: `frontend/src/components/stock/AnalysisAxesPanel.tsx`
- Modify: `frontend/src/components/stock/index.ts`
- Modify: `frontend/src/pages/StockDetailPage.tsx`

- [ ] **Step 1: AnalysisAxesPanel を作成**

`frontend/src/components/stock/AnalysisAxesPanel.tsx`：

```tsx
import { useState, useEffect } from 'react';
import { scoresApi } from '@/services/api/scoresApi';
import type { AnalysisAxes, AnalysisAxis } from '@/types/stockScore';

interface Props {
  symbol: string;
}

const AXIS_COLORS: Record<string, string> = {
  'ファンダメンタル': '#3b82f6',
  'テクニカル': '#10b981',
  '黒点子': '#8b5cf6',
  'チャート分析': '#f59e0b',
};

const ScoreBar = ({ score, color }: { score: number; color: string }) => (
  <div style={{ display: 'flex', alignItems: 'center', gap: 8, marginTop: 8 }}>
    <div style={{ flex: 1, height: 6, background: '#374151', borderRadius: 3, overflow: 'hidden' }}>
      <div style={{ width: `${score}%`, height: '100%', background: color, borderRadius: 3 }} />
    </div>
    <span style={{ fontSize: 13, fontWeight: 700, color, minWidth: 36 }}>{Math.round(score)}</span>
  </div>
);

const AxisCard = ({ axis }: { axis: AnalysisAxis }) => {
  const [expanded, setExpanded] = useState(false);
  const color = AXIS_COLORS[axis.name] ?? '#6b7280';

  return (
    <div
      style={{
        border: `1px solid #374151`,
        borderRadius: 10,
        padding: '14px 16px',
        background: '#1f2937',
        borderTop: `3px solid ${color}`,
      }}
    >
      <div style={{ fontSize: 11, fontWeight: 700, textTransform: 'uppercase', color: '#9ca3af', letterSpacing: '0.5px' }}>
        {axis.name}
      </div>

      {axis.score !== null ? (
        <ScoreBar score={axis.score} color={color} />
      ) : axis.recommendation ? (
        <div style={{ marginTop: 8, fontSize: 18, fontWeight: 700, color }}>
          {axis.recommendation.toUpperCase()}
        </div>
      ) : (
        <div style={{ marginTop: 8, fontSize: 13, color: '#6b7280' }}>データなし</div>
      )}

      <button
        onClick={() => setExpanded(!expanded)}
        style={{
          marginTop: 10, fontSize: 11, color: '#6b7280', background: 'none',
          border: 'none', cursor: 'pointer', padding: 0,
        }}
      >
        {expanded ? '▲ 閉じる' : '▼ 詳細'}
      </button>

      {expanded && (
        <div style={{ marginTop: 8, borderTop: '1px solid #374151', paddingTop: 8 }}>
          {Object.entries(axis.detail).map(([key, value]) => (
            value !== null && value !== undefined && typeof value !== 'object' ? (
              <div key={key} style={{ display: 'flex', justifyContent: 'space-between', padding: '2px 0', fontSize: 12 }}>
                <span style={{ color: '#9ca3af' }}>{key}</span>
                <span style={{ fontWeight: 600, color: value === true ? '#34d399' : value === false ? '#f87171' : '#e5e7eb' }}>
                  {typeof value === 'boolean' ? (value ? '✓' : '✗') : String(value)}
                </span>
              </div>
            ) : null
          ))}
        </div>
      )}
    </div>
  );
};

const AnalysisAxesPanel = ({ symbol }: Props) => {
  const [axes, setAxes] = useState<AnalysisAxes | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    scoresApi.getAxes(symbol)
      .then(setAxes)
      .catch(() => setAxes(null))
      .finally(() => setLoading(false));
  }, [symbol]);

  if (loading) return <div style={{ color: '#6b7280', fontSize: 13 }}>分析軸を読み込み中...</div>;
  if (!axes || axes.axes.length === 0) return <div style={{ color: '#6b7280', fontSize: 13 }}>スコアデータがありません（バッチ未実行）</div>;

  return (
    <div style={{ marginTop: 16 }}>
      <h3 style={{ fontSize: 13, fontWeight: 700, textTransform: 'uppercase', letterSpacing: '0.5px', color: '#9ca3af', marginBottom: 12 }}>
        多軸分析
      </h3>
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))', gap: 12 }}>
        {axes.axes.map((axis) => (
          <AxisCard key={axis.name} axis={axis} />
        ))}
      </div>
    </div>
  );
};

export default AnalysisAxesPanel;
```

- [ ] **Step 2: index.ts にエクスポートを追加**

`frontend/src/components/stock/index.ts` を確認して、`AnalysisAxesPanel` のエクスポートを追加：

```typescript
export { default as AnalysisAxesPanel } from './AnalysisAxesPanel';
```

- [ ] **Step 3: StockDetailPage に AnalysisAxesPanel を追加**

`frontend/src/pages/StockDetailPage.tsx` の import に追加：

```typescript
import AnalysisAxesPanel from '@/components/stock/AnalysisAxesPanel';
```

既存の `ChartAnalysisPanel` の後に追加（`{chartAnalysis && <ChartAnalysisPanel ... />}` の直後）：

```tsx
{/* 多軸分析パネル */}
{code && <AnalysisAxesPanel symbol={code} />}
```

- [ ] **Step 4: 型チェック**

```bash
cd frontend
npx tsc --noEmit
```

期待: エラーなし。

- [ ] **Step 5: Commit**

```bash
git add frontend/src/components/stock/AnalysisAxesPanel.tsx frontend/src/components/stock/index.ts frontend/src/pages/StockDetailPage.tsx
git commit -m "feat: AnalysisAxesPanel を追加して StockDetailPage に統合"
```

---

## Task 8: StockRankingPage（スコアランキング一覧）

**Files:**
- Create: `frontend/src/pages/StockRankingPage.tsx`
- Modify: `frontend/src/App.tsx`

- [ ] **Step 1: StockRankingPage を作成**

`frontend/src/pages/StockRankingPage.tsx`：

```tsx
import { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { scoresApi } from '@/services/api/scoresApi';
import type { StockScore, BatchStatus } from '@/types/stockScore';

const RATING_COLORS: Record<string, string> = {
  '強い買い': '#3b82f6',
  '買い': '#10b981',
  '中立': '#9ca3af',
  '売り': '#f59e0b',
  '強い売り': '#ef4444',
};

const ScoreBar = ({ score }: { score: number | null }) => {
  if (score === null) return <span style={{ color: '#4b5563' }}>—</span>;
  const pct = Math.min(100, Math.max(0, score));
  return (
    <div style={{ display: 'flex', alignItems: 'center', gap: 6 }}>
      <div style={{ width: 80, height: 4, background: '#374151', borderRadius: 2, overflow: 'hidden' }}>
        <div style={{ width: `${pct}%`, height: '100%', background: 'linear-gradient(90deg,#3b82f6,#8b5cf6)', borderRadius: 2 }} />
      </div>
      <span style={{ fontSize: 13, fontWeight: 700, color: '#a78bfa', minWidth: 28 }}>{Math.round(pct)}</span>
    </div>
  );
};

const StockRankingPage = () => {
  const [scores, setScores] = useState<StockScore[]>([]);
  const [batchStatus, setBatchStatus] = useState<BatchStatus | null>(null);
  const [loading, setLoading] = useState(true);
  const [triggering, setTriggering] = useState(false);
  const navigate = useNavigate();

  useEffect(() => {
    Promise.all([
      scoresApi.listScores('total_score', 100),
      scoresApi.getBatchStatus(),
    ]).then(([s, b]) => {
      setScores(s);
      setBatchStatus(b);
    }).finally(() => setLoading(false));
  }, []);

  const handleTriggerBatch = async () => {
    setTriggering(true);
    try {
      await scoresApi.triggerBatch();
      alert('バッチスコアリングを開始しました');
    } catch (e: unknown) {
      const msg = e instanceof Error ? e.message : 'エラーが発生しました';
      alert(msg);
    } finally {
      setTriggering(false);
    }
  };

  if (loading) return <div style={{ padding: 24, color: '#9ca3af' }}>読み込み中...</div>;

  return (
    <div style={{ padding: 24, maxWidth: 1200, margin: '0 auto' }}>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 16 }}>
        <div>
          <h1 style={{ fontSize: 20, fontWeight: 700 }}>銘柄スコアランキング</h1>
          {batchStatus && (
            <div style={{ fontSize: 12, color: '#6b7280', marginTop: 4 }}>
              最終更新: {batchStatus.finished_at ? new Date(batchStatus.finished_at).toLocaleString('ja-JP') : '未実行'}
              {batchStatus.status === 'running' && <span style={{ color: '#f59e0b', marginLeft: 8 }}>実行中...</span>}
            </div>
          )}
        </div>
        <button
          onClick={handleTriggerBatch}
          disabled={triggering || batchStatus?.status === 'running'}
          style={{
            padding: '8px 16px', background: '#7c3aed', color: 'white',
            border: 'none', borderRadius: 8, fontWeight: 600, cursor: 'pointer', fontSize: 13,
          }}
        >
          {triggering ? '開始中...' : '▶ スコアリング実行'}
        </button>
      </div>

      {scores.length === 0 ? (
        <div style={{ padding: 48, textAlign: 'center', color: '#6b7280' }}>
          スコアデータがありません。「スコアリング実行」でバッチを開始してください。
        </div>
      ) : (
        <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: 13 }}>
          <thead>
            <tr style={{ borderBottom: '1px solid #374151' }}>
              <th style={{ padding: '8px 12px', textAlign: 'left', color: '#6b7280', fontWeight: 600 }}>#</th>
              <th style={{ padding: '8px 12px', textAlign: 'left', color: '#6b7280', fontWeight: 600 }}>銘柄</th>
              <th style={{ padding: '8px 12px', textAlign: 'left', color: '#a78bfa', fontWeight: 600 }}>総合スコア ▼</th>
              <th style={{ padding: '8px 12px', textAlign: 'left', color: '#6b7280', fontWeight: 600 }}>レーティング</th>
              <th style={{ padding: '8px 12px', textAlign: 'left', color: '#6b7280', fontWeight: 600 }}>ファンダ</th>
              <th style={{ padding: '8px 12px', textAlign: 'left', color: '#6b7280', fontWeight: 600 }}>テクニカル</th>
              <th style={{ padding: '8px 12px', textAlign: 'left', color: '#6b7280', fontWeight: 600 }}>黒点子</th>
              <th style={{ padding: '8px 12px', textAlign: 'left', color: '#6b7280', fontWeight: 600 }}></th>
            </tr>
          </thead>
          <tbody>
            {scores.map((s, i) => (
              <tr
                key={s.id}
                style={{ borderBottom: '1px solid #1f2937', cursor: 'pointer' }}
                onMouseEnter={(e) => (e.currentTarget.style.background = '#1f2937')}
                onMouseLeave={(e) => (e.currentTarget.style.background = '')}
              >
                <td style={{ padding: '10px 12px', color: '#6b7280' }}>{i + 1}</td>
                <td style={{ padding: '10px 12px' }}>
                  <div style={{ fontWeight: 600, color: '#a78bfa' }}>{s.symbol}</div>
                  <div style={{ fontSize: 11, color: '#6b7280' }}>{s.name}</div>
                </td>
                <td style={{ padding: '10px 12px' }}><ScoreBar score={s.total_score} /></td>
                <td style={{ padding: '10px 12px' }}>
                  {s.rating ? (
                    <span style={{
                      padding: '2px 8px', borderRadius: 12, fontSize: 11, fontWeight: 600,
                      background: `${RATING_COLORS[s.rating] ?? '#6b7280'}22`,
                      color: RATING_COLORS[s.rating] ?? '#6b7280',
                    }}>{s.rating}</span>
                  ) : '—'}
                </td>
                <td style={{ padding: '10px 12px', color: '#60a5fa', fontWeight: 600 }}>
                  {s.fundamental_score !== null ? Math.round(s.fundamental_score) : '—'}
                </td>
                <td style={{ padding: '10px 12px', color: '#34d399', fontWeight: 600 }}>
                  {s.technical_score !== null ? Math.round(s.technical_score) : '—'}
                </td>
                <td style={{ padding: '10px 12px', color: '#a78bfa', fontWeight: 600 }}>
                  {s.kurotenko_score !== null ? `${Math.round(s.kurotenko_score)}%` : '—'}
                </td>
                <td style={{ padding: '10px 12px' }}>
                  <button
                    onClick={() => navigate(`/stocks/${s.symbol.replace('.T', '')}`)}
                    style={{ fontSize: 12, color: '#9ca3af', background: '#374151', border: 'none', borderRadius: 6, padding: '4px 10px', cursor: 'pointer' }}
                  >
                    詳細 →
                  </button>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      )}
    </div>
  );
};

export default StockRankingPage;
```

- [ ] **Step 2: App.tsx にルートを追加**

`frontend/src/App.tsx` を修正：

```tsx
import { BrowserRouter, Routes, Route } from 'react-router-dom'
import HomePage from './pages/HomePage'
import StockDetailPage from './pages/StockDetailPage'
import StockRankingPage from './pages/StockRankingPage'
import './App.css'

function App() {
  return (
    <BrowserRouter>
      <Routes>
        <Route path="/" element={<HomePage />} />
        <Route path="/stocks/:code" element={<StockDetailPage />} />
        <Route path="/ranking" element={<StockRankingPage />} />
      </Routes>
    </BrowserRouter>
  )
}

export default App
```

- [ ] **Step 3: 型チェック**

```bash
cd frontend
npx tsc --noEmit
```

期待: エラーなし。

- [ ] **Step 4: Commit**

```bash
git add frontend/src/pages/StockRankingPage.tsx frontend/src/App.tsx
git commit -m "feat: StockRankingPage を追加（/ranking でアクセス可能）"
```

---

## Self-Review チェックリスト

### Spec カバレッジ確認

| 要件 | タスク |
|---|---|
| 全銘柄バッチスコアリング（定期実行） | Task 3（scoring_service）+ Task 4（APScheduler） |
| ファンダメンタル軸 | Task 2（fundamental.py） |
| テクニカル軸（MA/RSI/MACD） | Task 2（technical.py） |
| 黒点子軸（8条件） | Task 2（kurotenko_screener.py） |
| TradingView MCP 軸 | Task 5（analysis_axes_service が chart_analyses を結合） |
| 銘柄一覧にスコア列 | Task 8（StockRankingPage /ranking） |
| 銘柄詳細に軸別パネル | Task 7（AnalysisAxesPanel in StockDetailPage） |
| バッチ手動トリガー API | Task 4（POST /api/v1/batch/scoring/run） |
| バッチ進捗確認 API | Task 4（GET /api/v1/batch/scoring/status） |
| yfinance データソース | Task 3（yfinance_client.py） |
| Redis 進捗管理 | Task 3（scoring_service._set_status） |
| fetch_error で継続 | Task 3（error_record with data_quality） |
| JPX 銘柄マスター取得 | Task 3（load_jpx_symbols） |
| Alembic マイグレーション | Task 1 |

全要件がカバーされています。
