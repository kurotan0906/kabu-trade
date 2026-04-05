import { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { scoresApi } from '@/services/api/scoresApi';
import type { StockScore, BatchStatus } from '@/types/stockScore';

const RATING_COLORS: Record<string, string> = {
  '強い買い': '#3b82f6',
  '買い': '#10b981',
  '中立': '#9ca3af',
  '売り': '#f59e0b',
  '強い売り': '#ef4444',
};

const ScoreBar = ({ score }: { score: number | null }) => {
  if (score === null) return <span style={{ color: '#4b5563' }}>—</span>;
  const pct = Math.min(100, Math.max(0, score));
  return (
    <div style={{ display: 'flex', alignItems: 'center', gap: 6 }}>
      <div style={{ width: 80, height: 4, background: '#374151', borderRadius: 2, overflow: 'hidden' }}>
        <div style={{ width: `${pct}%`, height: '100%', background: 'linear-gradient(90deg,#3b82f6,#8b5cf6)', borderRadius: 2 }} />
      </div>
      <span style={{ fontSize: 13, fontWeight: 700, color: '#a78bfa', minWidth: 28 }}>{Math.round(pct)}</span>
    </div>
  );
};

const StockRankingPage = () => {
  const [scores, setScores] = useState<StockScore[]>([]);
  const [batchStatus, setBatchStatus] = useState<BatchStatus | null>(null);
  const [loading, setLoading] = useState(true);
  const [triggering, setTriggering] = useState(false);
  const navigate = useNavigate();

  useEffect(() => {
    Promise.all([
      scoresApi.listScores('total_score', 100),
      scoresApi.getBatchStatus(),
    ]).then(([s, b]) => {
      setScores(s);
      setBatchStatus(b);
    }).finally(() => setLoading(false));
  }, []);

  const handleTriggerBatch = async () => {
    setTriggering(true);
    try {
      await scoresApi.triggerBatch();
      alert('バッチスコアリングを開始しました');
    } catch {
      alert('エラーが発生しました');
    } finally {
      setTriggering(false);
    }
  };

  if (loading) return <div style={{ padding: 24, color: '#9ca3af' }}>読み込み中...</div>;

  return (
    <div style={{ padding: 24, maxWidth: 1200, margin: '0 auto' }}>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 16 }}>
        <div>
          <h1 style={{ fontSize: 20, fontWeight: 700 }}>銘柄スコアランキング</h1>
          {batchStatus && (
            <div style={{ fontSize: 12, color: '#6b7280', marginTop: 4 }}>
              最終更新: {batchStatus.finished_at ? new Date(batchStatus.finished_at).toLocaleString('ja-JP') : '未実行'}
              {batchStatus.status === 'running' && <span style={{ color: '#f59e0b', marginLeft: 8 }}>実行中...</span>}
            </div>
          )}
        </div>
        <button
          onClick={handleTriggerBatch}
          disabled={triggering || batchStatus?.status === 'running'}
          style={{
            padding: '8px 16px', background: '#7c3aed', color: 'white',
            border: 'none', borderRadius: 8, fontWeight: 600, cursor: 'pointer', fontSize: 13,
          }}
        >
          {triggering ? '開始中...' : '▶ スコアリング実行'}
        </button>
      </div>

      {scores.length === 0 ? (
        <div style={{ padding: 48, textAlign: 'center', color: '#6b7280' }}>
          スコアデータがありません。「スコアリング実行」でバッチを開始してください。
        </div>
      ) : (
        <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: 13 }}>
          <thead>
            <tr style={{ borderBottom: '1px solid #374151' }}>
              <th style={{ padding: '8px 12px', textAlign: 'left', color: '#6b7280', fontWeight: 600 }}>#</th>
              <th style={{ padding: '8px 12px', textAlign: 'left', color: '#6b7280', fontWeight: 600 }}>銘柄</th>
              <th style={{ padding: '8px 12px', textAlign: 'left', color: '#a78bfa', fontWeight: 600 }}>総合スコア ▼</th>
              <th style={{ padding: '8px 12px', textAlign: 'left', color: '#6b7280', fontWeight: 600 }}>レーティング</th>
              <th style={{ padding: '8px 12px', textAlign: 'left', color: '#6b7280', fontWeight: 600 }}>ファンダ</th>
              <th style={{ padding: '8px 12px', textAlign: 'left', color: '#6b7280', fontWeight: 600 }}>テクニカル</th>
              <th style={{ padding: '8px 12px', textAlign: 'left', color: '#6b7280', fontWeight: 600 }}>黒点子</th>
              <th style={{ padding: '8px 12px', textAlign: 'left', color: '#6b7280', fontWeight: 600 }}></th>
            </tr>
          </thead>
          <tbody>
            {scores.map((s, i) => (
              <tr
                key={s.id}
                style={{ borderBottom: '1px solid #1f2937', cursor: 'pointer' }}
                onMouseEnter={(e) => (e.currentTarget.style.background = '#1f2937')}
                onMouseLeave={(e) => (e.currentTarget.style.background = '')}
              >
                <td style={{ padding: '10px 12px', color: '#6b7280' }}>{i + 1}</td>
                <td style={{ padding: '10px 12px' }}>
                  <div style={{ fontWeight: 600, color: '#a78bfa' }}>{s.symbol}</div>
                  <div style={{ fontSize: 11, color: '#6b7280' }}>{s.name}</div>
                </td>
                <td style={{ padding: '10px 12px' }}><ScoreBar score={s.total_score} /></td>
                <td style={{ padding: '10px 12px' }}>
                  {s.rating ? (
                    <span style={{
                      padding: '2px 8px', borderRadius: 12, fontSize: 11, fontWeight: 600,
                      background: `${RATING_COLORS[s.rating] ?? '#6b7280'}22`,
                      color: RATING_COLORS[s.rating] ?? '#6b7280',
                    }}>{s.rating}</span>
                  ) : '—'}
                </td>
                <td style={{ padding: '10px 12px', color: '#60a5fa', fontWeight: 600 }}>
                  {s.fundamental_score !== null ? Math.round(s.fundamental_score) : '—'}
                </td>
                <td style={{ padding: '10px 12px', color: '#34d399', fontWeight: 600 }}>
                  {s.technical_score !== null ? Math.round(s.technical_score) : '—'}
                </td>
                <td style={{ padding: '10px 12px', color: '#a78bfa', fontWeight: 600 }}>
                  {s.kurotenko_score !== null ? `${Math.round(s.kurotenko_score)}%` : '—'}
                </td>
                <td style={{ padding: '10px 12px' }}>
                  <button
                    onClick={() => navigate(`/stocks/${s.symbol.replace('.T', '')}`)}
                    style={{ fontSize: 12, color: '#9ca3af', background: '#374151', border: 'none', borderRadius: 6, padding: '4px 10px', cursor: 'pointer' }}
                  >
                    詳細 →
                  </button>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      )}
    </div>
  );
};

export default StockRankingPage;
