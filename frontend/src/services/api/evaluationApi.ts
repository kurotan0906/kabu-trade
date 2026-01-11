/**
 * Evaluation API client
 */

import axios from 'axios';
import type { EvaluationResult } from '@/types/evaluation';

const API_BASE_URL = '/api/v1';

const apiClient = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
});

export const evaluationApi = {
  /**
   * 銘柄の評価を実行
   */
  async evaluateStock(
    code: string,
    period: string = '1y'
  ): Promise<EvaluationResult> {
    const response = await apiClient.post<EvaluationResult>(
      '/evaluations',
      null,
      {
        params: { stock_code: code, period },
      }
    );
    return response.data;
  },

  /**
   * 評価結果を取得
   */
  async getEvaluation(evaluationId: number): Promise<EvaluationResult> {
    const response = await apiClient.get<EvaluationResult>(
      `/evaluations/${evaluationId}`
    );
    return response.data;
  },
};
