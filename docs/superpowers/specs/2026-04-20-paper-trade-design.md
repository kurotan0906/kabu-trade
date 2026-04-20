# ペーパートレード機能 設計書

- 作成日: 2026-04-20
- 対象機能: 仮想資金で銘柄の擬似売買ができる「ペーパートレード」ページの追加

## 1. 目的と範囲

### 目的
仮想資金で銘柄の買付・売却をシミュレーションし、保有資産の推移・実現損益・含み損益・リターン率を可視化する機能を提供する。戦略検証や投資判断の練習に用いる。

### スコープ（MVP）
- 単一の仮想口座
- 初期資金を 1 度設定し、以降は保有・取引履歴・現金残高を口座内で管理
- 約定は「現在値（デフォルト）」または「手動上書きした価格」で即時成立
- 数量は 100 株単位
- 資産推移チャート（日次・履歴再構築）
- 銘柄別パフォーマンス集計（一覧）
- **銘柄別詳細分析ページ**（選択式の指標ダッシュボード。拡張可能な Indicator Registry を採用）
- 口座のリセット機能

### 設計の主眼
本機能で**最も重要な価値は「銘柄単位の売買結果を後から豊富な指標で振り返れること」**。  
したがって以下を設計原則として明記する：

- 取引データは**個別削除不可**とし、リセット時のみ全消去する
- 将来の指標追加（手数料・配当・リスク指標・曜日別・業種別など）に耐えるよう、`paper_trades` に予約カラムを持たせる
- フロントは **Indicator Registry パターン** で指標を 1 つずつ独立モジュールとして追加できる構造にする

### 非対象（MVP 外）
- 手数料・税金の**計算反映**（予約カラムは持つが常に NULL）
- 配当再投資
- 指値・逆指値注文
- 複数仮想口座
- 日次スナップショットバッチ
- チャート再構築結果の永続キャッシュ
- バックテスト（過去日付からの開始）
- 追加入金／出金
- 指標選択状態のサーバー同期（MVP は localStorage のみ）
- 指標カードのドラッグ&ドロップ並べ替え

## 2. 既存シミュレーターとの関係

既存の `SimulatorPage.tsx` は「積立＋想定年利 → 将来評価額」の計算機で、本機能とは性質が異なる。したがって本機能は別ページ `/paper-trade` として追加し、既存シミュレーターには一切変更を加えない。

## 3. アーキテクチャ概観

### ディレクトリ配置

```
backend/app/
  models/paper_trade.py              # PaperAccount / PaperHolding / PaperTrade
  schemas/paper_trade.py
  services/paper_trade_service.py
  api/v1/paper_trade.py
  alembic/versions/008_add_paper_trade.py

frontend/src/
  pages/PaperTradePage.tsx
  pages/PaperTradeSymbolPage.tsx            # 銘柄別詳細分析ページ
  components/paper-trade/
    BuyDialog.tsx
    SellDialog.tsx
    InitCapitalDialog.tsx
    ResetConfirmDialog.tsx
    AssetHistoryChart.tsx
    PerformanceTable.tsx
    analytics/
      registry.ts                           # Indicator Registry 本体
      IndicatorSelector.tsx                 # 表示項目の選択 UI
      SummaryCard.tsx                       # 指標 A
      PositionCyclesCard.tsx                # 指標 B
      OpenPositionCard.tsx                  # 指標 C
      TimingChartCard.tsx                   # 指標 D
      BuyAndHoldCard.tsx                    # 指標 E
      EquityTimeseriesCard.tsx              # 指標 F
  services/api/paperTradeApi.ts
  types/paperTrade.ts
```

### レイヤ責務
- **API 層**: HTTP 入出力と Pydantic 検証のみ。業務ロジックを持たない。
- **Service 層**: 売買実行、P/L 計算、チャート再構築、エラー判定。DB トランザクション境界もここ。
- **Model/Repository 層**: SQLAlchemy モデルと CRUD。既存の Portfolio モジュールと完全に分離する。

