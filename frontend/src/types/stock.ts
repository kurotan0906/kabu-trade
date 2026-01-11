/**
 * Stock related types
 */

export interface StockInfo {
  code: string;
  name: string;
  sector: string | null;
  market_cap: number | null;
  current_price: number | null;
  per: number | null;
  pbr: number | null;
}

export interface StockPriceData {
  date: string;
  open: number;
  high: number;
  low: number;
  close: number;
  volume: number;
}

export interface StockPriceResponse {
  stock_code: string;
  stock_name: string;
  period: string;
  prices: StockPriceData[];
}
