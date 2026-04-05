import { useState, useEffect } from 'react';
import { scoresApi } from '@/services/api/scoresApi';
import type { AnalysisAxes, AnalysisAxis } from '@/types/stockScore';

interface Props {
  symbol: string;
}

const AXIS_COLORS: Record<string, string> = {
  'ファンダメンタル': '#3b82f6',
  'テクニカル': '#10b981',
  '黒点子': '#8b5cf6',
  'チャート分析': '#f59e0b',
};

const ScoreBar = ({ score, color }: { score: number; color: string }) => (
  <div style={{ display: 'flex', alignItems: 'center', gap: 8, marginTop: 8 }}>
    <div style={{ flex: 1, height: 6, background: '#374151', borderRadius: 3, overflow: 'hidden' }}>
      <div style={{ width: `${score}%`, height: '100%', background: color, borderRadius: 3 }} />
    </div>
    <span style={{ fontSize: 13, fontWeight: 700, color, minWidth: 36 }}>{Math.round(score)}</span>
  </div>
);

const AxisCard = ({ axis }: { axis: AnalysisAxis }) => {
  const [expanded, setExpanded] = useState(false);
  const color = AXIS_COLORS[axis.name] ?? '#6b7280';

  return (
    <div
      style={{
        border: `1px solid #374151`,
        borderRadius: 10,
        padding: '14px 16px',
        background: '#1f2937',
        borderTop: `3px solid ${color}`,
      }}
    >
      <div style={{ fontSize: 11, fontWeight: 700, textTransform: 'uppercase', color: '#9ca3af', letterSpacing: '0.5px' }}>
        {axis.name}
      </div>

      {axis.score !== null ? (
        <ScoreBar score={axis.score} color={color} />
      ) : axis.recommendation ? (
        <div style={{ marginTop: 8, fontSize: 18, fontWeight: 700, color }}>
          {axis.recommendation.toUpperCase()}
        </div>
      ) : (
        <div style={{ marginTop: 8, fontSize: 13, color: '#6b7280' }}>データなし</div>
      )}

      <button
        onClick={() => setExpanded(!expanded)}
        style={{
          marginTop: 10, fontSize: 11, color: '#6b7280', background: 'none',
          border: 'none', cursor: 'pointer', padding: 0,
        }}
      >
        {expanded ? '▲ 閉じる' : '▼ 詳細'}
      </button>

      {expanded && (
        <div style={{ marginTop: 8, borderTop: '1px solid #374151', paddingTop: 8 }}>
          {Object.entries(axis.detail).map(([key, value]) =>
            value !== null && value !== undefined && typeof value !== 'object' ? (
              <div key={key} style={{ display: 'flex', justifyContent: 'space-between', padding: '2px 0', fontSize: 12 }}>
                <span style={{ color: '#9ca3af' }}>{key}</span>
                <span style={{ fontWeight: 600, color: value === true ? '#34d399' : value === false ? '#f87171' : '#e5e7eb' }}>
                  {typeof value === 'boolean' ? (value ? '✓' : '✗') : String(value)}
                </span>
              </div>
            ) : null
          )}
        </div>
      )}
    </div>
  );
};

const AnalysisAxesPanel = ({ symbol }: Props) => {
  const [axes, setAxes] = useState<AnalysisAxes | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    scoresApi.getAxes(symbol)
      .then(setAxes)
      .catch(() => setAxes(null))
      .finally(() => setLoading(false));
  }, [symbol]);

  if (loading) return <div style={{ color: '#6b7280', fontSize: 13 }}>分析軸を読み込み中...</div>;
  if (!axes || axes.axes.length === 0) return <div style={{ color: '#6b7280', fontSize: 13 }}>スコアデータがありません（バッチ未実行）</div>;

  return (
    <div style={{ marginTop: 16 }}>
      <h3 style={{ fontSize: 13, fontWeight: 700, textTransform: 'uppercase', letterSpacing: '0.5px', color: '#9ca3af', marginBottom: 12 }}>
        多軸分析
      </h3>
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))', gap: 12 }}>
        {axes.axes.map((axis) => (
          <AxisCard key={axis.name} axis={axis} />
        ))}
      </div>
    </div>
  );
};

export default AnalysisAxesPanel;
