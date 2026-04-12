import { apiClient } from '@/lib/apiClient';
import type {
  SimulateRequest,
  SimulateResponse,
  RequiredRateResponse,
  HistoryEntry,
} from '@/types/advisor';

export const advisorApi = {
  async simulate(req: SimulateRequest): Promise<SimulateResponse> {
    const { data } = await apiClient.post<SimulateResponse>('/advisor/simulate', req);
    return data;
  },
  async requiredRate(req: {
    goal: number;
    pv: number;
    n_months: number;
    monthly_investment: number;
  }): Promise<RequiredRateResponse> {
    const { data } = await apiClient.post<RequiredRateResponse>('/advisor/required-rate', req);
    return data;
  },
  async listHistory(limit = 50): Promise<HistoryEntry[]> {
    const { data } = await apiClient.get<HistoryEntry[]>('/advisor/history', { params: { limit } });
    return data;
  },
};