### データソース
- 現在値: 既存の Portfolio enrichment（`stock_prices` の最新終値 + yfinance フォールバック）を同じ経路で利用する。
- 過去終値（チャート再構築用）: `stock_prices` テーブルを直接参照。

### ルーティング／ナビゲーション
- フロントルート:
  - `/paper-trade`                   — メインダッシュボード
  - `/paper-trade/symbols/:symbol`   — 銘柄別詳細分析
- `NavLinks.tsx` の「ポートフォリオ」の隣に「ペーパートレード」を追加
- `App.tsx` に 2 ルートを追加

## 4. データモデル

MVP は単一口座だが、将来の複数口座拡張を見越して `account_id` カラムを持たせる（アプリケーション側で 1 行制約を担保）。

### paper_accounts

| 列 | 型 | 制約 | 備考 |
|---|---|---|---|
| id | Integer | PK | |
| initial_cash | Float | NOT NULL | 初期資金。リセット時に参照 |
| cash_balance | Float | NOT NULL | 現在の仮想現金残高 |
| started_at | DateTime(tz) | NOT NULL | 運用開始日（チャート左端の既定値、リセットで更新） |
| created_at | DateTime(tz) | NOT NULL | server_default=now() |
| updated_at | DateTime(tz) | NOT NULL | onupdate=now() |

MVP では 1 行のみ存在し得る。API `GET /account` は 0 行なら `{ initialized: false }` を返す。

### paper_holdings

| 列 | 型 | 制約 | 備考 |
|---|---|---|---|
| id | Integer | PK | |
| account_id | Integer | NOT NULL, INDEX | 将来拡張用 |
| symbol | String(10) | NOT NULL, INDEX | 例: `7203.T` |
| name | String(100) | NULL | |
| quantity | Integer | NOT NULL | 常に > 0（0 になれば行削除） |
| avg_price | Float | NOT NULL | 加重平均取得単価 |
| created_at | DateTime(tz) | NOT NULL | |
| updated_at | DateTime(tz) | NOT NULL | |

UNIQUE 制約: `(account_id, symbol)`

### paper_trades

| 列 | 型 | 制約 | 備考 |
|---|---|---|---|
| id | Integer | PK | |
| account_id | Integer | NOT NULL, INDEX | |
| symbol | String(10) | NOT NULL, INDEX | |
| action | String(4) | NOT NULL | `'buy'` or `'sell'` |
| quantity | Integer | NOT NULL | 100 単位 |
| price | Float | NOT NULL | 約定単価 |
| total_amount | Float | NOT NULL | `price × quantity`（集計高速化のため保存） |
| realized_pl | Float | NULL | sell のみ記録、buy は null |
| executed_at | DateTime(tz) | NOT NULL | 約定日時（タイムゾーン保持／曜日別分析に必要） |
| note | String(255) | NULL | |
| fee | Float | NULL | **予約**: 手数料。MVP では常に NULL |
| dividend | Float | NULL | **予約**: 配当収入。MVP では常に NULL |
| created_at | DateTime(tz) | NOT NULL | |

**予約カラムの扱い**: `fee` / `dividend` は MVP の計算式（total_amount, realized_pl）には一切関与させない。将来対応時にマイグレーションで列を追加するのを避けるため、最初から NULL 可で作っておく。

### マイグレーション
- Alembic revision: `008_add_paper_trade`
- 既存の 007（`stock_scores.close_price` 追加）の次として追加
- 3 テーブルを一括作成。ダウングレードは 3 テーブルの drop

## 5. API 仕様

ベースパス: `/api/v1/paper-trade`

### GET `/account`
口座情報を返す。未初期化時は `{ "initialized": false }`。

初期化済みレスポンス:
```json
{
  "initialized": true,
  "initial_cash": 1000000,
  "cash_balance": 750000,
  "started_at": "2026-04-20T09:00:00+09:00",
  "total_value": 1050000,
  "return_pct": 5.0
}
```

### POST `/account`
初回の初期資金設定。

Request:
```json
{ "initial_cash": 1000000 }
```
- 既に `paper_accounts` に行があれば `409 Conflict`（メッセージ: `既に初期化されています。リセットしてください`）

