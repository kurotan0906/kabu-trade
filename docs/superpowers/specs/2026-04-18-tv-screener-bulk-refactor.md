# TradingView Screener 一括取得への置き換え設計

**Date:** 2026-04-18
**Scope:** バッチスコアリングのデータソースを yfinance ループから TradingView Screener の一括取得へ切り替える。yfinance は個別銘柄データ専用に降格する。
**Status:** Draft v2（検証結果反映済み）

## 0. 事前検証結果（2026-04-18 実施）

- ✅ **TV Screener 必要カラム全て利用可能**: `SMA25`, `SMA75`, `RSI`, `MACD.macd`, `MACD.signal`（現行 `technical.py` が使う指標と一致）
- ✅ **`tradingview-screener` v3.1.0 インストール・実行確認**: `market=japan` + `type=stock` で 3,892 銘柄、1.29 秒で取得
- ⚠️ **MACD「直近クロス検出」はスナップショット再現不可**: 現行 `_calc_macd_state` は過去3本の MACD/Signal を見て recent_cross ボーナスを付与。TV Screener は断面値のみ。→ **§7.2 で新ロジック定義**
- ⚠️ **`bulk_tv_signals.py` は別サブシステム**: `tradingview_signals` テーブルへのデータ供給で、UI（`LatestSignalsCard`, `StockRankingPage`）と API (`/api/v1/tradingview-signals`) が消費中。**本 refactor の削除対象から除外**

## 1. 背景・目的

### 現状の課題
- `run_batch_scoring_sync` は JPX 全銘柄（~4,000）を `yfinance` で 1 銘柄ずつ取得してスコアリングしている。`MAX_WORKERS=1` + リトライ + throttle のため**実行時間が長い**（数十分）。
- `tradingview-ta` は個別銘柄指標の上書き用で、これも per-symbol。
- `curl-cffi` による User-Agent 詐称は yfinance の 429 回避策だが、レート制限や IP ブロックは恒常的なリスク。

### 目標
- **一括取得系は TradingView Screener API に集約**（1 リクエストで日本市場全銘柄の財務・テクニカルを取得）
- **個別データ系は yfinance に残す**（時系列・財務諸表・黒点子評価など、screener で取れない情報）
- **既存のスコアリング計算ロジックは変更しない**（`calc_fundamental_score`, `calc_technical_score`, `build_stock_result` は互換維持）
- バッチ実行時間を **数十分 → 数十秒**に短縮

### 非目標
- スコアリング計算式自体の変更（`scorer.py`, `fundamental.py`, `technical.py` は触らない）
- 黒転スクリーナー（`kurotenko_screener.evaluate_candidate`）のロジック変更
- 個別銘柄詳細ページ / チャートのデータソース変更

## 2. 現行アーキテクチャ

```
[APScheduler/Cloud Scheduler]
   ↓
run_batch_scoring_sync
   ↓ (for each symbol, ~4000)
   ├─ yfinance_client.fetch_stock_data       (info + history)
   ├─ tradingview_ta_client.fetch_stock_data_tv  (info 上書き)
   ├─ merge_info (hybrid モード)
   ├─ calc_fundamental_score(info)
   ├─ calc_technical_score(history)
   ├─ evaluate_candidate(symbol)  (Redis 30d cache 経由で yfinance 財務 API)
   └─ build_stock_result → StockScore 保存
```

**ネック**: ループの内側で 3 種類の外部 API を叩いている。

## 3. 新アーキテクチャ

```
[APScheduler/Cloud Scheduler]
   ↓
run_batch_scoring_sync (new)
   ↓
   ┌─ (1) 一括取得 [single API call]
   │    tv_screener_client.fetch_japan_market_snapshot()
   │      ↓
   │    Dict[symbol -> row]  (~4000 rows, fundamentals + technical + sector)
   │
   ├─ (2) JPX マスタとのマージ
   │    load_jpx_symbols() で symbol/name/market を取得
   │    TV スナップショットと symbol で突合
   │
   ├─ (3) 各銘柄をスコアリング [CPU のみ / IO なし]
   │    for each (jpx_row, tv_row):
   │      info = adapter.tv_row_to_info(tv_row)   # yfinance info 互換 dict へ変換
   │      fundamental = calc_fundamental_score(info)      # 変更なし
   │      technical   = calc_technical_score_from_tv(tv_row)  # 新規、TV 指標から直接
   │      kurotenko   = _get_kurotenko_cached(symbol)
   │                    ?? evaluate_candidate(symbol)   # cache miss 時のみ yfinance
   │      result = build_stock_result(...)
   │      session.add(StockScore(**result))
   │
   └─ (4) commit + Redis status 更新 + checkpoint
```

