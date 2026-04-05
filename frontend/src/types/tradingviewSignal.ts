export interface TradingViewSignal {
  id: number;
  symbol: string;
  recommendation: string | null;
  score: number | null;
  buy_count: number | null;
  sell_count: number | null;
  neutral_count: number | null;
  ma_recommendation: string | null;
  osc_recommendation: string | null;
  details: Record<string, unknown> | null;
  updated_at: string;
}

export interface TradingViewSignalCreate {
  recommendation?: string | null;
  score?: number | null;
  buy_count?: number | null;
  sell_count?: number | null;
  neutral_count?: number | null;
  ma_recommendation?: string | null;
  osc_recommendation?: string | null;
  details?: Record<string, unknown> | null;
}
