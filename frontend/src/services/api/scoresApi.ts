import axios from 'axios';
import type { StockScore, AnalysisAxes, BatchStatus } from '@/types/stockScore';

const API_BASE_URL = '/api/v1';

const apiClient = axios.create({
  baseURL: API_BASE_URL,
  headers: { 'Content-Type': 'application/json' },
});

type SortField = 'total_score' | 'fundamental_score' | 'technical_score' | 'kurotenko_score';

export const scoresApi = {
  async listScores(sort: SortField = 'total_score', limit = 100): Promise<StockScore[]> {
    const response = await apiClient.get<StockScore[]>('/scores', { params: { sort, limit } });
    return response.data;
  },

  async getScore(symbol: string): Promise<StockScore> {
    const response = await apiClient.get<StockScore>(`/scores/${symbol}`);
    return response.data;
  },

  async getAxes(symbol: string): Promise<AnalysisAxes> {
    const response = await apiClient.get<AnalysisAxes>(`/scores/${symbol}/axes`);
    return response.data;
  },

  async triggerBatch(): Promise<{ message: string; status: string }> {
    const response = await apiClient.post('/batch/scoring/run');
    return response.data;
  },

  async getBatchStatus(): Promise<BatchStatus> {
    const response = await apiClient.get<BatchStatus>('/batch/scoring/status');
    return response.data;
  },
};