### POST `/account/reset`
保有・取引履歴を全削除し、現金を `initial_cash` に戻し、`started_at` を now() に更新。

Request（任意）:
```json
{ "initial_cash": 2000000 }
```
- `initial_cash` を省略した場合は従来値を引き継ぐ。
- 未初期化なら `409`。

### GET `/holdings`
保有一覧。現在値・評価額・含み損益を含む。

```json
[
  {
    "id": 1,
    "symbol": "7203.T",
    "name": "トヨタ自動車",
    "quantity": 100,
    "avg_price": 2500.0,
    "current_price": 2650.0,
    "market_value": 265000.0,
    "unrealized_pl": 15000.0,
    "unrealized_pl_pct": 6.0
  }
]
```
`current_price` が取得不能な場合は `null`、評価系フィールドも `null`。

### GET `/trades?limit=100&offset=0`
取引履歴（`executed_at` の新しい順）。

```json
{
  "items": [
    {
      "id": 12,
      "symbol": "7203.T",
      "action": "sell",
      "quantity": 100,
      "price": 2650.0,
      "total_amount": 265000.0,
      "realized_pl": 15000.0,
      "executed_at": "2026-04-20T10:15:00+09:00",
      "note": null
    }
  ],
  "total": 12
}
```

### POST `/trades`
売買実行。

Request:
```json
{
  "action": "buy",
  "symbol": "7203.T",
  "quantity": 100,
  "price": 2500.0,
  "executed_at": "2026-04-20T10:00:00+09:00",
  "note": null
}
```
- `price` 省略時は現在値を自動取得。取得失敗なら 400。
- `executed_at` 省略時は now()。
- 検証エラー（数量・残高・保有不足など）はすべて 400。

レスポンスは作成された trade と更新後の account サマリ:
```json
{
  "trade": { ... },
  "account": { "cash_balance": 750000, "total_value": ... }
}
```

### GET `/summary`
ダッシュボード用の一括サマリ。

```json
{
  "initial_cash": 1000000,
  "cash_balance": 750000,
  "holdings_value": 300000,
  "total_value": 1050000,
  "unrealized_pl": 15000,
  "realized_pl": 35000,
  "return_pct": 5.0,
  "started_at": "2026-04-20T09:00:00+09:00"
}
```

### GET `/chart?from=YYYY-MM-DD&to=YYYY-MM-DD`
日次総資産推移。`from` 省略時は `started_at` の日付、`to` 省略時は今日。

```json
[
  { "date": "2026-04-20", "cash": 1000000, "holdings_value": 0, "total_value": 1000000 },
  { "date": "2026-04-21", "cash": 750000, "holdings_value": 265000, "total_value": 1015000 }
]
```

### GET `/performance`
銘柄別パフォーマンス（メインページ「銘柄別パフォーマンス」テーブル用）。

```json
[
  {
    "symbol": "7203.T",
    "name": "トヨタ自動車",
    "total_buy_amount": 250000,
    "total_sell_amount": 265000,
    "realized_pl": 15000,
    "unrealized_pl": 0,
    "total_pl": 15000,
    "return_pct": 6.0,
    "trade_count": 2,
    "win_count": 1
  }
]
```

### GET `/symbols/{symbol}/analytics?from=&to=`
銘柄別詳細分析ページ用の**全指標一括レスポンス**。  
`from` 省略時はその銘柄の最初の取引日、`to` 省略時は今日。

