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
    } catch (error: any) {
      const errorMessage =
        error.response?.data?.error?.message ||
        error.message ||
        '銘柄情報の取得に失敗しました';
      set({ error: errorMessage, loading: false, currentStock: null });
    }
  },

  // Fetch stock prices
  fetchPrices: async (code: string, period: string = '1y') => {
    set({ loading: true, error: null });
    try {
      const prices = await stockApi.getPrices(code, period);
      set({ stockPrices: prices, loading: false });
    } catch (error: any) {
      const errorMessage =
        error.response?.data?.error?.message ||
        error.message ||
        '株価データの取得に失敗しました';
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
