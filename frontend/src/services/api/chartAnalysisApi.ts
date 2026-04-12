import { apiClient } from '@/lib/apiClient';
import type { ChartAnalysis, ChartAnalysisCreate } from '@/types/chartAnalysis';

export const chartAnalysisApi = {
  async saveAnalysis(data: ChartAnalysisCreate): Promise<ChartAnalysis> {
    const response = await apiClient.post<ChartAnalysis>('/chart-analysis', data);
    return response.data;
  },

  async getLatest(symbol: string, timeframe?: string): Promise<ChartAnalysis> {
    const params = timeframe ? { timeframe } : undefined;
    const response = await apiClient.get<ChartAnalysis>(
      `/chart-analysis/${symbol}/latest`,
      { params }
    );
    return response.data;
  },

  async getHistory(
    symbol: string,
    timeframe?: string,
    limit: number = 20
  ): Promise<ChartAnalysis[]> {
    const params: Record<string, string | number> = { limit };
    if (timeframe) params.timeframe = timeframe;
    const response = await apiClient.get<ChartAnalysis[]>(
      `/chart-analysis/${symbol}/history`,
      { params }
    );
    return response.data;
  },
};
