# Lightweight Charts 導入 実装プラン

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** `StockChart.tsx` の描画ライブラリを recharts から lightweight-charts に置き換え、ローソク足 + 出来高チャート（ダークテーマ）を実装する。

**Architecture:** `StockChart.tsx` を丸ごと書き直す。チャートインスタンスの初期化・データ更新・リサイズをそれぞれ独立した `useEffect` で管理し、クリーンアップで `chart.remove()` を呼ぶ。呼び出し側（`StockDetailPage.tsx`）のインターフェースは変更しない。

**Tech Stack:** lightweight-charts v4, React 18 (useRef / useEffect), TypeScript strict mode

---

## ファイル構成

| ファイル | 変更内容 |
|---|---|
| `frontend/package.json` | `recharts` 削除、`lightweight-charts` 追加 |
| `frontend/src/components/stock/StockChart.tsx` | 全面書き直し |

---

### Task 1: 依存パッケージの入れ替え

**Files:**
- Modify: `frontend/package.json`

- [ ] **Step 1: recharts を削除して lightweight-charts をインストールする**

`frontend/` ディレクトリで実行:

```bash
cd frontend
npm uninstall recharts
npm install lightweight-charts
```

- [ ] **Step 2: インストール結果を確認する**

```bash
cat package.json | grep -E '"recharts"|"lightweight-charts"'
```

期待出力（`recharts` は表示されず、`lightweight-charts` だけ表示される）:
```
    "lightweight-charts": "^4.x.x",
```

- [ ] **Step 3: コミット**

```bash
git add frontend/package.json frontend/package-lock.json
git commit -m "chore: replace recharts with lightweight-charts"
```

---

### Task 2: StockChart.tsx を書き直す

**Files:**
- Modify: `frontend/src/components/stock/StockChart.tsx`

> **背景:** Lightweight Charts はキャンバスベースのライブラリで、React の JSX としてではなく DOM に直接マウントする。`useRef` で DOM 要素を取得し、`useEffect` でチャートを生成・破棄するパターンが基本。

- [ ] **Step 1: ファイルを以下の内容で全面置き換えする**

`frontend/src/components/stock/StockChart.tsx` を次の内容で上書きする:

```tsx
import { useEffect, useRef } from 'react';
import {
  createChart,
  ColorType,
  IChartApi,
  ISeriesApi,
  CandlestickData,
  HistogramData,
  Time,
} from 'lightweight-charts';
import type { StockPriceData } from '@/types/stock';

interface StockChartProps {
  prices: StockPriceData[];
  period: string;
}

const StockChart = ({ prices, period }: StockChartProps) => {
  const containerRef = useRef<HTMLDivElement>(null);
  const chartRef = useRef<IChartApi | null>(null);
  const candleSeriesRef = useRef<ISeriesApi<'Candlestick'> | null>(null);
  const volumeSeriesRef = useRef<ISeriesApi<'Histogram'> | null>(null);

  // チャートインスタンスの初期化（マウント時に1回だけ）
  useEffect(() => {
    if (!containerRef.current) return;
    const container = containerRef.current;

    const chart = createChart(container, {
      width: container.clientWidth,
      height: 400,
      layout: {
        background: { type: ColorType.Solid, color: '#131722' },
        textColor: '#d1d4dc',
      },
      grid: {
        vertLines: { color: '#2a2e39' },
        horzLines: { color: '#2a2e39' },
      },
      rightPriceScale: {
        borderColor: '#2a2e39',
      },
      timeScale: {
        borderColor: '#2a2e39',
        timeVisible: false,
      },
    });
    chartRef.current = chart;

    // ローソク足系列（上部70%）
    const candleSeries = chart.addCandlestickSeries({
      upColor: '#26a69a',
      downColor: '#ef5350',
      borderVisible: false,
      wickUpColor: '#26a69a',
      wickDownColor: '#ef5350',
      priceFormat: {
        type: 'custom',
        formatter: (price: number) => `${price.toLocaleString()}円`,
        minMove: 1,
      },
    });
    candleSeries.priceScale().applyOptions({
      scaleMargins: { top: 0.1, bottom: 0.3 },
    });
    candleSeriesRef.current = candleSeries;

    // 出来高系列（下部30%、オーバーレイスケール＝右軸に数値を出さない）
    const volumeSeries = chart.addHistogramSeries({
      priceFormat: { type: 'volume' },
      priceScaleId: '',
    });
    volumeSeries.priceScale().applyOptions({
      scaleMargins: { top: 0.7, bottom: 0 },
    });
    volumeSeriesRef.current = volumeSeries;

    // レスポンシブ対応
    const resizeObserver = new ResizeObserver((entries) => {
      for (const entry of entries) {
        chart.applyOptions({ width: entry.contentRect.width });
      }
    });
    resizeObserver.observe(container);

    return () => {
      resizeObserver.disconnect();
      chart.remove();
      chartRef.current = null;
      candleSeriesRef.current = null;
      volumeSeriesRef.current = null;
    };
  }, []);

  // prices 変化時にデータを更新
  useEffect(() => {
    if (!candleSeriesRef.current || !volumeSeriesRef.current) return;

    const candleData: CandlestickData[] = prices.map((p) => ({
      time: p.date.split('T')[0] as Time,
      open: p.open,
      high: p.high,
      low: p.low,
      close: p.close,
    }));

    const volumeData: HistogramData[] = prices.map((p) => ({
      time: p.date.split('T')[0] as Time,
      value: p.volume,
      color:
        p.close >= p.open
          ? 'rgba(38, 166, 154, 0.5)'
          : 'rgba(239, 83, 80, 0.5)',
    }));

    candleSeriesRef.current.setData(candleData);
    volumeSeriesRef.current.setData(volumeData);
    chartRef.current?.timeScale().fitContent();
  }, [prices]);

  return (
    <div style={{ marginTop: '2rem' }}>
      <h3>株価チャート ({period})</h3>
      <div ref={containerRef} style={{ width: '100%' }} />
    </div>
  );
};

export default StockChart;
```

- [ ] **Step 2: TypeScript のコンパイルエラーがないか確認する**

```bash
cd frontend
npx tsc --noEmit
```

期待出力: エラーなし（何も表示されない）

- [ ] **Step 3: lint を通す**

```bash
cd frontend
npm run lint
```

期待出力: `0 warnings, 0 errors`

- [ ] **Step 4: コミット**

```bash
git add frontend/src/components/stock/StockChart.tsx
git commit -m "feat: replace recharts with lightweight-charts (candlestick + volume, dark theme)"
```

---

### Task 3: 動作確認

**Files:** なし（確認のみ）

- [ ] **Step 1: 開発サーバーを起動する**

Docker で PostgreSQL / Redis が起動している前提。バックエンドも起動している前提。

```bash
cd frontend
npm run dev
```

- [ ] **Step 2: ブラウザで動作を確認する**

`http://localhost:5173` を開き、任意の銘柄コードで銘柄詳細ページへ遷移する。

以下をすべて目視で確認:
- [ ] ローソク足が表示される（陽線=緑、陰線=赤）
- [ ] チャート下部に出来高バーが表示される
- [ ] 期間ボタン（1日/1週間/1ヶ月/3ヶ月/6ヶ月/1年）を切り替えるとチャートが再描画される
- [ ] ブラウザウィンドウを横にリサイズするとチャートが追従する
- [ ] コンソールにエラーが出ていない

- [ ] **Step 3: 確認完了後、完了コミットは不要**（動作確認のみのタスクのため）
