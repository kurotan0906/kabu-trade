import { useEffect, useState } from 'react';
import { Link } from 'react-router-dom';
import {
  Card,
  CardHeader,
  CardTitle,
  CardBody,
  EmptyState,
  Button,
} from '@/components/ui';
import { portfolioApi } from '@/services/api/portfolioApi';
import type { Holding } from '@/types/portfolio';

export const HoldingsQuickCard = () => {
  const [holdings, setHoldings] = useState<Holding[] | null>(null);

  useEffect(() => {
    portfolioApi
      .listHoldings()
      .then((xs) => setHoldings(xs.slice(0, 5)))
      .catch(() => setHoldings([]));
  }, []);

  if (holdings === null) {
    return (
      <Card>
        <CardBody className="text-sm text-slate-500">読み込み中...</CardBody>
      </Card>
    );
  }

  return (
    <Card>
      <CardHeader>
        <CardTitle>保有銘柄</CardTitle>
        <Link to="/portfolio" className="text-xs text-brand-600 hover:underline">
          詳細 →
        </Link>
      </CardHeader>
      <CardBody>
        {holdings.length === 0 ? (
          <EmptyState
            title="まだ保有銘柄がありません"
            action={
              <Link to="/portfolio">
                <Button variant="accent" size="sm">
                  ＋ 追加
                </Button>
              </Link>
            }
          />
        ) : (
          <ul className="divide-y divide-slate-100">
            {holdings.map((h) => (
              <li key={h.id}>
                <Link
                  to={`/stocks/${h.symbol.replace('.T', '')}`}
                  className="flex items-center justify-between py-2.5 hover:bg-slate-50 rounded-md -mx-2 px-2"
                >
                  <div className="min-w-0">
                    <div className="text-sm font-semibold text-slate-900">
                      {h.symbol}
                    </div>
                    <div className="text-xs text-slate-500 truncate">{h.name}</div>
                  </div>
                  <div className="text-right">
                    <div className="text-sm text-slate-900 tabular-nums">
                      {h.quantity}株
                    </div>
                    <div className="text-xs text-slate-500 tabular-nums">
                      ¥{Math.round(h.avg_price).toLocaleString()}
                    </div>
                  </div>
                </Link>
              </li>
            ))}
          </ul>
        )}
      </CardBody>
    </Card>
  );
};