```json
{
  "symbol": "7203.T",
  "name": "トヨタ自動車",
  "summary": {
    "total_pl": 15000,
    "realized_pl": 15000,
    "unrealized_pl": 0,
    "return_pct": 6.0,
    "trade_count": 2,
    "buy_count": 1,
    "sell_count": 1,
    "win_count": 1,
    "loss_count": 0,
    "win_rate": 1.0,
    "avg_holding_days": 31.0,
    "best_trade_pl": 15000,
    "worst_trade_pl": 15000,
    "profit_factor": null,                 // 損失取引ゼロなら null
    "expectancy": 15000                    // 1 取引あたりの平均損益
  },
  "position_cycles": [
    {
      "entry_date": "2026-03-20",
      "exit_date": "2026-04-20",
      "entry_price": 2500,
      "exit_price": 2650,
      "quantity": 100,
      "pl": 15000,
      "return_pct": 6.0,
      "holding_days": 31
    }
  ],
  "open_position": null,                   // 保有がなければ null。保有中の例は下部参照
  "timing": {
    "price_series": [ { "date": "2026-03-20", "close": 2480 }, ... ],
    "trade_markers": [
      { "date": "2026-03-20", "action": "buy",  "price": 2500, "quantity": 100 },
      { "date": "2026-04-20", "action": "sell", "price": 2650, "quantity": 100 }
    ]
  },
  "buy_and_hold": {
    "first_buy_date": "2026-03-20",
    "first_buy_price": 2500,
    "bh_value_now": 265000,               // 最初の買い数量を今まで保有した場合の評価額
    "bh_return_pct": 6.0,
    "actual_return_pct": 6.0,
    "diff_pct": 0.0                        // 実トレード - バイ＆ホールド
  },
  "equity_timeseries": [
    { "date": "2026-03-20", "invested": 250000, "realized_pl": 0, "unrealized_pl": -2000, "total_pl": -2000 }
  ]
}
```

`open_position` はその銘柄を保有していない場合 `null`。保有中の場合の構造：

```json
{
  "quantity": 100,
  "avg_price": 2500,
  "current_price": 2650,
  "unrealized_pl": 15000,
  "unrealized_pl_pct": 6.0,
  "entry_date": "2026-03-20",
  "holding_days": 31,
  "mfe": 20000,                         // 保有期間中の最大含み益
  "mae": -5000                          // 保有期間中の最大含み損（負値）
}
```

`current_price` が取得不能な場合は `unrealized_pl` / `unrealized_pl_pct` を `null` とし、`summary.unrealized_pl` を 0 として扱う（警告フラグは MVP 外）。

### 将来拡張（MVP 外）
指標数が増えた場合は `/symbols/{symbol}/analytics?indicators=summary,timing` のように選択取得に切り替える。このパラメータを MVP でも**無視せず受け取るだけは許容**しておくと、将来の互換性が保ちやすい（任意）。

## 6. コアロジック

### 買い実行

```
1. quantity > 0 かつ 100 の倍数か検証（NG → 400）
2. price 未指定なら現在値取得（失敗 → 400）
3. total_cost = price × quantity
4. cash_balance >= total_cost か検証（NG → 400 現金不足）
5. DB トランザクション:
   a. account.cash_balance -= total_cost
   b. holding upsert:
      既存: new_avg = (avg_price × qty + price × quantity) / (qty + quantity)
            quantity += quantity, avg_price = new_avg
      新規: insert (symbol, name, quantity, avg_price=price)
   c. paper_trades insert (action='buy', realized_pl=NULL,
                           total_amount=price×quantity)
```

### 売り実行

```
1. quantity > 0 かつ 100 の倍数か検証
2. holding 存在 & holding.quantity >= quantity か検証（NG → 400）
3. price 未指定なら現在値取得
4. proceeds = price × quantity
5. realized_pl = (price - avg_price) × quantity   # 手数料・税は MVP 対象外
6. DB トランザクション:
   a. account.cash_balance += proceeds
   b. holding.quantity -= quantity
      holding.quantity == 0 ならその行を削除（avg_price は変更しない）
   c. paper_trades insert (action='sell', realized_pl=計算値,
                           total_amount=price×quantity)
```

### 含み損益・リターン率

```
unrealized_pl = Σ_holding (current_price - avg_price) × quantity
realized_pl   = Σ paper_trades.realized_pl（buy は null のため除外）
total_value   = cash_balance + Σ_holding (current_price × quantity)
return_pct    = (total_value - initial_cash) / initial_cash × 100
```
`current_price` が取得不能な銘柄は含み損益・評価額の合計から除外する（代わりに `market_value` を null にする）。

### 資産推移チャート（履歴再構築）

