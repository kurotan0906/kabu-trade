import { Card, CardBody, Stat } from '@/components/ui';
import type { IndicatorProps } from './registry';

const formatYen = (v: number | null | undefined) =>
  v == null ? '—' : `¥${Math.round(v).toLocaleString()}`;
const formatPct = (v: number | null | undefined) =>
  v == null ? '—' : `${v >= 0 ? '+' : ''}${v.toFixed(2)}%`;
const formatNum = (v: number | null | undefined, digits = 2) =>
  v == null ? '—' : v.toFixed(digits);

export const SummaryCard = ({ data }: IndicatorProps) => {
  const s = data.summary;
  return (
    <Card>
      <CardBody>
        <h3 className="mb-3 text-base font-semibold text-slate-900">サマリ指標</h3>
        <div className="grid gap-3 grid-cols-2 md:grid-cols-4">
          <Stat label="合計損益" value={formatYen(s.total_pl)} accent={s.total_pl >= 0 ? 'success' : 'danger'} />
          <Stat label="リターン" value={formatPct(s.return_pct)} accent={(s.return_pct ?? 0) >= 0 ? 'success' : 'danger'} />
          <Stat label="実現損益" value={formatYen(s.realized_pl)} accent={s.realized_pl >= 0 ? 'success' : 'danger'} />
          <Stat label="含み損益" value={formatYen(s.unrealized_pl)} accent={s.unrealized_pl >= 0 ? 'success' : 'danger'} />
          <Stat label="取引回数" value={`${s.trade_count} (買${s.buy_count}/売${s.sell_count})`} />
          <Stat label="勝率" value={s.win_rate == null ? '—' : `${(s.win_rate * 100).toFixed(1)}%`} hint={`勝${s.win_count}/負${s.loss_count}`} />
          <Stat label="平均保有日数" value={s.avg_holding_days == null ? '—' : `${formatNum(s.avg_holding_days, 1)}日`} />
          <Stat label="最大利益取引" value={formatYen(s.best_trade_pl)} accent="success" />
          <Stat label="最大損失取引" value={formatYen(s.worst_trade_pl)} accent={(s.worst_trade_pl ?? 0) < 0 ? 'danger' : undefined} />
          <Stat label="プロフィットファクター" value={formatNum(s.profit_factor, 2)} />
          <Stat label="期待値" value={formatYen(s.expectancy)} />
        </div>
      </CardBody>
    </Card>
  );
};

export default SummaryCard;
