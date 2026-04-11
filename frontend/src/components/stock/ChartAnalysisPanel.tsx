import type { ChartAnalysis } from '@/types/chartAnalysis';

interface ChartAnalysisPanelProps {
  analysis: ChartAnalysis;
}

const trendLabel: Record<string, string> = {
  bullish: '強気 (Bullish)',
  bearish: '弱気 (Bearish)',
  neutral: '中立 (Neutral)',
};

const trendClass: Record<string, string> = {
  bullish: 'text-emerald-600',
  bearish: 'text-rose-600',
  neutral: 'text-amber-600',
};

const recommendationLabel: Record<string, string> = {
  buy: '買い (Buy)',
  sell: '売り (Sell)',
  hold: '様子見 (Hold)',
};

const recommendationClass: Record<string, string> = {
  buy: 'text-emerald-600',
  sell: 'text-rose-600',
  hold: 'text-amber-600',
};

const ChartAnalysisPanel = ({ analysis }: ChartAnalysisPanelProps) => {
  const formattedDate = new Date(analysis.created_at).toLocaleString('ja-JP');

  return (
    <div className="mt-4 rounded-lg border border-slate-200 bg-white p-6">
      <div className="mb-4 flex items-center justify-between">
        <h3 className="m-0 text-base font-semibold text-slate-900">AI チャート分析</h3>
        <span className="text-xs text-slate-500">最終更新: {formattedDate}</span>
      </div>

      <div className="mb-4 grid grid-cols-2 gap-4">
        <div className="rounded bg-slate-100 p-4">
          <div className="text-xs text-slate-500">トレンド</div>
          <div
            className={`font-bold ${trendClass[analysis.trend] ?? 'text-slate-500'}`}
          >
            {trendLabel[analysis.trend] ?? analysis.trend}
          </div>
        </div>
        <div className="rounded bg-slate-100 p-4">
          <div className="text-xs text-slate-500">推奨</div>
          <div
            className={`font-bold ${recommendationClass[analysis.recommendation] ?? 'text-slate-500'}`}
          >
            {recommendationLabel[analysis.recommendation] ?? analysis.recommendation}
          </div>
        </div>
      </div>

      {analysis.signals && Object.keys(analysis.signals).length > 0 && (
        <div className="mb-4">
          <h4 className="mb-2 mt-0 text-sm font-semibold text-slate-900">シグナル</h4>
          <ul className="m-0 list-disc pl-6 text-sm text-slate-700">
            {Object.entries(analysis.signals).map(([key, value]) =>
              value ? (
                <li key={key} className="mb-1">
                  <strong className="text-slate-900">{key.toUpperCase()}:</strong> {value}
                </li>
              ) : null
            )}
          </ul>
        </div>
      )}

      <div>
        <h4 className="mb-2 mt-0 text-sm font-semibold text-slate-900">サマリー</h4>
        <p className="m-0 leading-relaxed text-slate-700">{analysis.summary}</p>
      </div>
    </div>
  );
};

export default ChartAnalysisPanel;