```
入力: from_date, to_date

前処理:
  1. 関連する trades を executed_at 昇順で全件取得
  2. 取引のあった全 symbol について stock_prices を [from_date-30d, to_date] で一括取得
     → dict[(symbol, date)] = close
     （from_date 直前の終値も使うため、余裕を見て 30 日前から）

走査:
  cash = initial_cash
  holdings = {}       # symbol -> {qty, avg_price}
  trade_idx = 0
  result = []

  for date in [from_date, ..., to_date]:
    # その日までの trades を時刻順に適用
    while trade_idx < len(trades) and trades[trade_idx].executed_at.date() <= date:
      t = trades[trade_idx]
      apply(t, cash, holdings)   # 買い/売りを適用。avg_price もここで更新
      trade_idx += 1

    # その日の評価
    holdings_value = 0
    for symbol, h in holdings.items():
      close = lookup_close(symbol, date)     # なければ date より前の最新終値で前方補完
      if close is None:
        # 一度も終値がない銘柄（通常ありえないが念のため avg_price で代替）
        close = h.avg_price
      holdings_value += h.qty × close

    result.append({ date, cash, holdings_value, total_value: cash + holdings_value })

  return result
```
計算量は O(trades + days × holdings)。1 年・50 銘柄・数百件程度の取引なら 1 秒未満で完了する想定。

**前方補完**: 休場日や株価データ欠損の場合は、その date 以前で最新の終値を使う。該当銘柄の終値が一切無い場合は `avg_price` を代替値として使用する（通常は発生しないが、安全策）。

### 銘柄別パフォーマンス（一覧）

```
symbol ごとに paper_trades を集計:
  total_buy_amount  = Σ buy.total_amount
  total_sell_amount = Σ sell.total_amount
  realized_pl       = Σ sell.realized_pl
  unrealized_pl     = 保有中なら (current_price - avg_price) × quantity、未保有なら 0
                      current_price 取得失敗時は 0（0 として扱う旨は UI で注釈）
  total_pl          = realized_pl + unrealized_pl
  return_pct        = total_pl / total_buy_amount × 100（0 除算時は null）
  trade_count       = buy + sell 件数
  win_count         = realized_pl > 0 の sell 件数
```

### 銘柄別詳細分析（Analytics）の計算

#### ポジションサイクル（FIFO 対応）
現金管理は加重平均方式のままとし、**分析時のみ** 取引履歴を再走査して FIFO でロットを対応させる：

```
lots = deque()   # { date, price_per_share, quantity_remaining }

for trade in paper_trades.order_by(executed_at):
  if trade.action == 'buy':
    lots.append({ date: trade.executed_at, price: trade.price, qty: trade.quantity })
  else:  # sell
    remaining = trade.quantity
    while remaining > 0 and lots:
      lot = lots[0]
      used = min(lot.qty, remaining)
      cycle = {
        entry_date:     lot.date,
        exit_date:      trade.executed_at,
        entry_price:    lot.price,
        exit_price:     trade.price,
        quantity:       used,
        pl:             (trade.price - lot.price) × used,
        return_pct:     (trade.price - lot.price) / lot.price × 100,
        holding_days:   (trade.executed_at - lot.date).days,
      }
      position_cycles.append(cycle)
      lot.qty -= used
      remaining -= used
      if lot.qty == 0: lots.popleft()
  # 残った lots は open_position の素材

open_position.entry_date = 残 lots の最古日
open_position.quantity   = Σ 残 lots の quantity
open_position.avg_price  = Σ(price × qty) / Σ qty
```

この FIFO 計算は DB に保存せず、API リクエストのたびに再構築する（追加テーブル不要）。  
注意：現金ベースの `realized_pl`（sell 時点の加重平均差で計算）と、FIFO ベースの `pl` の**合計は一致する**（単に個々の cycle への按分方法が違うだけ）。

