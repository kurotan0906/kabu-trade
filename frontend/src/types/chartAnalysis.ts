export interface ChartSignals {
  rsi?: string;
  ma?: string;
  macd?: string;
  bollinger?: string;
  [key: string]: string | undefined;
}

export interface ChartAnalysis {
  id: number;
  symbol: string;
  timeframe: string;
  screenshot_path: string | null;
  trend: 'bullish' | 'bearish' | 'neutral';
  signals: ChartSignals | null;
  summary: string;
  recommendation: 'buy' | 'sell' | 'hold';
  created_at: string;
}

export interface ChartAnalysisCreate {
  symbol: string;
  timeframe: string;
  screenshot_path?: string;
  trend: 'bullish' | 'bearish' | 'neutral';
  signals?: ChartSignals;
  summary: string;
  recommendation: 'buy' | 'sell' | 'hold';
}
