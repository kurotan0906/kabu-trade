import { useEffect, useState } from 'react';
import { Link } from 'react-router-dom';
import {
  Card,
  CardHeader,
  CardTitle,
  CardBody,
  Badge,
  EmptyState,
} from '@/components/ui';
import { tradingviewApi } from '@/services/api/tradingviewApi';
import type { TradingViewSignal } from '@/types/tradingviewSignal';

const TONE: Record<string, 'success' | 'brand' | 'slate' | 'warn' | 'danger'> = {
  STRONG_BUY: 'success',
  BUY: 'brand',
  NEUTRAL: 'slate',
  SELL: 'warn',
  STRONG_SELL: 'danger',
};

export const LatestSignalsCard = () => {
  const [sigs, setSigs] = useState<TradingViewSignal[] | null>(null);

  useEffect(() => {
    tradingviewApi
      .listSignals()
      .then((xs) => setSigs(xs.slice(0, 5)))
      .catch(() => setSigs([]));
  }, []);

  if (sigs === null) {
    return (
      <Card>
        <CardBody className="text-sm text-slate-500">読み込み中...</CardBody>
      </Card>
    );
  }

  return (
    <Card>
      <CardHeader>
        <CardTitle>最新 TV シグナル</CardTitle>
      </CardHeader>
      <CardBody>
        {sigs.length === 0 ? (
          <EmptyState
            title="シグナルがまだありません"
            description="ランキング画面の TVバッチ分析 から Claude に依頼してください"
          />
        ) : (
          <ul className="divide-y divide-slate-100">
            {sigs.map((sig) => (
              <li key={sig.id}>
                <Link
                  to={`/stocks/${sig.symbol.replace('.T', '')}`}
                  className="flex items-center justify-between py-2.5 hover:bg-slate-50 rounded-md -mx-2 px-2"
                >
                  <div className="flex items-center gap-2">
                    <span className="text-sm font-semibold text-slate-900">
                      {sig.symbol}
                    </span>
                    {sig.recommendation && (
                      <Badge tone={TONE[sig.recommendation] ?? 'slate'}>
                        {sig.recommendation.replaceAll('_', ' ')}
                      </Badge>
                    )}
                  </div>
                  <span className="text-xs text-slate-500">
                    {sig.updated_at
                      ? new Date(sig.updated_at).toLocaleString('ja-JP')
                      : ''}
                  </span>
                </Link>
              </li>
            ))}
          </ul>
        )}
      </CardBody>
    </Card>
  );
};