#### サマリ指標
```
buy_count  = count(action='buy')
sell_count = count(action='sell')
trade_count = buy_count + sell_count
win_count  = count(cycle.pl > 0)
loss_count = count(cycle.pl < 0)
win_rate   = win_count / (win_count + loss_count)  # 引き分け(0)は除外。分母0なら null
avg_holding_days = mean(cycle.holding_days)
best_trade_pl    = max(cycle.pl)
worst_trade_pl   = min(cycle.pl)
total_gains  = Σ cycle.pl where pl > 0
total_losses = -Σ cycle.pl where pl < 0
profit_factor = total_gains / total_losses      # total_losses == 0 なら null
expectancy    = mean(cycle.pl)
realized_pl   = Σ cycle.pl
unrealized_pl = open_position にあれば (current - avg) × qty、無ければ 0
total_pl      = realized_pl + unrealized_pl
return_pct    = total_pl / total_buy_amount × 100
```

#### 現在保有の健康度（MFE / MAE）
```
open_position が存在する場合:
  entry_date = FIFO 残 lots の最古日
  avg_price  = FIFO 残 lots の加重平均

  date ∈ [entry_date, today] について stock_prices.close を取得（前方補完）
  mfe = max((close - avg_price) × quantity) for close >= avg_price, else 0
  mae = min((close - avg_price) × quantity) for close <= avg_price, else 0
```
**簡略化**: MVP では open_position の `avg_price` と `quantity` を現時点スナップショットとして扱う（保有数量が期間中に増減したケースでも、現時点の avg_price 起点で MFE/MAE を出す）。厳密な履歴再走査による MFE/MAE は将来拡張。

#### タイミング可視化（D）
- `price_series`: `stock_prices` から [from, to] の日次終値を取得
- `trade_markers`: 期間中の `paper_trades` をそのまま返す（action / price / quantity / date）

#### バイ＆ホールド比較（E）
```
first_buy = 最初の buy 取引
first_buy_date  = first_buy.executed_at
first_buy_price = first_buy.price
first_buy_qty   = first_buy.quantity
bh_value_now    = first_buy_qty × current_price
bh_return_pct   = (current_price - first_buy_price) / first_buy_price × 100
actual_return_pct = summary.return_pct
diff_pct        = actual_return_pct - bh_return_pct
```
「最初に買った数量をそのまま持ち続けた」という基準でシンプル比較。  
**簡略化**: 複数回の買いを含むケースでも「最初の買いの数量」のみを比較対象とする（MVP）。より厳密な「累計投下資本ベース」のバイ＆ホールド比較は将来拡張。

#### 時系列チャート（F）
```
for date in [from, to]:
  date までの trades を適用 → 累計投下資本 invested, 実現損益累計 realized_pl
  open_position があれば close 価格から unrealized_pl を計算
  total_pl = realized_pl + unrealized_pl
```
資産推移チャート（口座全体）の「銘柄限定版」。ロジックは共通化の対象候補だが MVP は別実装で可。

## 7. フロントエンド

### PaperTradePage 構成

```
PageHeader: ペーパートレード / 仮想資金で売買を試す
  actions: [買い付け] [リセット]

未初期化時:
  EmptyState「仮想口座を作成しましょう」 + [初期資金を設定して開始]
    → InitCapitalDialog

初期化済み:
  [Stat x 6]  総資産 / 現金残高 / 保有評価額 / 含み損益 / 実現損益 / リターン%
  [Card] 資産推移チャート AssetHistoryChart (Recharts 折れ線)
         期間切替: 1M / 3M / 6M / 1Y / ALL
  [Card] 保有銘柄 (N) テーブル
         列: 銘柄・数量・取得単価・現在値・評価額・含み損益(%)・[売却]
  [Card] 銘柄別パフォーマンス PerformanceTable
         列: 銘柄・取引回数・勝率・実現損益・含み損益・合計損益・リターン%
  [Card] 取引履歴
         列: 日時・銘柄・区分・数量・単価・約定額・実現損益・メモ
         ページネーション 100 件単位
```

### ダイアログ

