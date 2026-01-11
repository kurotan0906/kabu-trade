/**
 * Stock API client
 */

import axios from 'axios';
import type { StockInfo, StockPriceResponse } from '@/types/stock';

const API_BASE_URL = '/api/v1';

const apiClient = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
});

export const stockApi = {
  /**
   * 銘柄情報を取得
   */
  async getStock(code: string): Promise<StockInfo> {
    const response = await apiClient.get<StockInfo>(`/stocks/${code}`);
    return response.data;
  },

  /**
   * 株価データを取得
   */
  async getPrices(
    code: string,
    period: string = '1y'
  ): Promise<StockPriceResponse> {
    const response = await apiClient.get<StockPriceResponse>(
      `/stocks/${code}/prices`,
      {
        params: { period },
      }
    );
    return response.data;
  },
};
