# TradingView MCP連携 設計ドキュメント

**作成日:** 2026-04-05  
**ステータス:** 承認済み  
**フェーズ:** Phase A（TradingView MCP連携）

---

## 1. 概要

Claude Code から TradingView を MCP 経由で操作し、チャートのスクリーンショットを取得・分析して、結果を kabu-trade アプリに保存・表示する仕組みを構築する。

### ゴール
- Claude Code から日本株のチャートを自動操作（銘柄・時間足・チャートタイプ切替）
- Claude Vision でチャート画像を分析し、構造化レポートを生成
- 分析結果を kabu-trade バックエンドに保存し、フロントエンドで表示
- 手動トリガーと定期自動実行の両方に対応

### スコープ外
- アルゴリズムトレード・自動発注（Phase B として別途設計）
- 海外株・暗号資産（Phase A は日本株のみ、拡張前提の設計）

---

## 2. アーキテクチャ

```
[Claude Code]
     │
     ├── MCP: tradingview-mcp (Playwright)
     │         ├── chart_set_symbol("7203")
     │         ├── chart_set_timeframe("1D")
     │         ├── chart_set_type("Candles")
     │         └── chart_take_screenshot() → base64画像
     │
     ├── Claude Vision で画像分析
     │         └── 構造化レポート生成（トレンド/シグナル/推奨）
     │
     └── HTTP POST → kabu-trade Backend
               └── POST /api/v1/chart-analysis
                         ├── DB保存（chart_analyses テーブル）
                         └── Frontend が GET で取得・表示
```

---

## 3. MCPサーバー設定

**使用パッケージ:** `ali-rajabpour/tradingview-mcp`（Python + Playwright）

**設定ファイル** (`.claude/settings.local.json`):
```json
{
  "mcpServers": {
    "tradingview": {
      "command": "uvx",
      "args": ["tradingview-mcp"],
      "env": {
        "TV_USERNAME": "your_tradingview_email",
        "TV_PASSWORD": "your_tradingview_password"
      }
    }
  }
}
```

**利用するMCPツール:**

| ツール | 引数 | 説明 |
|--------|------|------|
| `chart_set_symbol` | `symbol: str` | 銘柄切替（例: "7203"） |
| `chart_set_timeframe` | `timeframe: str` | 時間足変更（"1D", "1W", "4H"等） |
| `chart_set_type` | `chart_type: str` | チャートタイプ（"Candles"等） |
| `chart_take_screenshot` | なし | スクリーンショット取得（base64） |

---

## 4. バックエンド設計

### 4.1 データモデル

**新規ファイル:** `backend/app/models/chart_analysis.py`

```python
class ChartAnalysis(Base):
    __tablename__ = "chart_analyses"

    id: Mapped[int] = mapped_column(primary_key=True)
    symbol: Mapped[str] = mapped_column(String(10), nullable=False, index=True)
    timeframe: Mapped[str] = mapped_column(String(10), nullable=False)
    screenshot_path: Mapped[str | None] = mapped_column(String(500))
    trend: Mapped[str] = mapped_column(String(20))        # bullish / bearish / neutral
    signals: Mapped[dict] = mapped_column(JSON)           # {"rsi": "oversold", ...}
    summary: Mapped[str] = mapped_column(Text)
    recommendation: Mapped[str] = mapped_column(String(10))  # buy / sell / hold
    created_at: Mapped[datetime] = mapped_column(default=func.now())
```

### 4.2 APIエンドポイント

**新規ファイル:** `backend/app/api/v1/chart_analysis.py`

| メソッド | パス | 説明 |
|---------|------|------|
| `POST` | `/api/v1/chart-analysis` | Claude Code から分析結果を保存 |
| `GET` | `/api/v1/chart-analysis/{symbol}` | 銘柄の最新分析を取得 |
| `GET` | `/api/v1/chart-analysis/{symbol}/history` | 分析履歴一覧（最新20件） |

**POST リクエストボディ:**
```json
{
  "symbol": "7203",
  "timeframe": "1D",
  "screenshot_path": "/screenshots/7203_1D_20260405.png",
  "trend": "bullish",
  "signals": {
    "rsi": "oversold_recovery",
    "ma": "golden_cross_approaching",
    "macd": "bullish_divergence"
  },
  "summary": "日足チャートでは...",
  "recommendation": "buy"
}
```

### 4.3 マイグレーション

**新規ファイル:** `backend/alembic/versions/002_add_chart_analyses.py`

既存の `evaluations` テーブルとは独立した新テーブル。既存機能への影響なし。

---

## 5. フロントエンド設計

### 5.1 新規ファイル

| ファイル | 役割 |
|---------|------|
| `frontend/src/types/chartAnalysis.ts` | 型定義 |
| `frontend/src/services/api/chartAnalysisApi.ts` | APIクライアント |
| `frontend/src/components/stock/ChartAnalysisPanel.tsx` | 表示コンポーネント |

### 5.2 ChartAnalysisPanel UI

```
┌─────────────────────────────────────┐
│ AI チャート分析                      │
│ 最終更新: 2026-04-05 14:30          │
├──────────┬──────────────────────────┤
│ トレンド  │ 強気 (Bullish)           │
│ 推奨     │ 買い (Buy)               │
├──────────┴──────────────────────────┤
│ シグナル                             │
│  • RSI: 売られすぎゾーンから回復中   │
│  • MA: ゴールデンクロス直前          │
├─────────────────────────────────────┤
│ Claudeのサマリー                     │
│ 日足チャートでは...（テキスト）      │
├─────────────────────────────────────┤
│ [チャート分析を実行] [履歴を見る]    │
└─────────────────────────────────────┘
```

### 5.3 StockDetailPage への統合

既存の `EvaluationResult` コンポーネントの下に `ChartAnalysisPanel` を配置。
「チャート分析を実行」ボタンは既存の「評価を実行」ボタンと並列表示。

---

## 6. 自動化

### 手動トリガー（Phase 1）
Claude Code に自然言語で話しかけるだけ:
```
「7203の日足チャートを分析してkabu-tradeに保存して」
```

### 定期自動実行（Phase 2）
- **監視銘柄リスト:** `watchlist` テーブル（または設定ファイル）
- **スケジューラ:** macOS `launchd` または Claude Code `/schedule` スキル
- **実行タイミング:** 平日 9:00〜15:30、30分ごとを想定

---

## 7. 実装フェーズ

| フェーズ | 内容 | 優先度 |
|---------|------|--------|
| **Phase 1** | MCPサーバーセットアップ + 手動チャート操作・分析確認 | 高 |
| **Phase 2** | バックエンドAPI + DBマイグレーション追加 | 高 |
| **Phase 3** | フロントエンドUI（ChartAnalysisPanel） | 中 |
| **Phase 4** | 定期自動実行の設定 | 低 |

---

## 8. AWSコスト影響

- Playwright MCPサーバーはローカルMac上で動作するため**AWS追加コストなし**
- スクリーンショット（S3保存）・分析結果（RDS）は**個人利用の無料枠内に収まる**
- 個人利用構成（EC2 t3.micro + RDS t3.micro）で引き続き **$0/月** を維持可能

---

## 9. 拡張性

- **市場拡張:** `symbol` フィールドに市場コードを追加することで海外株・暗号資産に対応可能
- **Phase B（アルゴトレード）:** 本設計の分析結果（`recommendation` フィールド）をシグナルソースとして利用可能
- **プロバイダ差し替え:** `ali-rajabpour/tradingview-mcp` を別MCPサーバーに差し替えても、バックエンドAPIインターフェースは変わらない
