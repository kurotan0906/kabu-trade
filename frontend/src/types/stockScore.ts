export interface StockScore {
  id: number;
  symbol: string;
  name: string | null;
  sector: string | null;
  scored_at: string;
  total_score: number | null;
  rating: string | null;
  fundamental_score: number | null;
  technical_score: number | null;
  kurotenko_score: number | null;
  kurotenko_criteria: Record<string, boolean | null> | null;
  per: number | null;
  pbr: number | null;
  roe: number | null;
  dividend_yield: number | null;
  revenue_growth: number | null;
  ma_score: number | null;
  rsi_score: number | null;
  macd_score: number | null;
  close_price: number | null;
  data_quality: 'ok' | 'fetch_error' | 'partial';
  profile_score?: number | null;
  profile_name?: string | null;
  current_phase?: string | null;
  adjusted_total_score?: number | null;
}

export type ProfileKey = 'growth' | 'balanced' | 'income' | 'auto';

export interface AnalysisAxis {
  name: string;
  score: number | null;
  recommendation: string | null;
  detail: Record<string, unknown>;
}

export interface AnalysisAxes {
  symbol: string;
  axes: AnalysisAxis[];
}

export interface BatchStatus {
  status: 'idle' | 'running' | 'done' | 'error';
  total: number;
  processed: number;
  failed: number;
  started_at: string | null;
  finished_at: string | null;
}
