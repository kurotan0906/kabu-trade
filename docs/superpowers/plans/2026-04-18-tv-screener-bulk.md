# TradingView Screener 一括取得 実装プラン

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** バッチスコアリングのデータソースを yfinance ループから TradingView Screener の一括取得へ切り替える。yfinance は個別銘柄データ専用に残す。

**Design:** `docs/superpowers/specs/2026-04-18-tv-screener-bulk-refactor.md`

**Architecture:** 既存の `calc_fundamental_score` / `build_stock_result` は無変更。TV Screener 行を yfinance `info` 互換 dict に変換するアダプター層と、TV 指標から直接スコアを算出する `calc_technical_score_from_tv` を新設。既存設定 `SCORING_DATA_SOURCE` に `"screener"` 値を足して feature flag 切替。

**Tech Stack:** Python 3.11, FastAPI, SQLAlchemy 2, `tradingview-screener` v3.1.0, pytest-asyncio

---

## ファイルマップ

| 操作 | パス |
|------|------|
| 新規 | `backend/app/external/tv_screener_client.py` |
| 新規 | `backend/app/external/tv_screener_adapter.py` |
| 新規 | `backend/app/analyzer/technical_from_tv.py` |
| 新規 | `backend/tests/test_tv_screener_client.py` |
| 新規 | `backend/tests/test_tv_screener_adapter.py` |
| 新規 | `backend/tests/test_technical_from_tv.py` |
| 新規 | `backend/scripts/compare_scoring_sources.py` |
| 修正 | `backend/app/services/scoring_service.py` |
| 修正 | `backend/app/core/config.py` |
| 修正 | `backend/requirements.txt` |
| 削除（Phase 3） | `backend/app/external/tradingview_ta_client.py` |

---

## Phase 1: 並行稼働モードの実装（feature flag OFF 既定）

### Task 1: 依存追加と config 拡張

**Files:**
- Modify: `backend/requirements.txt`
- Modify: `backend/app/core/config.py`

- [ ] **Step 1**: `backend/requirements.txt` に `tradingview-screener>=3.1,<4.0` を追加
- [ ] **Step 2**: `.venv/bin/pip install -r requirements.txt` で取り込み
- [ ] **Step 3**: `backend/app/core/config.py` の `SCORING_DATA_SOURCE` の許容値コメントに `"screener"` を追記。既定値は現行（`"hybrid"`）維持

---

### Task 2: `tv_screener_client.py` を作成する

**Files:**
- Create: `backend/app/external/tv_screener_client.py`

- [ ] **Step 1**: モジュール新規作成

```python
"""TradingView Screener 一括取得クライアント。

tradingview-screener パッケージ経由で market=japan の断面データを 1 回のクエリで取得する。
MCP と同一の HTTP API を叩くため、MCP で検証したフィルタ/カラムがそのまま使える。
"""
from __future__ import annotations

import logging
from typing import Any

from tradingview_screener import Query, col

logger = logging.getLogger(__name__)

TV_SCREENER_COLUMNS: list[str] = [
    "name", "description", "sector", "exchange", "currency",
    "close", "volume", "market_cap_basic", "average_volume_10d_calc",
    "price_earnings_ttm",
    "price_book_ratio", "price_book_fq",
    "return_on_equity",
    "dividend_yield_recent",
    "total_revenue_yoy_growth_fy",
    "RSI",
    "MACD.macd", "MACD.signal",
    "SMA25", "SMA75",
    "Recommend.All",
]


def _tv_to_symbol(ticker: str) -> str | None:
    """TV 形式 (e.g. 'TSE:7203') を DB 形式 ('7203.T') に変換。TSE 以外は None。"""
    if not ticker or ":" not in ticker:
        return None
    exchange, code = ticker.split(":", 1)
    if exchange != "TSE":
        return None
    return f"{code}.T"


def fetch_japan_market_snapshot() -> dict[str, dict[str, Any]]:
    """日本市場の株式断面を取得。key=`{code}.T`, value=column dict。

    TSE 以外（NAG/FSE/SSE）と `type != 'stock'` は除外。
    """
    n, df = (
        Query()
        .set_markets("japan")
        .select(*TV_SCREENER_COLUMNS)
        .where(col("type") == "stock")
        .limit(5000)
        .get_scanner_data()
    )
    logger.info("tv_screener snapshot: total=%s rows_in_df=%s", n, len(df))

    result: dict[str, dict[str, Any]] = {}
    for record in df.to_dict(orient="records"):
        symbol = _tv_to_symbol(record.get("ticker", ""))
        if symbol is None:
            continue
        result[symbol] = record
    return result
```

