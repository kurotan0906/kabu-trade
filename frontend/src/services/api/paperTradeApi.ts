import { apiClient } from '@/lib/apiClient';
import type {
  AccountResponse,
  AccountInitialized,
  TradesPage,
  PaperHolding,
  PaperSummary,
  ChartPoint,
  PerformanceItem,
  AnalyticsResponse,
  TradeCreatePayload,
  TradeCreateResponse,
} from '@/types/paperTrade';

const base = '/paper-trade';

export const paperTradeApi = {
  async getAccount(): Promise<AccountResponse> {
    const { data } = await apiClient.get<AccountResponse>(`${base}/account`);
    return data;
  },
  async initAccount(initial_cash: number): Promise<AccountInitialized> {
    const { data } = await apiClient.post<AccountInitialized>(`${base}/account`, { initial_cash });
    return data;
  },
  async resetAccount(initial_cash?: number): Promise<AccountInitialized> {
    const { data } = await apiClient.post<AccountInitialized>(`${base}/account/reset`, { initial_cash });
    return data;
  },
  async listHoldings(): Promise<PaperHolding[]> {
    const { data } = await apiClient.get<PaperHolding[]>(`${base}/holdings`);
    return data;
  },
  async listTrades(limit = 100, offset = 0): Promise<TradesPage> {
    const { data } = await apiClient.get<TradesPage>(`${base}/trades`, { params: { limit, offset } });
    return data;
  },
  async createTrade(payload: TradeCreatePayload): Promise<TradeCreateResponse> {
    const { data } = await apiClient.post<TradeCreateResponse>(`${base}/trades`, payload);
    return data;
  },
  async getSummary(): Promise<PaperSummary> {
    const { data } = await apiClient.get<PaperSummary>(`${base}/summary`);
    return data;
  },
  async getChart(from?: string, to?: string): Promise<ChartPoint[]> {
    const { data } = await apiClient.get<ChartPoint[]>(`${base}/chart`, { params: { from, to } });
    return data;
  },
  async getPerformance(): Promise<PerformanceItem[]> {
    const { data } = await apiClient.get<PerformanceItem[]>(`${base}/performance`);
    return data;
  },
  async getSymbolAnalytics(symbol: string, from?: string, to?: string): Promise<AnalyticsResponse> {
    const { data } = await apiClient.get<AnalyticsResponse>(
      `${base}/symbols/${encodeURIComponent(symbol)}/analytics`,
      { params: { from, to } }
    );
    return data;
  },
};
