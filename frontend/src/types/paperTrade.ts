export type TradeAction = 'buy' | 'sell';

export type AccountUninitialized = { initialized: false };

export interface AccountInitialized {
  initialized: true;
  initial_cash: number;
  cash_balance: number;
  started_at: string;
  total_value: number;
  return_pct: number;
}

export type AccountResponse = AccountInitialized | AccountUninitialized;

export interface PaperTrade {
  id: number;
  symbol: string;
  action: TradeAction;
  quantity: number;
  price: number;
  total_amount: number;
  realized_pl: number | null;
  executed_at: string;
  note: string | null;
}

export interface TradesPage {
  items: PaperTrade[];
  total: number;
}

export interface PaperHolding {
  id: number;
  symbol: string;
  name: string | null;
  quantity: number;
  avg_price: number;
  current_price: number | null;
  market_value: number | null;
  unrealized_pl: number | null;
  unrealized_pl_pct: number | null;
}

export interface PaperSummary {
  initial_cash: number;
  cash_balance: number;
  holdings_value: number;
  total_value: number;
  unrealized_pl: number;
  realized_pl: number;
  return_pct: number;
  started_at: string;
}

export interface ChartPoint {
  date: string;
  cash: number;
  holdings_value: number;
  total_value: number;
}

export interface PerformanceItem {
  symbol: string;
  name: string | null;
  total_buy_amount: number;
  total_sell_amount: number;
  realized_pl: number;
  unrealized_pl: number;
  total_pl: number;
  return_pct: number | null;
  trade_count: number;
  win_count: number;
}

export interface SummaryMetrics {
  total_pl: number;
  realized_pl: number;
  unrealized_pl: number;
  return_pct: number | null;
  trade_count: number;
  buy_count: number;
  sell_count: number;
  win_count: number;
  loss_count: number;
  win_rate: number | null;
  avg_holding_days: number | null;
  best_trade_pl: number | null;
  worst_trade_pl: number | null;
  profit_factor: number | null;
  expectancy: number | null;
}

export interface PositionCycle {
  entry_date: string;
  exit_date: string;
  entry_price: number;
  exit_price: number;
  quantity: number;
  pl: number;
  return_pct: number;
  holding_days: number;
}

export interface OpenPosition {
  quantity: number;
  avg_price: number;
  current_price: number | null;
  unrealized_pl: number | null;
  unrealized_pl_pct: number | null;
  entry_date: string;
  holding_days: number;
  mfe: number | null;
  mae: number | null;
}

export interface TradeMarker {
  date: string;
  action: TradeAction;
  price: number;
  quantity: number;
}

export interface PricePoint {
  date: string;
  close: number;
}

export interface TimingData {
  price_series: PricePoint[];
  trade_markers: TradeMarker[];
}

export interface BuyAndHold {
  first_buy_date: string | null;
  first_buy_price: number | null;
  bh_value_now: number | null;
  bh_return_pct: number | null;
  actual_return_pct: number | null;
  diff_pct: number | null;
}

export interface EquityPoint {
  date: string;
  invested: number;
  realized_pl: number;
  unrealized_pl: number;
  total_pl: number;
}

export interface AnalyticsResponse {
  symbol: string;
  name: string | null;
  summary: SummaryMetrics;
  position_cycles: PositionCycle[];
  open_position: OpenPosition | null;
  timing: TimingData;
  buy_and_hold: BuyAndHold;
  equity_timeseries: EquityPoint[];
}

export interface TradeCreatePayload {
  action: TradeAction;
  symbol: string;
  quantity: number;
  price?: number;
  executed_at?: string;
  note?: string | null;
  name?: string | null;
}

export interface TradeCreateResponse {
  trade: PaperTrade;
  cash_balance: number;
  total_value: number;
}