- [ ] **Step 2**: 疎通確認を `python -c` で実行し、行数・サンプル symbol・代表カラムに None がないことを確認

```bash
cd backend && .venv/bin/python3.11 -c "
from app.external.tv_screener_client import fetch_japan_market_snapshot
snap = fetch_japan_market_snapshot()
print('n=', len(snap))
print('sample=', next(iter(snap.items())))
"
```

---

### Task 3: `tv_screener_adapter.py` を作成する

**Files:**
- Create: `backend/app/external/tv_screener_adapter.py`

- [ ] **Step 1**: アダプター本体

```python
"""TV Screener 行データを既存スコアリング関数と互換な形式へ変換する。"""
from __future__ import annotations

from typing import Any


def _percent_to_ratio(value: Any) -> float | None:
    """TV の %単位値（例: 15 → 0.15）を小数に変換。None/NaN 安全。"""
    if value is None:
        return None
    try:
        v = float(value)
    except (TypeError, ValueError):
        return None
    if v != v:  # NaN
        return None
    return v / 100.0


def _safe_float(value: Any) -> float | None:
    if value is None:
        return None
    try:
        v = float(value)
    except (TypeError, ValueError):
        return None
    if v != v:
        return None
    return v


def tv_row_to_info(row: dict[str, Any]) -> dict[str, Any]:
    """TV row → yfinance ticker.info 互換 dict。

    calc_fundamental_score が期待するキー:
      trailingPE, priceToBook, returnOnEquity, dividendYield, revenueGrowth
    """
    pb = _safe_float(row.get("price_book_ratio"))
    if pb is None:
        pb = _safe_float(row.get("price_book_fq"))

    return {
        "trailingPE": _safe_float(row.get("price_earnings_ttm")),
        "priceToBook": pb,
        "returnOnEquity": _percent_to_ratio(row.get("return_on_equity")),
        "dividendYield": _percent_to_ratio(row.get("dividend_yield_recent")),
        "revenueGrowth": _percent_to_ratio(row.get("total_revenue_yoy_growth_fy")),
        "marketCap": _safe_float(row.get("market_cap_basic")),
        "longName": row.get("description") or row.get("name"),
        "sector": row.get("sector"),
    }


def tv_row_to_technical_features(row: dict[str, Any]) -> dict[str, Any]:
    """TV row → technical_from_tv 用の値 dict。"""
    return {
        "close": _safe_float(row.get("close")),
        "rsi": _safe_float(row.get("RSI")),
        "macd": _safe_float(row.get("MACD.macd")),
        "macd_signal": _safe_float(row.get("MACD.signal")),
        "sma25": _safe_float(row.get("SMA25")),
        "sma75": _safe_float(row.get("SMA75")),
    }
```

---

### Task 4: `technical_from_tv.py` を作成する

**Files:**
- Create: `backend/app/analyzer/technical_from_tv.py`

- [ ] **Step 1**: 現行 `technical.py` の `score_ma` / `score_rsi` のロジックを snapshot 入力向けに書き直す。MACD はクロスボーナス無しの二値判定

