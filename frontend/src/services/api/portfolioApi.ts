import axios from 'axios';
import type {
  Holding,
  HoldingCreate,
  Trade,
  PortfolioSettings,
  PortfolioSummary,
} from '@/types/portfolio';

const apiClient = axios.create({
  baseURL: '/api/v1',
  headers: { 'Content-Type': 'application/json' },
});

export const portfolioApi = {
  async listHoldings(): Promise<Holding[]> {
    const { data } = await apiClient.get<Holding[]>('/portfolio/holdings');
    return data;
  },
  async createHolding(h: HoldingCreate): Promise<Holding> {
    const { data } = await apiClient.post<Holding>('/portfolio/holdings', h);
    return data;
  },
  async updateHolding(id: number, patch: Partial<HoldingCreate>): Promise<Holding> {
    const { data } = await apiClient.put<Holding>(`/portfolio/holdings/${id}`, patch);
    return data;
  },
  async deleteHolding(id: number): Promise<void> {
    await apiClient.delete(`/portfolio/holdings/${id}`);
  },
  async getSettings(): Promise<PortfolioSettings> {
    const { data } = await apiClient.get<PortfolioSettings>('/portfolio/settings');
    return data;
  },
  async updateSettings(patch: Partial<PortfolioSettings>): Promise<PortfolioSettings> {
    const { data } = await apiClient.put<PortfolioSettings>('/portfolio/settings', patch);
    return data;
  },
  async getSummary(): Promise<PortfolioSummary> {
    const { data } = await apiClient.get<PortfolioSummary>('/portfolio/summary');
    return data;
  },
  async listTrades(limit = 100): Promise<Trade[]> {
    const { data } = await apiClient.get<Trade[]>('/portfolio/trades', { params: { limit } });
    return data;
  },
  async createTrade(trade: Omit<Trade, 'id'>): Promise<Trade> {
    const { data } = await apiClient.post<Trade>('/portfolio/trades', trade);
    return data;
  },
};
