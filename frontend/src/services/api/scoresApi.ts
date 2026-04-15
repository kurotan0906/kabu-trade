import { apiClient } from '@/lib/apiClient';
import type { StockScore, AnalysisAxes, BatchStatus, ProfileKey } from '@/types/stockScore';

export type SortField = 'total_score' | 'fundamental_score' | 'technical_score' | 'kurotenko_score';

export const scoresApi = {
  async listScores(sort: SortField = 'total_score', limit = 100, profile?: ProfileKey): Promise<StockScore[]> {
    const params: Record<string, string | number> = { sort, limit };
    if (profile) params.profile = profile;
    const response = await apiClient.get<StockScore[]>('/scores', { params });
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