```python
"""TV Screener 指標値からテクニカルスコアを直接計算する（履歴不要版）。

現行 calc_technical_score(history) と同じ出力フォーマットを返すが、内部では
pandas_ta / ta 再計算は行わない。
"""
from __future__ import annotations

from typing import Any


def _score_ma(close: float | None, sma25: float | None, sma75: float | None) -> float:
    if close is None or sma25 is None or sma75 is None:
        return 6.0
    if close > sma25 > sma75:
        return 20.0
    if close > sma25:
        return 12.0
    if close < sma25 < sma75:
        return 0.0
    return 6.0


def _score_rsi(rsi: float | None) -> float:
    if rsi is None:
        return 7.5
    if rsi >= 70:
        return 5.0
    if rsi >= 50:
        return 15.0
    if rsi >= 30:
        return 5.0
    return 15.0


def _score_macd(macd: float | None, signal: float | None) -> float:
    """TV 断面では過去 N 本の crossover を見られないため、現行の recent_cross ボーナスは落とす。

    現行: macd > signal → 基本点 + （直近3本で上抜け時 +ボーナス）
    新 : macd > signal → +15, macd < signal → 0, それ以外 → 7.5
    """
    if macd is None or signal is None:
        return 7.5
    if macd > signal:
        return 15.0
    if macd < signal:
        return 0.0
    return 7.5


def calc_technical_score_from_tv(features: dict[str, Any]) -> dict[str, Any]:
    ma_score = _score_ma(features.get("close"), features.get("sma25"), features.get("sma75"))
    rsi_score = _score_rsi(features.get("rsi"))
    macd_score = _score_macd(features.get("macd"), features.get("macd_signal"))
    return {
        "technical_score": ma_score + rsi_score + macd_score,
        "ma_score": ma_score,
        "rsi_score": rsi_score,
        "macd_score": macd_score,
    }
```

- [ ] **Step 2**: 現行 `technical.py` のスコア配分（ma 0-20 / rsi 0-15 / macd 0-15 で合計 0-50）を実装から再確認し、数値が合うよう調整。**実装前に `backend/app/analyzer/technical.py` を Read して現行の最大値・閾値を正確にコピー**すること。

---

### Task 5: ユニットテストを追加

**Files:**
- Create: `backend/tests/test_tv_screener_adapter.py`
- Create: `backend/tests/test_technical_from_tv.py`
- Create: `backend/tests/test_tv_screener_client.py`

- [ ] **Step 1**: adapter のテスト（% → ratio 変換、None 安全、ratio/fq フォールバック）

```python
from app.external.tv_screener_adapter import tv_row_to_info, tv_row_to_technical_features


def test_percent_conversion():
    row = {"return_on_equity": 15.0, "dividend_yield_recent": 2.5, "total_revenue_yoy_growth_fy": 10.0}
    info = tv_row_to_info(row)
    assert info["returnOnEquity"] == 0.15
    assert info["dividendYield"] == 0.025
    assert info["revenueGrowth"] == 0.10


def test_pb_fallback():
    row = {"price_book_ratio": None, "price_book_fq": 1.5}
    info = tv_row_to_info(row)
    assert info["priceToBook"] == 1.5


def test_none_safety():
    info = tv_row_to_info({})
    assert all(v is None for v in (info["trailingPE"], info["priceToBook"], info["returnOnEquity"]))


def test_technical_features():
    row = {"close": 1000, "RSI": 55, "MACD.macd": 10, "MACD.signal": 5, "SMA25": 950, "SMA75": 900}
    feats = tv_row_to_technical_features(row)
    assert feats == {"close": 1000.0, "rsi": 55.0, "macd": 10.0, "macd_signal": 5.0, "sma25": 950.0, "sma75": 900.0}
```

- [ ] **Step 2**: `technical_from_tv` のテスト（完全陽転/中立/完全陰転、RSI 各帯、MACD クロス）

```python
from app.analyzer.technical_from_tv import calc_technical_score_from_tv


def test_full_bullish():
    result = calc_technical_score_from_tv({
        "close": 1100, "sma25": 1000, "sma75": 900,
        "rsi": 60, "macd": 5, "macd_signal": 3,
    })
    assert result["ma_score"] == 20
    assert result["rsi_score"] == 15
    assert result["macd_score"] == 15
    assert result["technical_score"] == 50


def test_full_bearish():
    result = calc_technical_score_from_tv({
        "close": 900, "sma25": 1000, "sma75": 1100,
        "rsi": 25, "macd": 1, "macd_signal": 3,
    })
    assert result["ma_score"] == 0
    assert result["macd_score"] == 0


def test_none_inputs_return_neutral():
    result = calc_technical_score_from_tv({})
    assert result["ma_score"] == 6
    assert result["rsi_score"] == 7.5
    assert result["macd_score"] == 7.5
```

