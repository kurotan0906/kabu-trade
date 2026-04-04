import { useEffect, useRef } from 'react';
import {
  createChart,
  ColorType,
  IChartApi,
  ISeriesApi,
  CandlestickData,
  HistogramData,
  Time,
  CandlestickSeries,
  HistogramSeries,
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
    const candleSeries = chart.addSeries(CandlestickSeries, {
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
    const volumeSeries = chart.addSeries(HistogramSeries, {
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
