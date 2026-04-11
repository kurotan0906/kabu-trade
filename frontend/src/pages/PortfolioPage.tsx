import { useEffect, useState } from 'react';
import { portfolioApi } from '@/services/api/portfolioApi';
import type {
  Holding,
  HoldingCreate,
  PortfolioSettings,
  PortfolioSummary,
} from '@/types/portfolio';

const PHASE_COLORS: Record<string, string> = {
  積立期: '#10b981',
  成長期: '#3b82f6',
  安定期: '#f59e0b',
};

const formatYen = (v: number | null | undefined) =>
  v == null ? '—' : `¥${Math.round(v).toLocaleString()}`;

const emptyHolding: HoldingCreate = {
  symbol: '',
  name: '',
  quantity: 0,
  avg_price: 0,
  account_type: 'general',
};

const PortfolioPage = () => {
  const [holdings, setHoldings] = useState<Holding[]>([]);
  const [summary, setSummary] = useState<PortfolioSummary | null>(null);
  const [settings, setSettings] = useState<PortfolioSettings | null>(null);
  const [loading, setLoading] = useState(true);
  const [showAdd, setShowAdd] = useState(false);
  const [draft, setDraft] = useState<HoldingCreate>(emptyHolding);

  const refresh = async () => {
    setLoading(true);
    const [h, s, st] = await Promise.all([
      portfolioApi.listHoldings(),
      portfolioApi.getSummary(),
      portfolioApi.getSettings(),
    ]);
    setHoldings(h);
    setSummary(s);
    setSettings(st);
    setLoading(false);
  };

  useEffect(() => {
    refresh();
  }, []);

  const handleAdd = async () => {
    if (!draft.symbol) return;
    await portfolioApi.createHolding(draft);
    setDraft(emptyHolding);
    setShowAdd(false);
    await refresh();
  };

  const handleDelete = async (id: number) => {
    if (!confirm('この保有銘柄を削除しますか？')) return;
    await portfolioApi.deleteHolding(id);
    await refresh();
  };

  const handleSaveSettings = async (patch: Partial<PortfolioSettings>) => {
    const updated = await portfolioApi.updateSettings(patch);
    setSettings(updated);
    await refresh();
  };

  if (loading) return <div style={{ padding: 24, color: '#9ca3af' }}>読み込み中...</div>;

  return (
    <div style={{ padding: 24, maxWidth: 1100, margin: '0 auto', color: '#e5e7eb' }}>
      <h1 style={{ fontSize: 20, fontWeight: 700, marginBottom: 16 }}>ポートフォリオ</h1>

      {/* サマリーカード */}
      <div
        style={{
          display: 'grid',
          gridTemplateColumns: 'repeat(4, 1fr)',
          gap: 12,
          marginBottom: 20,
        }}
      >
        <Card label="評価額合計" value={formatYen(summary?.total_value)} color="#a78bfa" />
        <Card
          label="含み損益"
          value={formatYen(summary?.unrealized_pl)}
          color={summary && summary.unrealized_pl >= 0 ? '#10b981' : '#ef4444'}
        />
        <Card
          label="目標進捗"
          value={summary?.progress_rate != null ? `${summary.progress_rate}%` : '目標未設定'}
          color="#60a5fa"
          subline={summary?.target_amount ? formatYen(summary.target_amount) : undefined}
        />
        <Card
          label="NISA 成長枠 残"
          value={formatYen(summary?.nisa_remaining)}
          color="#f59e0b"
        />
      </div>

      {/* フェーズ表示 */}
      {summary?.current_phase && (
        <div
          style={{
            padding: '10px 14px',
            background: '#1f2937',
            borderLeft: `3px solid ${PHASE_COLORS[summary.current_phase] ?? '#6b7280'}`,
            borderRadius: 6,
            marginBottom: 16,
            fontSize: 13,
          }}
        >
          現在フェーズ:{' '}
          <strong style={{ color: PHASE_COLORS[summary.current_phase] ?? '#fff' }}>
            {summary.current_phase}
          </strong>{' '}
          — プロファイル自動選択が有効です
        </div>
      )}

      {/* 目標設定フォーム */}
      <SettingsCard settings={settings} onSave={handleSaveSettings} />

      {/* 保有銘柄 */}
      <div style={{ marginTop: 20, display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
        <h2 style={{ fontSize: 16, fontWeight: 600 }}>保有銘柄 ({holdings.length})</h2>
        <button
          onClick={() => setShowAdd((x) => !x)}
          style={{
            padding: '6px 14px',
            background: '#7c3aed',
            color: 'white',
            border: 'none',
            borderRadius: 6,
            fontSize: 12,
            cursor: 'pointer',
          }}
        >
          {showAdd ? 'キャンセル' : '+ 銘柄追加'}
        </button>
      </div>

      {showAdd && (
        <div
          style={{
            display: 'flex',
            gap: 8,
            marginTop: 12,
            padding: 12,
            background: '#1f2937',
            borderRadius: 8,
            fontSize: 12,
          }}
        >
          <input
            placeholder="銘柄コード (例: 7203.T)"
            value={draft.symbol}
            onChange={(e) => setDraft({ ...draft, symbol: e.target.value })}
            style={inputStyle}
          />
          <input
            placeholder="名前"
            value={draft.name ?? ''}
            onChange={(e) => setDraft({ ...draft, name: e.target.value })}
            style={inputStyle}
          />
          <input
            type="number"
            placeholder="株数"
            value={draft.quantity || ''}
            onChange={(e) => setDraft({ ...draft, quantity: Number(e.target.value) })}
            style={{ ...inputStyle, width: 80 }}
          />
          <input
            type="number"
            placeholder="取得単価"
            value={draft.avg_price || ''}
            onChange={(e) => setDraft({ ...draft, avg_price: Number(e.target.value) })}
            style={{ ...inputStyle, width: 100 }}
          />
          <select
            value={draft.account_type}
            onChange={(e) => setDraft({ ...draft, account_type: e.target.value as any })}
            style={inputStyle}
          >
            <option value="general">特定/一般</option>
            <option value="nisa_growth">NISA成長枠</option>
            <option value="nisa_tsumitate">NISAつみたて</option>
          </select>
          <button onClick={handleAdd} style={{ ...inputStyle, background: '#10b981', color: 'white', cursor: 'pointer' }}>
            追加
          </button>
        </div>
      )}

      <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: 13, marginTop: 12 }}>
        <thead>
          <tr style={{ borderBottom: '1px solid #374151', color: '#6b7280' }}>
            <th style={th}>銘柄</th>
            <th style={th}>口座</th>
            <th style={th}>株数</th>
            <th style={th}>取得単価</th>
            <th style={th}>取得額</th>
            <th style={th}></th>
          </tr>
        </thead>
        <tbody>
          {holdings.map((h) => (
            <tr key={h.id} style={{ borderBottom: '1px solid #1f2937' }}>
              <td style={td}>
                <div style={{ fontWeight: 600, color: '#a78bfa' }}>{h.symbol}</div>
                <div style={{ fontSize: 11, color: '#6b7280' }}>{h.name}</div>
              </td>
              <td style={td}>
                <span
                  style={{
                    fontSize: 11,
                    padding: '2px 6px',
                    borderRadius: 10,
                    background: h.account_type.startsWith('nisa') ? '#f59e0b22' : '#37415122',
                    color: h.account_type.startsWith('nisa') ? '#f59e0b' : '#9ca3af',
                  }}
                >
                  {h.account_type === 'general' ? '一般' : h.account_type === 'nisa_growth' ? 'NISA成長' : 'NISAつみたて'}
                </span>
              </td>
              <td style={td}>{h.quantity.toLocaleString()}</td>
              <td style={td}>{formatYen(h.avg_price)}</td>
              <td style={td}>{formatYen(h.quantity * h.avg_price)}</td>
              <td style={td}>
                <button
                  onClick={() => handleDelete(h.id)}
                  style={{ fontSize: 11, color: '#ef4444', background: 'transparent', border: 'none', cursor: 'pointer' }}
                >
                  削除
                </button>
              </td>
            </tr>
          ))}
          {holdings.length === 0 && (
            <tr>
              <td colSpan={6} style={{ padding: 32, textAlign: 'center', color: '#6b7280' }}>
                保有銘柄がありません。「+ 銘柄追加」から登録してください。
              </td>
            </tr>
          )}
        </tbody>
      </table>
    </div>
  );
};

