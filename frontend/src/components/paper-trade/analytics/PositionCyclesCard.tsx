import { Card, CardBody, Table, Thead, Tbody, Tr, Th, Td, EmptyState } from '@/components/ui';
import type { IndicatorProps } from './registry';

const formatYen = (v: number) => `¥${Math.round(v).toLocaleString()}`;
const formatPct = (v: number) => `${v >= 0 ? '+' : ''}${v.toFixed(2)}%`;
const formatDate = (iso: string) => new Date(iso).toLocaleDateString();

export const PositionCyclesCard = ({ data }: IndicatorProps) => {
  return (
    <Card>
      <CardBody>
        <h3 className="mb-3 text-base font-semibold text-slate-900">
          ポジションサイクル ({data.position_cycles.length})
        </h3>
        {data.position_cycles.length === 0 ? (
          <EmptyState title="クローズしたサイクルがありません" description="" />
        ) : (
          <Table>
            <Thead>
              <Tr>
                <Th>入口</Th>
                <Th>出口</Th>
                <Th className="text-right">数量</Th>
                <Th className="text-right">入口価格</Th>
                <Th className="text-right">出口価格</Th>
                <Th className="text-right">保有日数</Th>
                <Th className="text-right">損益</Th>
                <Th className="text-right">リターン</Th>
              </Tr>
            </Thead>
            <Tbody>
              {data.position_cycles.map((c, i) => (
                <Tr key={i}>
                  <Td>{formatDate(c.entry_date)}</Td>
                  <Td>{formatDate(c.exit_date)}</Td>
                  <Td className="text-right">{c.quantity.toLocaleString()}</Td>
                  <Td className="text-right">{formatYen(c.entry_price)}</Td>
                  <Td className="text-right">{formatYen(c.exit_price)}</Td>
                  <Td className="text-right">{c.holding_days}日</Td>
                  <Td className={'text-right ' + (c.pl >= 0 ? 'text-emerald-700' : 'text-rose-700')}>
                    {formatYen(c.pl)}
                  </Td>
                  <Td className="text-right">{formatPct(c.return_pct)}</Td>
                </Tr>
              ))}
            </Tbody>
          </Table>
        )}
      </CardBody>
    </Card>
  );
};

export default PositionCyclesCard;