- [ ] **Step 3**: `tv_screener_client` は `_tv_to_symbol` のパラメタライズテストのみ（fetch 本体はネットワーク越しで、統合テスト扱い）

```python
import pytest
from app.external.tv_screener_client import _tv_to_symbol


@pytest.mark.parametrize("ticker,expected", [
    ("TSE:7203", "7203.T"),
    ("TSE:6758", "6758.T"),
    ("NAG:1234", None),
    ("FSE:9999", None),
    ("", None),
    ("7203", None),
])
def test_tv_to_symbol(ticker, expected):
    assert _tv_to_symbol(ticker) == expected
```

- [ ] **Step 4**: ローカルで pytest 通過確認

```bash
cd backend && PYTHONPATH=. .venv/bin/pytest tests/test_tv_screener_adapter.py tests/test_technical_from_tv.py tests/test_tv_screener_client.py -v
```

---

### Task 6: `scoring_service.py` に screener 分岐を追加する

**Files:**
- Modify: `backend/app/services/scoring_service.py`

- [ ] **Step 1**: まず `backend/app/services/scoring_service.py` を Read して現在の `run_batch_scoring_sync` / `_score_symbol` / `_fetch_merged_data` のシグネチャと、Redis ステータス更新・checkpoint 処理の構造を把握する

- [ ] **Step 2**: 新関数 `_run_batch_scoring_screener` を追加（現行 `run_batch_scoring_sync` とは並列）

```python
def _run_batch_scoring_screener() -> None:
    """TV Screener 一括取得モードのバッチ。"""
    from app.external.tv_screener_client import fetch_japan_market_snapshot
    from app.external.tv_screener_adapter import (
        tv_row_to_info, tv_row_to_technical_features,
    )
    from app.analyzer.technical_from_tv import calc_technical_score_from_tv
    from app.analyzer.fundamental import calc_fundamental_score
    from app.analyzer.scorer import build_stock_result
    from app.external.yfinance_client import load_jpx_symbols

    _update_status({"phase": "snapshot", "progress": 0})
    snapshot = fetch_japan_market_snapshot()
    _update_status({"phase": "snapshot_done", "total_snapshot": len(snapshot)})

    jpx_df = load_jpx_symbols()
    total = len(jpx_df)

    with SessionLocal() as session:
        for idx, row in enumerate(jpx_df.itertuples(index=False)):
            symbol = row.symbol
            tv_row = snapshot.get(symbol)
            if tv_row is None:
                # データ欠損は missing_tv で空スコア保存。スキップでも可（運用で決定）。
                continue

            info = tv_row_to_info(tv_row)
            features = tv_row_to_technical_features(tv_row)
            fund = calc_fundamental_score(info)
            tech = calc_technical_score_from_tv(features)
            kurotenko = _get_kurotenko_cached_or_compute(symbol)

            result = build_stock_result(
                symbol=symbol, name=row.name, market=row.market,
                info=info, fund=fund, tech=tech, kurotenko=kurotenko,
            )
            session.add(StockScore(**result))

            if (idx + 1) % 100 == 0:
                session.commit()
                _update_status({"phase": "scoring", "progress": idx + 1, "total": total})
        session.commit()
    _update_status({"phase": "done", "progress": total, "total": total})
```

- [ ] **Step 3**: `run_batch_scoring_sync` の冒頭に分岐を挿入

```python
def run_batch_scoring_sync() -> None:
    if settings.SCORING_DATA_SOURCE == "screener":
        _run_batch_scoring_screener()
        return
    # ...以降は現行コード
```

