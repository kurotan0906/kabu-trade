import { useEffect, useMemo, useState } from 'react';
import { Link, useParams } from 'react-router-dom';
import { PageHeader, Button } from '@/components/ui';
import { paperTradeApi } from '@/services/api/paperTradeApi';
import type { AnalyticsResponse } from '@/types/paperTrade';
import IndicatorSelector from '@/components/paper-trade/analytics/IndicatorSelector';
import { loadVisibleIds, saveVisibleIds } from '@/components/paper-trade/analytics/registry';
import type { IndicatorDef } from '@/components/paper-trade/analytics/registry';
import SummaryCard from '@/components/paper-trade/analytics/SummaryCard';
import PositionCyclesCard from '@/components/paper-trade/analytics/PositionCyclesCard';
import OpenPositionCard from '@/components/paper-trade/analytics/OpenPositionCard';
import TimingChartCard from '@/components/paper-trade/analytics/TimingChartCard';
import BuyAndHoldCard from '@/components/paper-trade/analytics/BuyAndHoldCard';
import EquityTimeseriesCard from '@/components/paper-trade/analytics/EquityTimeseriesCard';

const INDICATORS: IndicatorDef[] = [
  { id: 'summary', label: 'サマリ指標', category: 'basic', defaultEnabled: true, component: SummaryCard },
  { id: 'position_cycles', label: 'ポジションサイクル', category: 'basic', defaultEnabled: true, component: PositionCyclesCard },
  { id: 'open_position', label: '現在保有の健康度', category: 'basic', defaultEnabled: true, component: OpenPositionCard },
  { id: 'timing', label: 'タイミング可視化', category: 'basic', defaultEnabled: true, component: TimingChartCard },
  { id: 'buy_and_hold', label: 'バイ＆ホールド比較', category: 'advanced', defaultEnabled: false, component: BuyAndHoldCard },
  { id: 'equity_timeseries', label: '投下資本/損益推移', category: 'advanced', defaultEnabled: false, component: EquityTimeseriesCard },
];

const DEFAULT_VISIBLE = INDICATORS.filter((i) => i.defaultEnabled).map((i) => i.id);

const PaperTradeSymbolPage = () => {
  const { symbol = '' } = useParams();
  const [data, setData] = useState<AnalyticsResponse | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [visibleIds, setVisibleIds] = useState<string[]>(() => loadVisibleIds(DEFAULT_VISIBLE));

  useEffect(() => {
    let cancelled = false;
    (async () => {
      setLoading(true);
      setError(null);
      try {
        const r = await paperTradeApi.getSymbolAnalytics(symbol);
        if (!cancelled) setData(r);
      } catch (err) {
        if (!cancelled) setError(err instanceof Error ? err.message : '取得に失敗しました');
      } finally {
        if (!cancelled) setLoading(false);
      }
    })();
    return () => {
      cancelled = true;
    };
  }, [symbol]);

  const updateVisibleIds = (ids: string[]) => {
    setVisibleIds(ids);
    saveVisibleIds(ids);
  };

  const visibleIndicators = useMemo(
    () => INDICATORS.filter((ind) => visibleIds.includes(ind.id)),
    [visibleIds]
  );

  if (loading) return <div className="p-6 text-sm text-slate-500">読み込み中...</div>;
  if (error || !data) {
    return (
      <div className="p-6">
        <Link to="/paper-trade" className="text-sm text-brand-600 hover:underline">
          ← ペーパートレードに戻る
        </Link>
        <div className="mt-4 text-sm text-rose-700">{error ?? 'データがありません'}</div>
      </div>
    );
  }

  return (
    <div>
      <PageHeader
        title={`${data.symbol}${data.name ? ' ' + data.name : ''}`}
        description="銘柄別の売買結果を多角的に分析"
        actions={
          <div className="flex gap-2">
            <Link to="/paper-trade">
              <Button variant="ghost" size="sm">← 戻る</Button>
            </Link>
            <IndicatorSelector
              registry={INDICATORS}
              visibleIds={visibleIds}
              onChange={updateVisibleIds}
            />
          </div>
        }
      />
      <div className="flex flex-col gap-4">
        {visibleIndicators.map((ind) => {
          const C = ind.component;
          return <C key={ind.id} symbol={symbol} data={data} />;
        })}
      </div>
    </div>
  );
};

export default PaperTradeSymbolPage;
