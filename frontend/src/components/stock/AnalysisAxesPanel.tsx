import { useState, useEffect } from 'react';
import { scoresApi } from '@/services/api/scoresApi';
import type { AnalysisAxes, AnalysisAxis } from '@/types/stockScore';

interface Props {
  symbol: string;
}

const AXIS_COLORS: Record<string, string> = {
  ファンダメンタル: 'bg-blue-500',
  テクニカル: 'bg-emerald-500',
  黒点子: 'bg-violet-500',
  チャート分析: 'bg-amber-500',
  TradingView: 'bg-orange-500',
};

const AXIS_BORDER: Record<string, string> = {
  ファンダメンタル: 'border-t-blue-500',
  テクニカル: 'border-t-emerald-500',
  黒点子: 'border-t-violet-500',
  チャート分析: 'border-t-amber-500',
  TradingView: 'border-t-orange-500',
};

const AXIS_TEXT: Record<string, string> = {
  ファンダメンタル: 'text-blue-600',
  テクニカル: 'text-emerald-600',
  黒点子: 'text-violet-600',
  チャート分析: 'text-amber-600',
  TradingView: 'text-orange-600',
};

const ScoreBar = ({ score, barClass, textClass }: { score: number; barClass: string; textClass: string }) => (
  <div className="mt-2 flex items-center gap-2">
    <div className="h-1.5 flex-1 overflow-hidden rounded bg-slate-200">
      <div className={`h-full rounded ${barClass}`} style={{ width: `${score}%` }} />
    </div>
    <span className={`min-w-[36px] text-sm font-bold ${textClass}`}>{Math.round(score)}</span>
  </div>
);

const AxisCard = ({ axis }: { axis: AnalysisAxis }) => {
  const [expanded, setExpanded] = useState(false);
  const barClass = AXIS_COLORS[axis.name] ?? 'bg-slate-400';
  const borderClass = AXIS_BORDER[axis.name] ?? 'border-t-slate-400';
  const textClass = AXIS_TEXT[axis.name] ?? 'text-slate-500';

  return (
    <div className={`rounded-lg border border-slate-200 border-t-[3px] bg-white px-4 py-3.5 ${borderClass}`}>
      <div className="text-[11px] font-bold uppercase tracking-wider text-slate-500">
        {axis.name}
      </div>

      {axis.score !== null ? (
        <ScoreBar score={axis.score} barClass={barClass} textClass={textClass} />
      ) : axis.recommendation ? (
        <div className={`mt-2 text-lg font-bold ${textClass}`}>
          {axis.recommendation.toUpperCase()}
        </div>
      ) : (
        <div className="mt-2 text-sm text-slate-500">データなし</div>
      )}

      <button
        onClick={() => setExpanded(!expanded)}
        className="mt-2.5 cursor-pointer border-none bg-transparent p-0 text-[11px] text-slate-500"
      >
        {expanded ? '▲ 閉じる' : '▼ 詳細'}
      </button>

      {expanded && (
        <div className="mt-2 border-t border-slate-200 pt-2">
          {Object.entries(axis.detail).map(([key, value]) =>
            value !== null && value !== undefined && typeof value !== 'object' ? (
              <div key={key} className="flex justify-between py-0.5 text-xs">
                <span className="text-slate-500">{key}</span>
                <span
                  className={`font-semibold ${
                    value === true
                      ? 'text-emerald-600'
                      : value === false
                        ? 'text-rose-500'
                        : 'text-slate-900'
                  }`}
                >
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
    scoresApi
      .getAxes(symbol)
      .then(setAxes)
      .catch(() => setAxes(null))
      .finally(() => setLoading(false));
  }, [symbol]);

  if (loading) return <div className="text-sm text-slate-500">分析軸を読み込み中...</div>;
  if (!axes || axes.axes.length === 0)
    return <div className="text-sm text-slate-500">スコアデータがありません（バッチ未実行）</div>;

  return (
    <div className="mt-4">
      <h3 className="mb-3 text-xs font-bold uppercase tracking-wider text-slate-500">多軸分析</h3>
      <div className="grid gap-3" style={{ gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))' }}>
        {axes.axes.map((axis) => (
          <AxisCard key={axis.name} axis={axis} />
        ))}
      </div>
    </div>
  );
};

export default AnalysisAxesPanel;
