import { useState, useEffect } from 'react';
import { scoresApi } from '@/services/api/scoresApi';
import type { AnalysisAxes, AnalysisAxis } from '@/types/stockScore';

interface Props {
  symbol: string;
}

const AXIS_FILLS: Record<string, string> = {
  ファンダメンタル: 'fill-blue-500',
  テクニカル: 'fill-emerald-500',
  黒点子: 'fill-violet-500',
  チャート分析: 'fill-amber-500',
  TradingView: 'fill-orange-500',
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

const ScoreBar = ({ score, fillClass, textClass }: { score: number; fillClass: string; textClass: string }) => {
  const w = Math.min(100, Math.max(0, score));
  return (
    <div className="mt-2 flex items-center gap-2">
      <svg className="h-1.5 min-w-0 flex-1" viewBox="0 0 100 4" preserveAspectRatio="none" aria-hidden>
        <rect className="fill-slate-200" width={100} height={4} rx={2} />
        <rect className={fillClass} width={w} height={4} rx={2} />
      </svg>
      <span className={`min-w-[36px] text-sm font-bold ${textClass}`}>{Math.round(score)}</span>
    </div>
  );
};

const AxisCard = ({ axis }: { axis: AnalysisAxis }) => {
  const [expanded, setExpanded] = useState(false);
  const fillClass = AXIS_FILLS[axis.name] ?? 'fill-slate-400';
  const borderClass = AXIS_BORDER[axis.name] ?? 'border-t-slate-400';
  const textClass = AXIS_TEXT[axis.name] ?? 'text-slate-500';

  return (
    <div className={`rounded-lg border border-slate-200 border-t-[3px] bg-white px-4 py-3.5 ${borderClass}`}>
      <div className="text-[11px] font-bold uppercase tracking-wider text-slate-500">
        {axis.name}
      </div>

      {axis.score !== null ? (
        <ScoreBar score={axis.score} fillClass={fillClass} textClass={textClass} />
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
      <div className="grid grid-cols-[repeat(auto-fit,minmax(200px,1fr))] gap-3">
        {axes.axes.map((axis) => (
          <AxisCard key={axis.name} axis={axis} />
        ))}
      </div>
    </div>
  );
};

export default AnalysisAxesPanel;
