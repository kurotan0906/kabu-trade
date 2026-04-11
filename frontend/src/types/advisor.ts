export interface SimulatePoint {
  year: number;
  value: number;
  contributed: number;
  gain: number;
}

export interface SimulateResponse {
  final_value: number;
  total_contributed: number;
  total_gain: number;
  timeseries: SimulatePoint[];
}

export interface SimulateRequest {
  pv: number;
  monthly_investment: number;
  annual_rate: number;
  years: number;
}

export interface RequiredRateResponse {
  annual_rate_percent: number | null;
  feasible: boolean;
}

export interface HistoryEntry {
  id: number;
  created_at: string;
  input_json: Record<string, unknown>;
  result_json: Record<string, unknown>;
}