| Dialog | 入力／挙動 |
|---|---|
| InitCapitalDialog | 初期資金（デフォルト 1,000,000 円）→ POST `/account` |
| BuyDialog | 銘柄検索（既存 SymbolSearch 流用）→ 数量(100株単位) → 約定価格（現在値プリセット・編集可）→ 概算コスト表示。残高不足で赤帯警告 |
| SellDialog | 保有銘柄選択（保有テーブルの「売却」から起動、または銘柄選択）→ 数量 → 約定価格 → 想定実現損益表示 |
| ResetConfirmDialog | 警告文 + 新しい初期資金（任意変更） → POST `/account/reset` |

### 既存コンポーネント流用

Card / CardHeader / CardBody / PageHeader / Stat / Badge / Table / Dialog / Field / NumberInput / Button / EmptyState。銘柄検索は Portfolio の `HoldingDialog` で使っているパターンを再利用する（現時点で共通化まではしない）。

チャートは用途が異なるため `FutureValueChart` を流用せず、新規 `AssetHistoryChart` を Recharts で作る。

### 銘柄別詳細分析ページ（PaperTradeSymbolPage）

#### ページ構成
```
PageHeader: 7203.T トヨタ自動車 / [← 戻る]
  actions: [📊 表示項目を選択] [期間: 1M/3M/6M/1Y/ALL]

[選択された Indicator を順番に Card で縦並び表示]
  SummaryCard             # A
  PositionCyclesCard      # B
  OpenPositionCard        # C
  TimingChartCard         # D
  BuyAndHoldCard          # E
  EquityTimeseriesCard    # F
```

#### Indicator Registry（拡張性の核）
`frontend/src/components/paper-trade/analytics/registry.ts`:

```ts
export interface IndicatorDef<K extends keyof AnalyticsResponse = keyof AnalyticsResponse> {
  id: K;                                              // 'summary' | 'position_cycles' | ...
  label: string;                                      // 表示名
  description?: string;                               // 選択 UI のツールチップ
  category: 'basic' | 'advanced';                     // 将来の絞り込み用
  defaultEnabled: boolean;
  component: React.FC<{ symbol: string; data: AnalyticsResponse }>;
}

export const INDICATOR_REGISTRY: IndicatorDef[] = [
  { id: 'summary',           label: 'サマリ指標',          category: 'basic',    defaultEnabled: true,  component: SummaryCard },
  { id: 'position_cycles',   label: 'ポジションサイクル',  category: 'basic',    defaultEnabled: true,  component: PositionCyclesCard },
  { id: 'open_position',     label: '現在保有の健康度',    category: 'basic',    defaultEnabled: true,  component: OpenPositionCard },
  { id: 'timing',            label: 'タイミング可視化',    category: 'basic',    defaultEnabled: true,  component: TimingChartCard },
  { id: 'buy_and_hold',      label: 'バイ＆ホールド比較', category: 'advanced', defaultEnabled: false, component: BuyAndHoldCard },
  { id: 'equity_timeseries', label: '投下資本/損益推移',  category: 'advanced', defaultEnabled: false, component: EquityTimeseriesCard },
];
```

**新しい指標を追加する手順**（将来作業の明確化）:
1. バックエンド `analytics` 計算関数にフィールドを追加し、レスポンス型を拡張
2. 新 `XxxCard.tsx` を `analytics/` 以下に追加（props は `{ symbol, data }` 固定）
3. `INDICATOR_REGISTRY` に IndicatorDef を 1 行追加
4. レジストリ順序 = 表示順序（任意で再並び替え）

これで既存指標のコード・UI に手を入れずに追加できる。

#### 選択 UI（IndicatorSelector）
- 「📊 表示項目を選択」ボタン → Popover でチェックボックスリスト
- `localStorage['paperTrade.symbolAnalytics.visibleIds']` に string[] として保存
- 初期値は `defaultEnabled: true` の指標群
- `category === 'advanced'` は折りたたみセクションに分離表示

#### API クライアント拡張
`paperTradeApi.getSymbolAnalytics(symbol, from?, to?)` を追加。

### API クライアント

`frontend/src/services/api/paperTradeApi.ts` に以下を定義:
- `getAccount`
- `initAccount`
- `resetAccount`
- `listHoldings`
- `listTrades`
- `createTrade`
- `getSummary`
- `getChart`
- `getPerformance`
- `getSymbolAnalytics`