const inputStyle: React.CSSProperties = {
  padding: '6px 10px',
  background: '#374151',
  color: '#e5e7eb',
  border: '1px solid #4b5563',
  borderRadius: 6,
  fontSize: 12,
};

const th: React.CSSProperties = { padding: '8px 12px', textAlign: 'left', fontWeight: 600 };
const td: React.CSSProperties = { padding: '10px 12px' };

const Card = ({
  label,
  value,
  color,
  subline,
}: {
  label: string;
  value: string;
  color: string;
  subline?: string;
}) => (
  <div style={{ padding: 16, background: '#1f2937', borderRadius: 10 }}>
    <div style={{ fontSize: 11, color: '#6b7280', marginBottom: 6 }}>{label}</div>
    <div style={{ fontSize: 20, fontWeight: 700, color }}>{value}</div>
    {subline && <div style={{ fontSize: 11, color: '#6b7280', marginTop: 4 }}>目標: {subline}</div>}
  </div>
);

const SettingsCard = ({
  settings,
  onSave,
}: {
  settings: PortfolioSettings | null;
  onSave: (p: Partial<PortfolioSettings>) => Promise<void>;
}) => {
  const [target, setTarget] = useState(settings?.target_amount ?? '');
  const [monthly, setMonthly] = useState(settings?.monthly_investment ?? '');
  const [deadline, setDeadline] = useState(settings?.target_deadline ?? '');

  useEffect(() => {
    setTarget(settings?.target_amount ?? '');
    setMonthly(settings?.monthly_investment ?? '');
    setDeadline(settings?.target_deadline ?? '');
  }, [settings]);

  return (
    <div style={{ padding: 14, background: '#1f2937', borderRadius: 10, marginBottom: 0 }}>
      <div style={{ fontSize: 12, color: '#6b7280', marginBottom: 8 }}>目標設定</div>
      <div style={{ display: 'flex', gap: 8, fontSize: 12, flexWrap: 'wrap' }}>
        <label>
          目標額 (円){' '}
          <input
            type="number"
            value={target ?? ''}
            onChange={(e) => setTarget(e.target.value ? Number(e.target.value) : '')}
            style={{ ...inputStyle, width: 140 }}
          />
        </label>
        <label>
          毎月積立 (円){' '}
          <input
            type="number"
            value={monthly ?? ''}
            onChange={(e) => setMonthly(e.target.value ? Number(e.target.value) : '')}
            style={{ ...inputStyle, width: 120 }}
          />
        </label>
        <label>
          達成期限{' '}
          <input
            type="date"
            value={deadline ?? ''}
            onChange={(e) => setDeadline(e.target.value)}
            style={inputStyle}
          />
        </label>
        <button
          onClick={() =>
            onSave({
              target_amount: target === '' ? null : Number(target),
              monthly_investment: monthly === '' ? null : Number(monthly),
              target_deadline: deadline || null,
            })
          }
          style={{ ...inputStyle, background: '#3b82f6', color: 'white', cursor: 'pointer' }}
        >
          保存
        </button>
      </div>
    </div>
  );
};

export default PortfolioPage;
