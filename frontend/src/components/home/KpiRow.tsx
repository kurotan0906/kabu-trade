import { useEffect, useState } from 'react';
import { Stat, Badge, Progress } from '@/components/ui';
import { portfolioApi } from '@/services/api/portfolioApi';
import type { PortfolioSummary } from '@/types/portfolio';

const PHASE_TONE: Record<string, 'sky' | 'brand' | 'success'> = {
  積立期: 'sky',
  成長期: 'brand',
  安定期: 'success',
};

const formatYen = (v: number | null | undefined) => {
  if (v == null) return '—';
  return `¥${Math.round(v).toLocaleString()}`;
};

export const KpiRow = () => {
  const [summary, setSummary] = useState<PortfolioSummary | null>(null);

  useEffect(() => {
    portfolioApi
      .getSummary()
      .then(setSummary)
      .catch(() => setSummary(null));
  }, []);

  const progress = summary?.progress_rate ?? 0;
  const phase = summary?.current_phase ?? null;

  return (
    <div className="grid gap-4 grid-cols-2 lg:grid-cols-4">
      <Stat label="評価額" value={formatYen(summary?.total_value)} accent="brand" />
      <Stat
        label="目標進捗"
        value={summary?.target_amount ? `${progress.toFixed(1)}%` : '—'}
        hint={summary?.target_amount ? <Progress value={progress} /> : '目標未設定'}
        accent="success"
      />
      <Stat
        label="フェーズ"
        value={
          phase ? <Badge tone={PHASE_TONE[phase] ?? 'slate'}>{phase}</Badge> : '—'
        }
      />
      <Stat
        label="NISA残枠"
        value={formatYen(summary?.nisa_remaining)}
        hint="年間上限 ¥2,400,000"
      />
    </div>
  );
};
