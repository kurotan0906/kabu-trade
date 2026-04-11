import { useEffect, useState } from 'react';
import { advisorApi } from '@/services/api/advisorApi';
import type { HistoryEntry } from '@/types/advisor';

const formatYen = (v: unknown) => {
  const n = Number(v);
  if (Number.isNaN(n)) return '—';
  return `¥${Math.round(n).toLocaleString()}`;
};

const AnalysisHistoryPage = () => {
  const [entries, setEntries] = useState<HistoryEntry[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    advisorApi
      .listHistory()
      .then(setEntries)
      .finally(() => setLoading(false));
  }, []);

  if (loading) return <div style={{ padding: 24, color: '#9ca3af' }}>読み込み中...</div>;

  return (
    <div style={{ padding: 24, maxWidth: 1000, margin: '0 auto', color: '#e5e7eb' }}>
      <h1 style={{ fontSize: 20, fontWeight: 700, marginBottom: 16 }}>シミュレーション履歴</h1>
      {entries.length === 0 ? (
        <div style={{ padding: 48, textAlign: 'center', color: '#6b7280' }}>
          履歴がありません。シミュレータから計算を実行すると記録されます。
        </div>
      ) : (
        <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: 13 }}>
          <thead>
            <tr style={{ borderBottom: '1px solid #374151', color: '#6b7280' }}>
              <th style={th}>日時</th>
              <th style={th}>現在額</th>
              <th style={th}>積立</th>
              <th style={th}>年利</th>
              <th style={th}>期間</th>
              <th style={th}>最終評価額</th>
              <th style={th}>運用益</th>
            </tr>
          </thead>
          <tbody>
            {entries.map((e) => {
              const i = e.input_json as Record<string, number>;
              const r = e.result_json as Record<string, number>;
              return (
                <tr key={e.id} style={{ borderBottom: '1px solid #1f2937' }}>
                  <td style={td}>{new Date(e.created_at).toLocaleString('ja-JP')}</td>
                  <td style={td}>{formatYen(i.pv)}</td>
                  <td style={td}>{formatYen(i.monthly_investment)}/月</td>
                  <td style={td}>{((i.annual_rate ?? 0) * 100).toFixed(2)}%</td>
                  <td style={td}>{i.years}年</td>
                  <td style={{ ...td, color: '#a78bfa', fontWeight: 600 }}>{formatYen(r.final_value)}</td>
                  <td
                    style={{
                      ...td,
                      color: (r.total_gain ?? 0) >= 0 ? '#10b981' : '#ef4444',
                      fontWeight: 600,
                    }}
                  >
                    {formatYen(r.total_gain)}
                  </td>
                </tr>
              );
            })}
          </tbody>
        </table>
      )}
    </div>
  );
};

const th: React.CSSProperties = { padding: '8px 12px', textAlign: 'left', fontWeight: 600 };
const td: React.CSSProperties = { padding: '10px 12px' };

export default AnalysisHistoryPage;