- [ ] **Step 4**: 現行の `_fetch_merged_data` / `_score_symbol_with_retry` / ThreadPoolExecutor は **このフェーズでは触らない**（Phase 3 で削除）

- [ ] **Step 5**: 既存テスト（`tests/test_scoring.py`）が既定モード（hybrid）で通過することを確認

```bash
cd backend && PYTHONPATH=. .venv/bin/pytest tests/test_scoring.py -v
```

---

### Task 7: 差分比較スクリプトで品質検証

**Files:**
- Create: `backend/scripts/compare_scoring_sources.py`

- [ ] **Step 1**: top100 銘柄に対して「現行 hybrid」と「新 screener」両方でスコアを計算し、差分を CSV 出力

```python
"""hybrid vs screener スコア比較ツール。

Usage: PYTHONPATH=. .venv/bin/python scripts/compare_scoring_sources.py --limit 100
"""
import argparse, csv, statistics
from app.external.tv_screener_client import fetch_japan_market_snapshot
from app.external.tv_screener_adapter import tv_row_to_info, tv_row_to_technical_features
from app.analyzer.technical_from_tv import calc_technical_score_from_tv
from app.analyzer.fundamental import calc_fundamental_score
from app.analyzer.scorer import build_stock_result, get_rating
from app.external.yfinance_client import fetch_stock_data, load_jpx_symbols
from app.analyzer.technical import calc_technical_score

def score_hybrid(symbol):
    data = fetch_stock_data(symbol)
    fund = calc_fundamental_score(data["info"])
    tech = calc_technical_score(data["history"])
    return fund["fundamental_score"] + tech["technical_score"]

def score_screener(symbol, snapshot):
    row = snapshot.get(symbol)
    if row is None: return None
    info = tv_row_to_info(row)
    feats = tv_row_to_technical_features(row)
    fund = calc_fundamental_score(info)
    tech = calc_technical_score_from_tv(feats)
    return fund["fundamental_score"] + tech["technical_score"]

def main(limit):
    snapshot = fetch_japan_market_snapshot()
    symbols = [r.symbol for r in load_jpx_symbols().itertuples(index=False)][:limit]
    diffs = []
    with open("scoring_diff.csv", "w") as f:
        w = csv.writer(f)
        w.writerow(["symbol", "hybrid", "screener", "diff"])
        for s in symbols:
            try:
                h = score_hybrid(s); sc = score_screener(s, snapshot)
                if h is not None and sc is not None:
                    w.writerow([s, h, sc, sc - h])
                    diffs.append(sc - h)
            except Exception as e:
                print(s, "error:", e)
    print(f"n={len(diffs)} mean_diff={statistics.mean(diffs):.2f} "
          f"median={statistics.median(diffs):.2f} "
          f"abs_max={max(abs(d) for d in diffs):.2f}")

if __name__ == "__main__":
    p = argparse.ArgumentParser()
    p.add_argument("--limit", type=int, default=100)
    main(p.parse_args().limit)
```

- [ ] **Step 2**: ローカル実行し **合格ライン判定**

| 指標 | 合格ライン |
|---|---|
| mean_diff（絶対値） | ≤ 3 pt |
| rating 一致率 | ≥ 95% |
| abs_max（極端な外れ値） | ≤ 10 pt（超える銘柄は CSV を目視確認しフィールド欠損パターンを特定） |

基準外だったら `technical_from_tv` の閾値微調整 or adapter の単位変換再確認。**合格しない限り Phase 2 に進まない**

---

### Task 8: 手動検証（staging ≒ 開発環境）

- [ ] **Step 1**: `.env` or 環境変数で `SCORING_DATA_SOURCE=screener` を一時設定し、ローカルから `run_batch_scoring_sync` を直接呼び出す

```bash
cd backend && PYTHONPATH=. SCORING_DATA_SOURCE=screener .venv/bin/python3.11 -c "
from app.services.scoring_service import run_batch_scoring_sync
run_batch_scoring_sync()
"
```

- [ ] **Step 2**: 期待: 数十秒で完了、`stock_scores` に数千行が作成されていること。`data_quality != 'fetch_error'` の行数が現行バッチと同等かそれ以上

