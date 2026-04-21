import type { FC } from 'react';
import type { AnalyticsResponse } from '@/types/paperTrade';

export interface IndicatorProps {
  symbol: string;
  data: AnalyticsResponse;
}

export interface IndicatorDef {
  id: string;
  label: string;
  description?: string;
  category: 'basic' | 'advanced';
  defaultEnabled: boolean;
  component: FC<IndicatorProps>;
}

export const STORAGE_KEY = 'paperTrade.symbolAnalytics.visibleIds';

export const loadVisibleIds = (fallback: string[]): string[] => {
  try {
    const raw = localStorage.getItem(STORAGE_KEY);
    if (!raw) return fallback;
    const parsed = JSON.parse(raw);
    return Array.isArray(parsed) ? parsed.filter((v) => typeof v === 'string') : fallback;
  } catch {
    return fallback;
  }
};

export const saveVisibleIds = (ids: string[]) => {
  try {
    localStorage.setItem(STORAGE_KEY, JSON.stringify(ids));
  } catch {
    /* ignore quota errors */
  }
};
