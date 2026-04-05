# TradingView MCP 統合設計

## 概要

TradingView MCP（`get_technical_analysis` 等）で取得したリアルタイムテクニカル分析を kabu-trade に統合する。既存の yfinance バッチスコアリング（stock-advisor 統合）と並列に「TradingView テクニカル」軸を追加し、銘柄詳細とランキングページの両方でシグナルを表示できるようにする。

## アーキテクチャ

```
TradingView MCP (AI tool)
       ↓ Claude が呼び出す（MCP はバックエンドから直接呼べない）
get_technical_analysis("7203.T")
       ↓ 結果を POST
POST /api/v1/tradingview-signals/{symbol}
       ↓
tradingview_signals テーブル（PostgreSQL）
       ↓ GET で取得
フロントエンド（AnalysisAxesPanel / StockRankingPage）
```

ChartAnalysis と同じ「Claude が分析 → DB 保存 → フロントが表示」パターンを踏襲する。

## データモデル

### `tradingview_signals` テーブル

| カラム | 型 | 説明 |
|---|---|---|
| `id` | SERIAL PK | |
| `symbol` | VARCHAR(20) NOT NULL | 銘柄コード（例: `"7203"`、`.T` なし） |
| `recommendation` | VARCHAR(20) | `STRONG_BUY` / `BUY` / `NEUTRAL` / `SELL` / `STRONG_SELL` |
| `score` | FLOAT | 0–100 に変換したスコア |
| `buy_count` | INTEGER | 買いシグナル数 |
| `sell_count` | INTEGER | 売りシグナル数 |
| `neutral_count` | INTEGER | 中立シグナル数 |
| `ma_recommendation` | VARCHAR(20) | 移動平均サマリー |
| `osc_recommendation` | VARCHAR(20) | オシレーターサマリー |
| `details` | JSONB | 全指標の生データ |
| `updated_at` | TIMESTAMPTZ | 保存日時 |

インデックス: `ix_tradingview_signals_symbol`

### スコア変換

```
STRONG_BUY  → 100
BUY         → 75
NEUTRAL     → 50
SELL        → 25
STRONG_SELL → 0
```

## APIエンドポイント

| メソッド | パス | 説明 |
|---|---|---|
| `POST` | `/api/v1/tradingview-signals/{symbol}` | Claude が MCP 結果を保存 |
| `GET` | `/api/v1/tradingview-signals/{symbol}` | フロントが最新シグナルを取得 |
| `GET` | `/api/v1/tradingview-signals` | ランキングページ用一覧（全銘柄の最新1件） |

`POST` は常に新規 INSERT。取得系は `updated_at DESC LIMIT 1` で最新1件を返す（stock_scores と同じパターン）。

## フロントエンド

### AnalysisAxesPanel（5軸目追加）

既存 4 軸の末尾に TradingView 軸を追加。

```
[ファンダメンタル]   ████████░░  72
[テクニカル]        ██████░░░░  58
[黒田子]            █████░░░░░  45
[チャート分析]      AI所見テキスト
[TradingView]      █████████░  75  BUY   ← 新規
                   買い:12 / 売り:4 / 中立:6
```

展開すると `details` の移動平均・オシレーター内訳を表示。

### StockDetailPage

「チャート分析を更新」ボタンの隣に「TradingView更新」ボタンを追加。押下で `GET /api/v1/tradingview-signals/{symbol}` を呼び直してパネルを更新する。

### StockRankingPage

- テーブルに「TVシグナル」列を追加（`BUY` / `NEUTRAL` / `SELL` などをバッジ表示）
- 「スコアリング実行」ボタンの隣に「TradingViewバッチ分析」ボタンを追加（ユーザーが Claude に一括分析を依頼するトリガー）

## Claudeワークフロー

### 個別銘柄（StockDetailPage）

1. ユーザーが Claude Code で「7203 の TradingView 分析をして」と依頼
2. Claude が `get_technical_analysis("7203.T")` を MCP 経由で呼び出す
3. Claude が `POST /api/v1/tradingview-signals/7203` に結果を送信
4. フロントで「TradingView更新」ボタンを押すと最新が表示される

### バッチ（StockRankingPage）

1. ユーザーが Claude Code で「上位 N 銘柄を TradingView 一括分析して」と依頼
2. Claude がスコアランキングを `GET /api/v1/scores` で取得
3. 上位 N 銘柄に対して `get_technical_analysis` を順次呼び出し
4. 各銘柄を `POST /api/v1/tradingview-signals/{symbol}` で保存

## 新規ファイル構成

```
backend/
  app/models/tradingview_signal.py
  app/schemas/tradingview_signal.py
  app/api/v1/tradingview_signals.py
  alembic/versions/004_add_tradingview_signals.py

frontend/
  src/types/tradingviewSignal.ts
  src/services/api/tradingviewApi.ts
  # 修正:
  src/components/stock/AnalysisAxesPanel.tsx
  src/pages/StockDetailPage.tsx
  src/pages/StockRankingPage.tsx
```

## テスト方針

- バックエンド: `POST` / `GET` の各エンドポイントを pytest で確認（DBはNullPool fixture）
- フロントエンド: 型チェック（tsc）が通ること

## 除外スコープ

- TradingView MCP をバックエンドから直接呼び出す機構（MCP は AI ツールであり REST API ではない）
- リアルタイムストリーミング / WebSocket
- TradingView スコアを yfinance スコアと合算して `total_score` を再計算すること
