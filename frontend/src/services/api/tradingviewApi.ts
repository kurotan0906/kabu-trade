import axios from 'axios';
import type { TradingViewSignal, TradingViewSignalCreate } from '@/types/tradingviewSignal';

const apiClient = axios.create({
  baseURL: '/api/v1',
  headers: { 'Content-Type': 'application/json' },
});

export const tradingviewApi = {
  async getSignal(symbol: string): Promise<TradingViewSignal> {
    const response = await apiClient.get<TradingViewSignal>(`/tradingview-signals/${symbol}`);
    return response.data;
  },

  async listSignals(): Promise<TradingViewSignal[]> {
    const response = await apiClient.get<TradingViewSignal[]>('/tradingview-signals');
    return response.data;
  },

  async createSignal(symbol: string, data: TradingViewSignalCreate): Promise<TradingViewSignal> {
    const response = await apiClient.post<TradingViewSignal>(`/tradingview-signals/${symbol}`, data);
    return response.data;
  },
};