**改善点**:
- 外部 API 呼び出しが **1 回のスナップショット + 黒点子 cache miss 分のみ**
- ThreadPoolExecutor 不要（IO が消えて CPU だけになる）
- checkpoint/retry も単純化（もしくは不要）

## 4. データソース分離ポリシー

| 用途 | ソース | 理由 |
|---|---|---|
| **一括ランキング用スコアリング** | TV Screener | 一発取得で高速 |
| **一括スクリーニング**（黒転候補絞込 等） | TV Screener | 同上 |
| **黒点子評価**（前期赤字判定等） | yfinance 財務諸表 | TV では前期単独値が取れない |
| **個別銘柄 OHLCV 履歴**（チャート・テクニカル詳細画面） | yfinance `ticker.history` | TV Screener は断面データのみ |
| **個別銘柄 info**（詳細画面の PER/PBR 等） | yfinance `ticker.info` | 現状のまま（将来 TV へ移行検討可） |
| **ChartAnalysisService の指標計算** | yfinance + pandas_ta | 現状のまま |

## 5. 新規/変更モジュール

### 5.1 新規: `backend/app/external/tv_screener_client.py`

```python
"""TradingView Screener 一括取得クライアント。

tradingview-screener (pip) パッケージ経由で market=japan の断面データを一括取得する。
MCP と同一の HTTP API を叩くため、MCP で検証したフィルタ/カラムがそのまま使える。
"""

TV_SCREENER_COLUMNS = [
    # メタ
    "name", "description", "sector", "exchange", "currency",
    # 価格・出来高
    "close", "volume", "market_cap_basic", "average_volume_10d_calc",
    # ファンダメンタル（yfinance info 互換マッピング元）
    "price_earnings_ttm",           # -> trailingPE
    "price_book_ratio",             # -> priceToBook (fallback: price_book_fq)
    "price_book_fq",
    "return_on_equity",             # -> returnOnEquity (% 単位)
    "dividend_yield_recent",        # -> dividendYield (% 単位)
    "total_revenue_yoy_growth_fy",  # -> revenueGrowth (% 単位)
    # テクニカル（現行 technical.py の指標と一致させる）
    "RSI",
    "MACD.macd", "MACD.signal",
    "SMA25", "SMA75",              # score_ma の配列判定で利用
    # TV 総合レーティング（メタ用途・将来のシグナル抽出用）
    "Recommend.All",
]

def fetch_japan_market_snapshot(
    min_market_cap: int = 0,
    min_avg_volume: int = 0,
) -> dict[str, dict]:
    """日本市場全銘柄の断面データを 1 回のクエリで取得する。

    Returns:
        {"7203.T": {...row...}, "6758.T": {...}, ...}
        TSE 以外（NAG, FSE, SSE）は除外。symbol は `.T` サフィックス付きで正規化する。
    """
```

**キー設計原則**:
- **`symbol` キーは `.T` 付きに正規化**（既存 DB / JPX マスタと整合）
- **TSE 以外は除外**（同じコードが NAG にも存在する問題の回避）
- **レスポンスは dict[symbol -> row]** でルックアップ O(1)

### 5.2 新規: `backend/app/external/tv_screener_adapter.py`

```python
"""TV Screener の行データを既存スコアリング関数と互換な形式へ変換する。"""

def tv_row_to_info(row: dict) -> dict:
    """TV row → yfinance ticker.info 互換 dict。

    calc_fundamental_score が期待するキー (trailingPE, priceToBook, returnOnEquity,
    dividendYield, revenueGrowth) に合わせて変換。% 単位は小数に直す。
    """

def tv_row_to_technical_features(row: dict) -> dict:
    """TV row → 技術スコア計算用の dict（close, RSI, MACD, SMA, EMA, BB）。"""
```

### 5.3 新規: `backend/app/analyzer/technical_from_tv.py`

