import { useEffect, useState } from 'react';
import { advisorApi } from '@/services/api/advisorApi';
import type { HistoryEntry } from '@/types/advisor';
import {
  PageHeader,
  Card,
  CardBody,
  Table,
  Thead,
  Tbody,
  Tr,
  Th,
  Td,
  EmptyState,
} from '@/components/ui';

const formatYen = (v: unknown) => {
  const n = Number(v);
  if (Number.isNaN(n)) return '—';
  return `¥${Math.round(n).toLocaleString()}`;
};

const AnalysisHistoryPage = () => {
  const [entries, setEntries] = useState<HistoryEntry[] | null>(null);

  useEffect(() => {
    advisorApi.listHistory().then(setEntries).catch(() => setEntries([]));
  }, []);

  if (entries === null) {
    return (
      <Card>
        <CardBody className="text-sm text-slate-500">読み込み中...</CardBody>
      </Card>
    );
  }

  return (
    <>
      <PageHeader title="シミュレーション履歴" description="過去の将来価値計算ログ" />

      {entries.length === 0 ? (
        <EmptyState
          title="履歴がありません"
          description="シミュレータから計算を実行すると記録されます"
        />
      ) : (
        <>
          <div className="hidden md:block">
            <Table>
              <Thead>
                <Tr>
                  <Th>日時</Th>
                  <Th>現在額</Th>
                  <Th>積立</Th>
                  <Th>年利</Th>
                  <Th>期間</Th>
                  <Th>最終評価額</Th>
                  <Th>運用益</Th>
                </Tr>
              </Thead>
              <Tbody>
                {entries.map((e) => {
                  const i = e.input_json as Record<string, number>;
                  const r = e.result_json as Record<string, number>;
                  return (
                    <Tr key={e.id}>
                      <Td className="text-slate-500">
                        {new Date(e.created_at).toLocaleString('ja-JP')}
                      </Td>
                      <Td className="tabular-nums">{formatYen(i.pv)}</Td>
                      <Td className="tabular-nums">{formatYen(i.monthly_investment)}/月</Td>
                      <Td className="tabular-nums">{((i.annual_rate ?? 0) * 100).toFixed(2)}%</Td>
                      <Td>{i.years}年</Td>
                      <Td className="font-semibold tabular-nums text-brand-600">
                        {formatYen(r.final_value)}
                      </Td>
                      <Td
                        className={`font-semibold tabular-nums ${(r.total_gain ?? 0) >= 0 ? 'text-emerald-600' : 'text-rose-600'}`}
                      >
                        {formatYen(r.total_gain)}
                      </Td>
                    </Tr>
                  );
                })}
              </Tbody>
            </Table>
          </div>

          <div className="space-y-3 md:hidden">
            {entries.map((e) => {
              const i = e.input_json as Record<string, number>;
              const r = e.result_json as Record<string, number>;
              return (
                <Card key={e.id}>
                  <CardBody className="space-y-1.5">
                    <div className="text-xs text-slate-500">
                      {new Date(e.created_at).toLocaleString('ja-JP')}
                    </div>
                    <div className="text-lg font-bold tabular-nums text-brand-600">
                      {formatYen(r.final_value)}
                    </div>
                    <div className="text-xs text-slate-600">
                      {formatYen(i.pv)} + {formatYen(i.monthly_investment)}/月 × {i.years}年 @{' '}
                      {((i.annual_rate ?? 0) * 100).toFixed(1)}%
                    </div>
                    <div
                      className={`text-xs font-semibold ${(r.total_gain ?? 0) >= 0 ? 'text-emerald-600' : 'text-rose-600'}`}
                    >
                      運用益 {formatYen(r.total_gain)}
                    </div>
                  </CardBody>
                </Card>
              );
            })}
          </div>
        </>
      )}
    </>
  );
};

export default AnalysisHistoryPage;
