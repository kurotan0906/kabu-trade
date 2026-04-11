import { useState } from 'react';
import { advisorApi } from '@/services/api/advisorApi';
import FutureValueChart from '@/components/advisor/FutureValueChart';
import type { SimulateResponse } from '@/types/advisor';

const formatYen = (v: number) => `¥${Math.round(v).toLocaleString()}`;

const SimulatorPage = () => {
  const [pv, setPv] = useState(1_000_000);
  const [monthly, setMonthly] = useState(50_000);
  const [rate, setRate] = useState(5.0);
  const [years, setYears] = useState(20);
  const [result, setResult] = useState<SimulateResponse | null>(null);
  const [loading, setLoading] = useState(false);

  // 必要年利計算
  const [goal, setGoal] = useState(20_000_000);
  const [requiredRate, setRequiredRate] = useState<number | null>(null);
  const [requiredMsg, setRequiredMsg] = useState<string>('');

  const handleSimulate = async () => {
    setLoading(true);
    try {
      const res = await advisorApi.simulate({
        pv,
        monthly_investment: monthly,
        annual_rate: rate / 100,
        years,
      });
      setResult(res);
    } finally {
      setLoading(false);
    }
  };

  const handleRequiredRate = async () => {
    const res = await advisorApi.requiredRate({
      goal,
      pv,
      n_months: years * 12,
      monthly_investment: monthly,
    });
    setRequiredRate(res.annual_rate_percent);
    setRequiredMsg(
      res.annual_rate_percent == null
        ? '計算不能（pv または期間が不正です）'
        : res.annual_rate_percent > 200
          ? '実質到達不可能な目標です'
          : `必要年利: ${res.annual_rate_percent}%`
    );
  };

  return (
    <div style={{ padding: 24, maxWidth: 1000, margin: '0 auto', color: '#e5e7eb' }}>
      <h1 style={{ fontSize: 20, fontWeight: 700, marginBottom: 16 }}>将来価値シミュレータ</h1>

      {/* 入力 */}
      <div style={{ padding: 16, background: '#1f2937', borderRadius: 10, marginBottom: 16 }}>
        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(4, 1fr)', gap: 12 }}>
          <Field label="現在評価額 (円)" value={pv} onChange={setPv} />
          <Field label="毎月積立 (円)" value={monthly} onChange={setMonthly} />
          <Field label="想定年利 (%)" value={rate} onChange={setRate} step={0.1} />
          <Field label="期間 (年)" value={years} onChange={setYears} />
        </div>
        <button
          onClick={handleSimulate}
          disabled={loading}
          style={{
            marginTop: 12,
            padding: '8px 20px',
            background: '#7c3aed',
            color: 'white',
            border: 'none',
            borderRadius: 6,
            cursor: 'pointer',
            fontSize: 13,
            fontWeight: 600,
          }}
        >
          {loading ? '計算中...' : '▶ シミュレーション実行'}
        </button>
      </div>

      {result && (
        <>
          <div
            style={{
              display: 'grid',
              gridTemplateColumns: 'repeat(3, 1fr)',
              gap: 12,
              marginBottom: 16,
            }}
          >
            <Summary label="最終評価額" value={formatYen(result.final_value)} color="#a78bfa" />
            <Summary label="拠出累計" value={formatYen(result.total_contributed)} color="#60a5fa" />
            <Summary
              label="運用益"
              value={formatYen(result.total_gain)}
              color={result.total_gain >= 0 ? '#10b981' : '#ef4444'}
            />
          </div>
          <FutureValueChart data={result.timeseries} />
        </>
      )}

      {/* 必要年利計算 */}
      <div style={{ marginTop: 24, padding: 16, background: '#1f2937', borderRadius: 10 }}>
        <div style={{ fontSize: 14, fontWeight: 600, marginBottom: 10 }}>必要年利逆算</div>
        <div style={{ display: 'flex', gap: 12, alignItems: 'center' }}>
          <Field label="目標額 (円)" value={goal} onChange={setGoal} />
          <button
            onClick={handleRequiredRate}
            style={{
              padding: '8px 16px',
              background: '#3b82f6',
              color: 'white',
              border: 'none',
              borderRadius: 6,
              cursor: 'pointer',
              fontSize: 12,
            }}
          >
            計算
          </button>
          {requiredMsg && (
            <span
              style={{
                fontSize: 13,
                color: requiredRate != null && requiredRate <= 10 ? '#10b981' : '#f59e0b',
              }}
            >
              {requiredMsg}
            </span>
          )}
        </div>
      </div>
    </div>
  );
};

const Field = ({
  label,
  value,
  onChange,
  step = 1,
}: {
  label: string;
  value: number;
  onChange: (v: number) => void;
  step?: number;
}) => (
  <label style={{ display: 'flex', flexDirection: 'column', fontSize: 11, color: '#9ca3af' }}>
    {label}
    <input
      type="number"
      value={value}
      step={step}
      onChange={(e) => onChange(Number(e.target.value))}
      style={{
        marginTop: 4,
        padding: '6px 10px',
        background: '#374151',
        color: '#e5e7eb',
        border: '1px solid #4b5563',
        borderRadius: 6,
        fontSize: 13,
      }}
    />
  </label>
);

const Summary = ({ label, value, color }: { label: string; value: string; color: string }) => (
  <div style={{ padding: 14, background: '#0f172a', borderRadius: 8 }}>
    <div style={{ fontSize: 11, color: '#6b7280' }}>{label}</div>
    <div style={{ fontSize: 20, fontWeight: 700, color, marginTop: 4 }}>{value}</div>
  </div>
);

export default SimulatorPage;