```python
"""TV の指標値から技術スコアを計算する（履歴不要版）。

現行 calc_technical_score は pd.DataFrame (OHLCV 1年分) を受け取って pandas_ta で
計算し直す。新関数は TV から既計算の指標値を受け取り、スコアリング部分だけ流用する。
出力フォーマットは calc_technical_score と同一:
    {"technical_score": float, "ma_score": float, "rsi_score": float, "macd_score": float}
"""

def calc_technical_score_from_tv(features: dict) -> dict:
    ...
```

判定ロジックは既存 `technical.py` のスコアリング関数 (`score_rsi`, `score_macd`, `score_ma_alignment`) を流用。移動平均配列は `close > SMA20 > SMA50 > SMA200` のような条件式で判定する。

### 5.4 改修: `backend/app/services/scoring_service.py`

- `_fetch_merged_data` / `_score_symbol_with_retry` を削除または私有化。
- 新しい `run_batch_scoring_sync` を以下のフローに差し替え:
  1. `snapshot = tv_screener_client.fetch_japan_market_snapshot(...)`
  2. `jpx = load_jpx_symbols()`
  3. 各 jpx エントリに対して snapshot から行を引く、無ければ data_quality=`missing_tv`
  4. スコア計算 → StockScore 保存
  5. 黒点子評価は cache hit 最優先、miss のみ `evaluate_candidate` を別スレッドで非同期実行（並列度は少な目）
- `SCORING_DATA_SOURCE` / `SCORING_MAX_WORKERS` / `SCORING_YFINANCE_MIN_INTERVAL_SEC` 設定は段階的に整理（Phase 3 で削除）

### 5.5 既存の使い分け

| モジュール | 扱い |
|---|---|
| `yfinance_client.fetch_stock_data` | **存続**（詳細画面・ChartAnalysis で継続利用） |
| `yfinance_client.load_jpx_symbols` | **存続**（銘柄マスタ・市場区分の唯一の出典） |
| `tradingview_ta_client.fetch_stock_data_tv` | **非推奨化**（Phase 3 で削除。新規 screener で代替） |
| `kurotenko_screener.evaluate_candidate` | **存続**（yfinance 財務諸表依存） |

## 6. 銘柄コード / 市場の扱い

| ソース | フォーマット | 例 |
|---|---|---|
| JPX マスタ / DB | `{code}.T` | `7203.T` |
| yfinance | 同上 | `7203.T` |
| TV API | `{exchange}:{code}` | `TSE:7203` |

**ルール**:
- DB のキーは `7203.T` のまま（マイグレーション不要）
- `tv_screener_client` 内で `symbol_to_tv` / `tv_to_symbol` のコンバータを持つ
- TV レスポンスの `ticker` が `TSE:*` 以外（`NAG:*`, `FSE:*`, `SSE:*`）の場合は破棄
- 既存 `tradingview_ta_client.symbol_to_tv` ロジックを共通モジュールに切り出して再利用

## 7. スコアリング互換性の担保

### 7.1 ファンダメンタル側

| yfinance `info` key | TV column | 単位変換 |
|---|---|---|
| `trailingPE` | `price_earnings_ttm` | なし |
| `priceToBook` | `price_book_ratio` (FY)、`price_book_fq` fallback | なし |
| `returnOnEquity` | `return_on_equity` | **% → 小数**（`0.15 = 15%`） |
| `dividendYield` | `dividend_yield_recent` | **% → 小数** |
| `revenueGrowth` | `total_revenue_yoy_growth_fy` | **% → 小数** |

`calc_fundamental_score(info)` は無変更。アダプターが単位変換を担う。

### 7.2 テクニカル側

`calc_technical_score(history)` は履歴 DataFrame を前提（`ta` ライブラリで MA/RSI/MACD を再計算）。TV 版は既計算の指標値を使う別関数を追加する（既存を温存）。

**現行ロジックの写像（`backend/app/analyzer/technical.py` 実装準拠）**:

| サブスコア | 現行実装 | TV 版新実装 | 再現性 |
|---|---|---|---|
| `ma_score` | `close`, rolling SMA25, SMA75 の位置関係（完全陽転 +20 / 陽転 +12 / 中立 +6 / 完全陰転 0） | 同条件を TV `close` / `SMA25` / `SMA75` で判定 | **完全再現** |
| `rsi_score` | `ta.RSIIndicator(14)` 終値時点のレンジ判定 | TV `RSI` のレンジ判定 | **±1〜2 pt の微差**（ライブラリ実装差） |
| `macd_score` | `macd > signal` 基本点 + **直近3本でゴールデンクロス/デッドクロス検出時にボーナス** | `MACD.macd > MACD.signal` の 2 値判定のみに簡略化 | **ボーナス分損失** |

