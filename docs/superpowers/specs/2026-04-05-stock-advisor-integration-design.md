# 設計ドキュメント: stock-advisor × kabu-trade 統合

- 作成日: 2026-04-05
- ステータス: 承認済み

## 概要

`../stock-advisor`（Flask + yfinance + SQLite）のスコアリング・分析機能を `kabu-trade`（FastAPI + PostgreSQL + React）に統合する。kabu-trade をベースとして stock-advisor の機能を移植し、1つのアプリケーションに集約する。

## 目標

- 全銘柄バッチスコアリング（定期実行）を kabu-trade 上で実現する
- 銘柄ごとに複数の分析軸（ファンダメンタル・テクニカル・黒点子・TradingView MCP）でスコアを表示する
- 銘柄一覧でスコアランキングを表示し、銘柄詳細で軸別の内訳を確認できる

## アーキテクチャ

```
kabu-trade/backend/app/
├── services/
│   ├── scoring_service.py        # バッチスコアリング制御
│   └── analysis_axes_service.py  # 銘柄ごとの多軸分析集約
├── external/
│   └── yfinance_client.py        # yfinanceラッパー（バッチ専用）
├── analyzer/                     # stock-advisorから移植
│   ├── technical.py              # MA/RSI/MACDスコア
│   ├── fundamental.py            # PER/PBR/ROEスコア
│   └── kurotenko_screener.py     # 黒点子スクリーナー
├── models/
│   └── stock_score.py            # スコアDBモデル
└── api/v1/
    ├── scores.py                 # スコアAPI（一覧・銘柄別）
    └── batch.py                  # バッチ実行API

frontend/src/
├── components/stock/
│   └── AnalysisAxesPanel.tsx     # 多軸スコア表示コンポーネント
└── pages/
    └── StockListPage.tsx         # 既存: スコア列を追加
```

## データモデル

### stock_scores テーブル（新規）

```sql
CREATE TABLE stock_scores (
    id                 SERIAL PRIMARY KEY,
    symbol             VARCHAR NOT NULL,
    name               VARCHAR,
    sector             VARCHAR,
    scored_at          TIMESTAMPTZ NOT NULL,
    -- 総合
    total_score        FLOAT,
    rating             VARCHAR,        -- "強い買い" / "買い" / "中立" / "様子見" / "売り"
    -- 軸別スコア（0〜100）
    fundamental_score  FLOAT,
    technical_score    FLOAT,
    kurotenko_score    FLOAT,          -- rating(0〜8) / 8 * 100 で正規化
    kurotenko_criteria JSONB,          -- 各条件の合否 {"year_end_turnaround": true, ...}
    -- 内訳
    per                FLOAT,
    pbr                FLOAT,
    roe                FLOAT,
    dividend_yield     FLOAT,
    revenue_growth     FLOAT,
    ma_score           FLOAT,
    rsi_score          FLOAT,
    macd_score         FLOAT,
    data_quality       VARCHAR DEFAULT 'ok'   -- 'ok' / 'fetch_error' / 'partial'
);
```

### 集約ビュー（AnalysisAxes）

`analysis_axes_service` が `stock_scores`（最新1件）と `chart_analyses`（TradingView MCP、最新1件）を銘柄コードで結合して返す。

```json
{
  "symbol": "7203",
  "axes": [
    { "name": "ファンダメンタル", "score": 72, "detail": { "per": 8.5, "pbr": 0.9, "roe": 12.3, "dividend_yield": 2.8, "revenue_growth": 5.1 } },
    { "name": "テクニカル",       "score": 65, "detail": { "ma_score": 20, "rsi_score": 10, "macd_score": 8 } },
    { "name": "黒点子",           "score": 80, "detail": { "criteria_met": 6, "criteria_total": 8, "year_end_turnaround": true, "consec_quarters_profit": true, "sales_yoy": true, "equity_ratio": false, "cf_positive": true, "cash_over_debt": true } },
    { "name": "チャート分析",     "score": null, "recommendation": "Buy", "detail": { "summary": "...", "analyzed_at": "2026-04-05T10:00:00Z" } }
  ]
}
```

## API

| メソッド | パス | 説明 |
|---|---|---|
| GET | `/api/v1/scores` | 全銘柄スコア一覧（`?sort=total_score&limit=100`） |
| GET | `/api/v1/scores/{symbol}` | 銘柄別スコア（最新1件） |
| GET | `/api/v1/scores/{symbol}/axes` | 銘柄別の全分析軸集約 |
| POST | `/api/v1/batch/scoring/run` | バッチ手動トリガー |
| GET | `/api/v1/batch/scoring/status` | バッチ進捗確認 |

## バッチ実行

- **スケジューラ**: APScheduler を kabu-trade の FastAPI 起動時に組み込む
- **実行タイミング**: 毎日 18:00 JST（stock-advisor と同一）
- **対象銘柄**: JPX銘柄マスター（stock-advisor の `load_symbols()` ロジックを移植）
- **データソース**: yfinance（バッチ専用。リアルタイム取得は引き続き kabuステーション/モック）
- **進捗管理**: Redis に `batch:scoring:status` キーで保存（processed/total/started_at/status）
- **エラー処理**: yfinance 取得失敗時は `data_quality: "fetch_error"` で記録してスキップ、バッチ継続

## フロントエンド

### 銘柄一覧（StockListPage）
- 既存テーブルに `総合スコア` 列と `レーティング` バッジを追加
- スコア未取得銘柄は `-` 表示
- スコア列でソート可能（降順デフォルト）

### 銘柄詳細（StockDetailPage）
- 既存の `ChartAnalysisPanel` の下に `AnalysisAxesPanel` を追加
- 軸ごとにカード表示（ファンダメンタル・テクニカル・黒点子・チャート分析）
- 各カードは詳細内訳を展開可能

### バッチ管理
- 管理用UIに「スコアリング実行」ボタンと進捗バーを追加
- 最終実行日時を表示

## 移植対象（stock-advisor → kabu-trade）

| stock-advisor | kabu-trade 移植先 | 変更点 |
|---|---|---|
| `analyzer/technical.py` | `app/analyzer/technical.py` | pandas/ta 依存はそのまま |
| `analyzer/fundamental.py` | `app/analyzer/fundamental.py` | yfinance 依存はそのまま |
| `analyzer/kurotenko_screener.py` | `app/analyzer/kurotenko_screener.py` | そのまま移植 |
| `analyzer/scorer.py` | `app/analyzer/scorer.py` | そのまま移植 |
| `analyzer/collector.py` → | `app/external/yfinance_client.py` | 非同期対応に修正 |
| `portfolio/stock_master.py` | `app/services/scoring_service.py` に統合 | JPX銘柄マスター取得ロジック |

## 除外・対象外

- stock-advisor の Flask アプリ（`app.py`）: 不要（kabu-trade の FastAPI で代替）
- `portfolio/advisor_logic.py`（ポートフォリオアドバイス）: 今回スコープ外、将来拡張候補
- Lambda 関連（`lambda_*.py`）: 不要

## 実装順序

1. DBマイグレーション（`stock_scores` テーブル）
2. analyzer/ 移植（technical/fundamental/kurotenko/scorer）
3. yfinance_client.py + scoring_service.py
4. APScheduler 組み込み + batch API
5. scores API + analysis_axes_service
6. フロントエンド（AnalysisAxesPanel + StockListPage 更新）
7. テスト
