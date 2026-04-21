import { Card, CardBody, Stat, EmptyState } from '@/components/ui';
import type { IndicatorProps } from './registry';

const formatYen = (v: number | null | undefined) =>
  v == null ? '—' : `¥${Math.round(v).toLocaleString()}`;
const formatPct = (v: number | null | undefined) =>
  v == null ? '—' : `${v >= 0 ? '+' : ''}${v.toFixed(2)}%`;

export const OpenPositionCard = ({ data }: IndicatorProps) => {
  const p = data.open_position;
  return (
    <Card>
      <CardBody>
        <h3 className="mb-3 text-base font-semibold text-slate-900">現在保有の健康度</h3>
        {!p ? (
          <EmptyState title="現在この銘柄を保有していません" description="" />
        ) : (
          <div className="grid gap-3 grid-cols-2 md:grid-cols-4">
            <Stat label="保有数量" value={p.quantity.toLocaleString()} />
            <Stat label="平均取得単価" value={formatYen(p.avg_price)} />
            <Stat label="現在値" value={formatYen(p.current_price)} />
            <Stat
              label="含み損益"
              value={formatYen(p.unrealized_pl)}
              accent={(p.unrealized_pl ?? 0) >= 0 ? 'success' : 'danger'}
              hint={formatPct(p.unrealized_pl_pct)}
            />
            <Stat label="エントリー日" value={new Date(p.entry_date).toLocaleDateString()} />
            <Stat label="保有日数" value={`${p.holding_days}日`} />
            <Stat label="MFE (最大含み益)" value={formatYen(p.mfe)} accent="success" />
            <Stat label="MAE (最大含み損)" value={formatYen(p.mae)} accent="danger" />
          </div>
        )}
      </CardBody>
    </Card>
  );
};

export default OpenPositionCard;