**MACD クロスボーナスの扱い（重要な設計判断）**:
- TV Screener は断面値のみを返すため、`_calc_macd_state` が参照している過去3本の MACD/Signal 値にアクセスできない。
- 選択肢:
  - **A. 二値化（採用案）**: `macd_score` を `macd > signal ? +1 : -1` のみにする。現行の「直近クロス時 +2 ボーナス」は削除。スコア全体（technical = 0〜50 pt）への寄与が小さい（±1 pt）ため実用上の影響は限定的。
  - B. TV で過去N本のクロス有無を別フィールド（`MACD.hist` の連続符号反転など）で推定 → 実装複雑度に対して精度改善が小さく不採用。
  - C. ターゲット銘柄だけ yfinance で history 再取得 → IO コスト復活・設計目的（高速化）に反する。
- **既存スコアとの差分監視**: Phase 1 の並行稼働中、top100 銘柄で technical_score の差分を計測。平均乖離 ±3 pt 以内を許容ライン。

**整合性検証**: 現行 `ta` 計算値と TV 値の差分を 100 銘柄サンプル比較。差が ±5% 以内であれば同一スコア帯（rating）に収束することを確認する（テスト項目）。

### 7.3 黒点子スコア

- 完全に既存フロー踏襲（Redis 30d cache → miss なら yfinance 財務 API）
- キャッシュキー `kurotenko:v1:*` のままバージョンバンプ不要

## 8. エラーハンドリング / フォールバック

| 障害 | 挙動 |
|---|---|
| TV Screener 応答失敗 / タイムアウト | バッチ全体失敗とせず、**yfinance にフォールバック**するオプションを feature flag で残す（Phase 2 まで） |
| JPX 銘柄が TV snapshot に存在しない（ETF・REIT・新規上場） | `data_quality = "missing_tv"` で保存。スコア計算はスキップ |
| TV 個別フィールドが null（例: Sony の PER） | 現行 `calc_fundamental_score` が None を中立値 5 に正規化するので問題なし |
| 黒点子 evaluate_candidate (yfinance) 失敗 | 現行どおり kurotenko=None で保存（スコア計算には影響せず） |

## 9. キャッシュ戦略

| 対象 | 現行 | 新 |
|---|---|---|
| TV Screener snapshot | - | **短期 Redis cache 1h**（`/api/v1/scores` のリアルタイム問い合わせ対策。バッチ実行時は必ずフレッシュ取得） |
| 黒点子評価 | Redis 30d | **変更なし** |
| 個別銘柄 yfinance info | なし | **変更なし**（詳細画面は都度取得） |

## 10. 移行計画（段階的切替）

### Phase 1: 並行稼働（feature flag）
- `SCORING_DATA_SOURCE` に `"screener"` を追加。既定は現行の `"hybrid"` のまま。
- `run_batch_scoring_sync` が flag で分岐
- 検証: 一度両方を回して `stock_scores` テーブルの差分を比較

### Phase 2: 既定切替
- Cloud Run の環境変数で `SCORING_DATA_SOURCE=screener` に切替
- 1 週間稼働監視（エラー率・スコア分布・処理時間）
- kurotenko cache hit 率・miss 時の yfinance エラー率を確認

### Phase 3: 旧パス削除
- `tradingview_ta_client.py` を削除
- `yfinance_client.fetch_stock_data` はバッチから不要に（個別用途のみ保持）
- `SCORING_DATA_SOURCE` / `SCORING_MAX_WORKERS` / `SCORING_YFINANCE_MIN_INTERVAL_SEC` 設定削除
- `_fetch_merged_data` / `_score_symbol_with_retry` / ThreadPoolExecutor 削除

## 11. テスト戦略

### ユニットテスト
- `tv_screener_adapter.tv_row_to_info` の単位変換・キーマッピング
- `calc_technical_score_from_tv` の判定ロジック
- `tv_screener_client.fetch_japan_market_snapshot` は **VCR 録画 or モック**（外部 API 依存のため）

