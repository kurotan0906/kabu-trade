/**
 * Stock API client
 */

import { apiClient } from '@/lib/apiClient';
import type { StockInfo, StockPriceResponse } from '@/types/stock';

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