- [ ] **Step 3**: `SCORING_DATA_SOURCE=hybrid` に戻し既定運用に戻すこと

---

### Task 9: 本番リリース（Phase 1 完了）

- [ ] **Step 1**: `git add` → コミット → Cloud Run デプロイ

```bash
git add backend/ docs/
git commit -m "feat(scoring): add TV Screener bulk fetch mode behind SCORING_DATA_SOURCE=screener"
gcloud run deploy kabu-trade-backend --source backend/
```

- [ ] **Step 2**: Cloud Run 環境変数は **変更しない**（flag OFF のまま）。デプロイ後スモークテスト: `/api/v1/scores` が現行どおり返ることを確認

---

## Phase 2: 既定切替（1週間の監視期間）

### Task 10: Cloud Run 環境変数で切替

- [ ] **Step 1**: `gcloud run services update kabu-trade-backend --update-env-vars SCORING_DATA_SOURCE=screener`
- [ ] **Step 2**: 次回バッチ実行のログ（Cloud Logging）で以下を確認
  - `tv_screener snapshot: total=...` が出ていること
  - 全体の実行時間（開始〜完了）が数十秒に短縮されていること
  - `data_quality` 別の件数分布
- [ ] **Step 3**: 1 週間 `/api/v1/scores` の rating 分布モニタリング。大きな構成変化がないか確認
- [ ] **Step 4**: 問題発生時のロールバック手順を README に追記（`SCORING_DATA_SOURCE=hybrid` に戻すだけ）

---

### Task 11: TradingView 利用規約 最終確認

- [ ] **Step 1**: Phase 2 切替前に TradingView の公式ポリシー（Scanner/Screener API の商用/定期バッチ利用）を Web で再確認
- [ ] **Step 2**: 懸念がある場合、呼び出し頻度を「1 日 N 回まで」に自主制限する Redis カウンタを追加

---

## Phase 3: 旧パス削除

### Task 12: `tradingview_ta_client.py` を削除

**Files:**
- Delete: `backend/app/external/tradingview_ta_client.py`
- Modify: `backend/app/services/scoring_service.py`

- [ ] **Step 1**: `scoring_service.py` から `tradingview_ta_client` の import / 呼び出し / `hybrid` / `tv` 分岐を削除
- [ ] **Step 2**: `_fetch_merged_data` / `_score_symbol_with_retry` / `ThreadPoolExecutor` を削除
- [ ] **Step 3**: `config.py` から `SCORING_DATA_SOURCE`, `SCORING_MAX_WORKERS`, `SCORING_YFINANCE_MIN_INTERVAL_SEC` を削除
- [ ] **Step 4**: `Cloud Run` の環境変数から同項目を削除
- [ ] **Step 5**: `tests/test_scoring.py` の hybrid 前提テストを削除 or screener 前提にリライト

---

### Task 13: Phase 3 クリーンアップの最終確認

- [ ] **Step 1**: `grep -r "tradingview_ta_client\|SCORING_DATA_SOURCE\|SCORING_MAX_WORKERS" backend/` で残骸がないこと
- [ ] **Step 2**: 全テスト通過 → `git commit -m "chore(scoring): remove legacy yfinance/TA hybrid path"` → Cloud Run 再デプロイ

---

## スコープ外

以下は本プランでは触らない:
- `backend/scripts/bulk_tv_signals.py` / `batch_tv_analysis.py`（別サブシステム `tradingview_signals` 向け）
- `kurotenko_screener.evaluate_candidate`（yfinance 財務諸表に依存、変更しない）
- `ChartAnalysisService`（yfinance + `ta` ライブラリで独立動作）
- `/api/v1/scores` 等 API のレスポンス形式（互換維持）

---

## 完了条件

- Phase 1 Task 7 の差分比較で合格ライン達成
- Phase 2 で 1 週間 `SCORING_DATA_SOURCE=screener` 既定稼働し、ユーザーから不具合報告なし
- Phase 3 で旧コードが削除され、`grep` で残骸ゼロ
