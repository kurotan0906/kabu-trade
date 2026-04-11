import { useEffect, useState } from 'react';
import { Link } from 'react-router-dom';
import {
  Card,
  CardHeader,
  CardTitle,
  CardBody,
  Badge,
  Progress,
  EmptyState,
  Button,
} from '@/components/ui';
import { scoresApi } from '@/services/api/scoresApi';
import type { StockScore } from '@/types/stockScore';

const RATING_TONE: Record<string, 'brand' | 'success' | 'slate' | 'warn' | 'danger'> = {
  強い買い: 'brand',
  買い: 'success',
  中立: 'slate',
  売り: 'warn',
  強い売り: 'danger',
};

export const TopScoresCard = () => {
  const [scores, setScores] = useState<StockScore[] | null>(null);

  useEffect(() => {
    scoresApi
      .listScores('total_score', 5)
      .then(setScores)
      .catch(() => setScores([]));
  }, []);

  if (scores === null) {
    return (
      <Card>
        <CardBody className="text-sm text-slate-500">読み込み中...</CardBody>
      </Card>
    );
  }

  return (
    <Card>
      <CardHeader>
        <CardTitle>スコア TOP 5</CardTitle>
        <Link to="/ranking" className="text-xs text-brand-600 hover:underline">
          すべて見る →
        </Link>
      </CardHeader>
      <CardBody>
        {scores.length === 0 ? (
          <EmptyState
            title="スコアデータがありません"
            description="ヘッダーの ▶ バッチ からスコアリングを実行してください"
            action={
              <Button variant="accent" size="sm">
                ▶ バッチ
              </Button>
            }
          />
        ) : (
          <ul className="divide-y divide-slate-100">
            {scores.map((s, i) => (
              <li key={s.id}>
                <Link
                  to={`/stocks/${s.symbol.replace('.T', '')}`}
                  className="flex items-center gap-3 py-2.5 hover:bg-slate-50 rounded-md -mx-2 px-2"
                >
                  <span className="w-6 text-xs text-slate-400 tabular-nums">
                    {i + 1}
                  </span>
                  <div className="flex-1 min-w-0">
                    <div className="text-sm font-semibold text-slate-900">
                      {s.symbol}
                    </div>
                    <div className="text-xs text-slate-500 truncate">{s.name}</div>
                  </div>
                  <div className="w-32">
                    <Progress value={s.total_score ?? 0} />
                  </div>
                  <div className="w-12 text-right text-sm font-bold tabular-nums text-brand-600">
                    {Math.round(s.total_score ?? 0)}
                  </div>
                  {s.rating && (
                    <Badge tone={RATING_TONE[s.rating] ?? 'slate'}>{s.rating}</Badge>
                  )}
                </Link>
              </li>
            ))}
          </ul>
        )}
      </CardBody>
    </Card>
  );
};
