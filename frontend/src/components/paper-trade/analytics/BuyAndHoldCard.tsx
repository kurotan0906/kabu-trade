import { Card, CardBody, Stat, EmptyState } from '@/components/ui';
import type { IndicatorProps } from './registry';

const formatYen = (v: number | null | undefined) =>
  v == null ? '—' : `¥${Math.round(v).toLocaleString()}`;
const formatPct = (v: number | null | undefined) =>
  v == null ? '—' : `${v >= 0 ? '+' : ''}${v.toFixed(2)}%`;

export const BuyAndHoldCard = ({ data }: IndicatorProps) => {
  const b = data.buy_and_hold;
  const hasData = b.first_buy_date != null;
  return (
    <Card>
      <CardBody>
        <h3 className="mb-3 text-base font-semibold text-slate-900">バイ＆ホールド比較</h3>
        {!hasData ? (
          <EmptyState title="買いが 1 件もありません" description="" />
        ) : (
          <>
            <p className="mb-3 text-xs text-slate-500">
              最初の買い（{b.first_buy_date && new Date(b.first_buy_date).toLocaleDateString()} /{' '}
              {formatYen(b.first_buy_price)}）の数量を売買せずに保有し続けた場合との比較。
            </p>
            <div className="grid gap-3 grid-cols-2 md:grid-cols-4">
              <Stat label="実トレード リターン" value={formatPct(b.actual_return_pct)} />
              <Stat label="バイ＆ホールド リターン" value={formatPct(b.bh_return_pct)} />
              <Stat
                label="差分 (実 - BH)"
                value={formatPct(b.diff_pct)}
                accent={(b.diff_pct ?? 0) >= 0 ? 'success' : 'danger'}
              />
              <Stat label="BH 時価（現時点）" value={formatYen(b.bh_value_now)} />
            </div>
          </>
        )}
      </CardBody>
    </Card>
  );
};

export default BuyAndHoldCard;