### 互換性テスト
- 同一の TV row から変換した info を `calc_fundamental_score` に食わせ、期待スコアと一致することを確認
- 現行 yfinance パスの結果と新パスの結果を 50 銘柄でサンプル比較（スコアの ±10 以内で収束を確認）

### 統合テスト
- 空 DB から `run_batch_scoring_sync`（new）を実行 → 数千行の StockScore が作成されることを確認（Staging 環境）

## 12. リスクと緩和策

| リスク | 影響 | 緩和策 |
|---|---|---|
| TV Screener の利用規約 | 商用利用や API 呼び出し頻度で制約の可能性 | 利用規約を事前確認。個人利用 + 1 日数回呼び出しなら実用上問題なしの見込み |
| TV フィールド欠損率 | スコア精度低下 | `data_quality` に `partial_tv` を新設し UI で表示。閾値超えたら yfinance フォールバックへ feature flag 戻し |
| 日本の新興 ETF / REIT 未収録 | スコアリング対象外になる | Phase 1 で欠損率を計測。問題なら JPX マスタから ETF/REIT を除外するか、別パスで yfinance 補完 |
| `tradingview-screener` パッケージのメンテ放棄 | 将来の API 変更で壊れる | MCP 経由で同じ API を叩いていることは確認済み。パッケージがダメになっても HTTP を直接叩ける（非公式 API） |
| TV の指標算出定義と pandas_ta の差異 | 技術スコアが現行と乖離 | Phase 1 の並行稼働で 50 銘柄サンプル比較。乖離が大きい指標は TV 側定義に合わせて閾値を再キャリブレート |

## 13. 未決事項

1. ~~`tradingview-screener` パッケージの正式採用可否~~ → **解決**: v3.1.0 動作確認済み（MIT License, アクティブメンテ）。ただし **TradingView 利用規約の商用/サーバー用途** は Phase 2 切替前に要確認。
2. **並行稼働モードでの差分許容閾値**
   - rating 一致率 ≥95% / 平均 technical_score 差 ±3 pt / 平均 fundamental_score 差 ±2 pt を Phase 1 合格ラインとして提案（要合意）
3. **ページネーション**
   - 3,892 銘柄が 1 回のクエリで返ってきたので既定 limit は実用上問題なし。念のため `range=[0, 5000]` を明示して取得し、返却件数の下振れを監視
4. **MACD ボーナス削除の影響範囲**
   - top100 銘柄サンプルで現行 `macd_score` 分布を採取し、クロス検出ボーナス寄与率を定量化（Phase 1 準備段階）

## 14. 成果物・ファイル変更サマリ

### 新規
- `backend/app/external/tv_screener_client.py`
- `backend/app/external/tv_screener_adapter.py`
- `backend/app/analyzer/technical_from_tv.py`
- `backend/tests/test_tv_screener_client.py`
- `backend/tests/test_tv_screener_adapter.py`
- `backend/tests/test_technical_from_tv.py`

### 変更
- `backend/app/services/scoring_service.py`（run_batch_scoring_sync の本体差し替え）
- `backend/requirements.txt`（`tradingview-screener` 追加）
- `backend/app/core/config.py`（`SCORING_DATA_SOURCE` に `screener` を追加）

### 削除（Phase 3）
- `backend/app/external/tradingview_ta_client.py`
- 関連環境変数（`SCORING_DATA_SOURCE`, `SCORING_MAX_WORKERS`, `SCORING_YFINANCE_MIN_INTERVAL_SEC`）

### スコープ外（削除しない）
- `backend/scripts/bulk_tv_signals.py` / `backend/scripts/batch_tv_analysis.py` — `tradingview_signals` テーブルに書き込むバッチで、ホーム画面 `LatestSignalsCard` や `StockRankingPage` のシグナル表示を支える別サブシステム。本 refactor のスコア（`stock_scores`）とは別軸。将来、TV Screener ベースのシグナル抽出で置換する場合は別チケット化。

### 温存
- `backend/app/external/yfinance_client.py`（個別取得用途）
- `backend/app/analyzer/kurotenko_screener.py`
- `backend/app/analyzer/fundamental.py` / `technical.py` / `scorer.py`

## 15. 次のステップ

次は **実装タスク分解（plan）** に進む。本設計のレビューで承認を得た後、`docs/superpowers/plans/2026-04-18-tv-screener-bulk.md` を作成し、Phase 1 → 2 → 3 のタスクに分割する。
