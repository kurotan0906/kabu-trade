/**
 * Evaluation related types
 */

export interface TechnicalIndicators {
  moving_averages: {
    ma_short: number;
    ma_medium: number;
    ma_long: number;
  };
  rsi: number;
  macd: {
    macd: number;
    signal: number;
    histogram: number;
  };
  bollinger_bands: {
    upper: number;
    middle: number;
    lower: number;
  };
  support_resistance: {
    support: number;
    resistance: number;
  };
}

export interface FundamentalMetrics {
  score: number;
  evaluation: string;
  per_evaluation: {
    score: number;
    evaluation: string;
    description: string;
  };
  pbr_evaluation: {
    score: number;
    evaluation: string;
    description: string;
  };
  descriptions: string[];
}

export interface BuySignal {
  score: number;
  recommendation: string;
  reasons: string[];
}

export interface SellSignal {
  score: number;
  recommendation: string;
  reasons: string[];
}

export interface EvaluationResult {
  id?: number;
  stock_code: string;
  stock_name: string;
  buy_score: number;
  sell_score: number;
  buy_recommendation: string;
  sell_recommendation: string;
  technical_indicators: TechnicalIndicators;
  fundamental_metrics: FundamentalMetrics;
  buy_signal: BuySignal;
  sell_signal: SellSignal;
  evaluation_date: string;
}
