export type AccountType = 'general' | 'nisa_growth' | 'nisa_tsumitate';

export interface Holding {
  id: number;
  symbol: string;
  name: string | null;
  quantity: number;
  avg_price: number;
  purchase_date: string | null;
  account_type: AccountType;
  created_at: string | null;
  updated_at: string | null;
}

export interface HoldingCreate {
  symbol: string;
  name?: string | null;
  quantity: number;
  avg_price: number;
  purchase_date?: string | null;
  account_type: AccountType;
}

export interface Trade {
  id: number;
  symbol: string;
  action: 'buy' | 'sell';
  quantity: number;
  price: number;
  executed_at: string;
  account_type: AccountType;
  note: string | null;
}

export interface PortfolioSettings {
  target_amount: number | null;
  target_deadline: string | null;
  monthly_investment: number | null;
  nisa_used_current_year: number;
}

export interface PortfolioSummary {
  total_value: number;
  total_cost: number;
  unrealized_pl: number;
  holdings_count: number;
  target_amount: number | null;
  progress_rate: number | null;
  nisa_remaining: number;
  current_phase: string | null;
}
