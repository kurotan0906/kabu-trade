# 設計書: TradingView Lightweight Charts 導入

_date: 2026-04-04_

## 概要

`StockChart.tsx` の描画ライブラリを `recharts` から TradingView の `lightweight-charts` に置き換える。
チャートタイプをローソク足 + 出来高に変更し、ダークテーマを適用する。

## スコープ

- **対象ファイル**: `frontend/src/components/stock/StockChart.tsx`（置き換え）
- **変更なし**: `StockDetailPage.tsx`、`types/stock.ts`、その他すべて
- **依存関係**: `recharts` 削除、`lightweight-charts` 追加

## 依存関係の変更

```
削除: recharts (^2.10.3)
追加: lightweight-charts (^4.x)
```

## コンポーネント設計

### インターフェース（変更なし）

```tsx
interface StockChartProps {
  prices: StockPriceData[];
  period: string;
}
```

呼び出し側（`StockDetailPage.tsx`）は一切変更不要。

### 内部構造

```
StockChart
  ├── containerRef: チャートをマウントする div への ref
  ├── chartRef: IChartApi インスタンスの保持（cleanup 用）
  ├── useEffect [初期化]: createChart → candlestickSeries + volumeSeries 生成
  ├── useEffect [データ更新]: prices 変化時に setData で再描画
  ├── useEffect [リサイズ]: ResizeObserver でコンテナ幅に追従
  └── cleanup: chart.remove() でメモリリーク防止
```

## データ変換

`StockPriceData`（既存型）→ Lightweight Charts 形式:

| StockPriceData フィールド | LW Charts フィールド | 変換内容 |
|---|---|---|
| `date` (ISO文字列 e.g. `"2024-01-15T00:00:00"`) | `time` (`"2024-01-15"`) | `.split('T')[0]` で日付部分を切り出す |
| `open` / `high` / `low` / `close` | `open` / `high` / `low` / `close` | そのまま |
| `volume` | `value` | HistogramData の `value` にマッピング |

出来高の色分け:
- 終値 >= 始値（陽線）: `rgba(38, 166, 154, 0.5)` （緑）
- 終値 < 始値（陰線）: `rgba(239, 83, 80, 0.5)` （赤）

## チャート構成

### レイアウト

- **上部 70%**: ローソク足（`addCandlestickSeries`）
- **下部 30%**: 出来高（`addHistogramSeries`）、`priceScaleId: 'volume'` で独立スケール

### テーマ（ダーク）

```ts
layout: {
  background: { color: '#131722' },
  textColor: '#d1d4dc',
},
grid: {
  vertLines: { color: '#2a2e39' },
  horzLines: { color: '#2a2e39' },
},
```

### 価格フォーマット

右軸に円表示:
```ts
priceFormat: {
  type: 'custom',
  formatter: (price: number) => `${price.toLocaleString()}円`,
}
```

### レスポンシブ対応

`ResizeObserver` でコンテナの幅変化を監視し、`chart.applyOptions({ width })` で追従する。

## エラーハンドリング

- `prices` が空配列の場合は `StockDetailPage.tsx` 側で「データがありません」を表示済みのため、`StockChart.tsx` 内での空チェックは不要。
- チャートの初期化失敗は発生しないと想定（DOM mount 後に実行するため）。

## テスト方針

- フロントエンドのテストは現時点で最小構成（`tech.md` 記載）のため、本変更でテストは追加しない。
- 動作確認は `npm run dev` で実際のチャートを目視確認する。

## 実装後の確認項目

- [ ] ローソク足が正しく表示される（陽線・陰線の色分け）
- [ ] 出来高バーが下部に表示される
- [ ] 期間変更（PeriodSelector）でチャートが再描画される
- [ ] ウィンドウリサイズでチャートが追従する
- [ ] `recharts` が `package.json` から削除されている
