/**
 * Stock store (Zustand)
 */

import { create } from 'zustand';
import { stockApi } from '@/services/api/stockApi';
import type { StockInfo, StockPriceResponse } from '@/types/stock';

interface StockState {
  // State
  currentStock: StockInfo | null;
  stockPrices: StockPriceResponse | null;
  loading: boolean;
  error: string | null;

  // Actions
  fetchStock: (code: string) => Promise<void>;
  fetchPrices: (code: string, period?: string) => Promise<void>;
  clearError: () => void;
  reset: () => void;
}

export const useStockStore = create<StockState>((set) => ({
  // Initial state
  currentStock: null,
  stockPrices: null,
  loading: false,
  error: null,

  // Fetch stock info
  fetchStock: async (code: string) => {
    set({ loading: true, error: null });
    try {
      const stock = await stockApi.getStock(code);
      set({ currentStock: stock, loading: false });
    } catch (error: unknown) {
      let errorMessage = '銘柄情報の取得に失敗しました';
      if (error instanceof Error) {
        errorMessage = error.message;
      } else if (typeof error === 'object' && error !== null && 'response' in error) {
        const errorObj = error as Record<string, unknown>;
        const response = errorObj.response as Record<string, unknown>;
        if (response && typeof response === 'object' && 'data' in response) {
          const data = response.data as Record<string, unknown>;
          if ('error' in data && typeof data.error === 'object' && data.error !== null) {
            const errorDetail = data.error as Record<string, unknown>;
            if ('message' in errorDetail && typeof errorDetail.message === 'string') {
              errorMessage = errorDetail.message;
            }
          }
        }
      }
      set({ error: errorMessage, loading: false, currentStock: null });
    }
  },

  // Fetch stock prices
  fetchPrices: async (code: string, period: string = '1y') => {
    set({ loading: true, error: null });
    try {
      const prices = await stockApi.getPrices(code, period);
      set({ stockPrices: prices, loading: false });
    } catch (error: unknown) {
      let errorMessage = '株価データの取得に失敗しました';
      if (error instanceof Error) {
        errorMessage = error.message;
      } else if (typeof error === 'object' && error !== null && 'response' in error) {
        const errorObj = error as Record<string, unknown>;
        const response = errorObj.response as Record<string, unknown>;
        if (response && typeof response === 'object' && 'data' in response) {
          const data = response.data as Record<string, unknown>;
          if ('error' in data && typeof data.error === 'object' && data.error !== null) {
            const errorDetail = data.error as Record<string, unknown>;
            if ('message' in errorDetail && typeof errorDetail.message === 'string') {
              errorMessage = errorDetail.message;
            }
          }
        }
      }
      set({ error: errorMessage, loading: false, stockPrices: null });
    }
  },

  // Clear error
  clearError: () => set({ error: null }),

  // Reset state
  reset: () =>
    set({
      currentStock: null,
      stockPrices: null,
      loading: false,
      error: null,
    }),
}));