型は `frontend/src/types/paperTrade.ts`。`AnalyticsResponse` を API レスポンスと完全対応させ、指標ごとの型は `SummaryMetrics` / `PositionCycle` / `OpenPosition` / `TimingData` / `BuyAndHold` / `EquityTimeseriesPoint` で分解する。

## 8. エラー処理

| ケース | HTTP | メッセージ |
|---|---|---|
| 数量 <= 0 または 100 の倍数でない | 400 | 数量は100株単位で指定してください |
| 未初期化で売買 | 409 | 仮想口座が初期化されていません |
| 初期化済みに POST /account | 409 | 既に初期化されています。リセットしてください |
| 買い・残高不足 | 400 | 現金残高が不足しています（必要: ¥X / 残高: ¥Y） |
| 売り・保有なし | 400 | この銘柄は保有していません |
| 売り・数量不足 | 400 | 保有数量を超えています（保有: X株） |
| 現在値取得失敗 | 400 | 現在値を取得できませんでした。価格を手動で入力してください |

フロント側はダイアログ内で赤帯表示する（既存 `HoldingDialog` のパターンに準拠）。

## 9. テスト

### バックエンド（pytest）

`backend/tests/test_paper_trade_service.py`:
- 初期化後の現金残高 == initial_cash
- 買い: 残高減・保有作成・取引記録
- 買い増し: 加重平均単価の再計算
- 売り（全数量）: 保有行削除・現金増・realized_pl 計算
- 売り（一部）: 保有残・avg_price は不変
- 売り > 保有数量 → 400
- 買い・残高不足 → 400
- 数量 100 株未満 / 端数 → 400
- 未初期化で売買 → 409
- リセット: 全削除 + started_at 更新 + 新 initial_cash 反映
- サマリ: return_pct / realized_pl / unrealized_pl の集計
- チャート再構築:
  - 休場日の前方補完
  - 複数銘柄混在
  - from_date より前の取引の反映
- 銘柄別パフォーマンス:
  - win_count が sell.realized_pl > 0 のみをカウント
  - 保有中銘柄の含み益が total_pl に含まれる
  - total_buy_amount == 0 の symbol で return_pct が null
- 銘柄別詳細分析（analytics）:
  - FIFO ポジションサイクルの分割（1 回の売りが複数 lot を消費するケース）
  - 保有継続中の open_position が残る（売り切っていない状態）
  - profit_factor の分母 0（損失なし）で null を返す
  - win_rate の分母 0（勝敗ゼロ）で null を返す
  - MFE/MAE の前方補完
  - バイ＆ホールド比較の diff_pct
  - FIFO cycles の合計 pl が集計の realized_pl と一致する（数学的整合性）

`backend/tests/test_paper_trade_api.py`:
- 主要エンドポイントのハッピーパス
- 400 / 409 エラーレスポンスの検証
- `/symbols/{symbol}/analytics` のハッピーパスと未保有銘柄で 404 を返す挙動

### フロントエンド

MVP では型チェック（tsc）と既存 UI コンポーネントの流用のみ。自動テストは追加せず、手動テストのシナリオ（golden path）は実装計画側で列挙する。

## 10. オープン事項（実装計画フェーズで詰める）

- 現在値取得の共通化: Portfolio の enrichment を service 層から直接呼び出せるか、薄いヘルパーを切り出すか
- `/chart` のデフォルト最大期間（無制限だと遅くなる可能性）。MVP は started_at からの全期間をそのまま返す
- `total_amount` をカラム保存したが、select 時の再計算でも十分という判断もあり得る。保存しておくと集計 SQL が簡潔になる
- Analytics エンドポイントのキャッシュ戦略（必要になったら Redis / in-memory）
- 未保有かつ取引履歴ゼロの symbol で `/symbols/{symbol}/analytics` にアクセスされた時の返し方（404 か 空の analytics か）
- 将来の指標候補: シャープレシオ、ソルティノレシオ、ドローダウン曲線、勝ち連続記録、曜日別・月別ヒートマップ、業種別集計、タグ/メモ検索、エクイティカーブ回帰分析
