/**
 * Evaluation result component
 */

import type { EvaluationResult as EvaluationResultType } from '@/types/evaluation';

interface EvaluationResultProps {
  evaluation: EvaluationResultType;
}

const EvaluationResult = ({ evaluation }: EvaluationResultProps) => {
  const getScoreClass = (score: number) => {
    if (score >= 70) return 'text-emerald-600';
    if (score >= 50) return 'text-amber-600';
    return 'text-rose-600';
  };

  const getRecommendationClass = (recommendation: string) => {
    switch (recommendation) {
      case '強力':
        return 'bg-emerald-600';
      case '推奨':
        return 'bg-emerald-500';
      case '注意':
        return 'bg-amber-500';
      case '非推奨':
      case '様子見':
        return 'bg-rose-500';
      default:
        return 'bg-slate-500';
    }
  };

  return (
    <div className="mt-8">
      <h2 className="text-lg font-semibold text-slate-900">評価結果</h2>

      {/* スコア表示 */}
      <div className="mb-8 mt-4 grid grid-cols-2 gap-4">
        <div className="rounded-lg bg-slate-100 p-6 text-center">
          <h3 className="mt-0 text-base font-semibold text-slate-900">買いスコア</h3>
          <div className={`text-5xl font-bold ${getScoreClass(evaluation.buy_score)}`}>
            {evaluation.buy_score}
          </div>
          <div
            className={`mt-2 rounded p-2 font-bold text-white ${getRecommendationClass(evaluation.buy_recommendation)}`}
          >
            {evaluation.buy_recommendation}
          </div>
        </div>

        <div className="rounded-lg bg-slate-100 p-6 text-center">
          <h3 className="mt-0 text-base font-semibold text-slate-900">売りスコア</h3>
          <div className={`text-5xl font-bold ${getScoreClass(evaluation.sell_score)}`}>
            {evaluation.sell_score}
          </div>
          <div
            className={`mt-2 rounded p-2 font-bold text-white ${getRecommendationClass(evaluation.sell_recommendation)}`}
          >
            {evaluation.sell_recommendation}
          </div>
        </div>
      </div>

      {/* 買いシグナル */}
      <div className="mb-8">
        <h3 className="text-base font-semibold text-slate-900">買いシグナル</h3>
        <ul className="list-disc pl-6 text-sm text-slate-700">
          {evaluation.buy_signal.reasons.map((reason, index) => (
            <li key={index} className="mb-2">
              {reason}
            </li>
          ))}
        </ul>
      </div>

      {/* 売りシグナル */}
      <div className="mb-8">
        <h3 className="text-base font-semibold text-slate-900">売りシグナル</h3>
        <ul className="list-disc pl-6 text-sm text-slate-700">
          {evaluation.sell_signal.reasons.map((reason, index) => (
            <li key={index} className="mb-2">
              {reason}
            </li>
          ))}
        </ul>
      </div>

      {/* テクニカル指標 */}
      <div className="mb-8">
        <h3 className="text-base font-semibold text-slate-900">テクニカル指標</h3>
        <div className="grid grid-cols-2 gap-4 text-sm text-slate-700">
          <div>
            <strong className="text-slate-900">RSI:</strong>{' '}
            {evaluation.technical_indicators.rsi.toFixed(2)}
          </div>
          <div>
            <strong className="text-slate-900">移動平均（短期）:</strong>{' '}
            {evaluation.technical_indicators.moving_averages.ma_short.toFixed(2)}円
          </div>
          <div>
            <strong className="text-slate-900">移動平均（中期）:</strong>{' '}
            {evaluation.technical_indicators.moving_averages.ma_medium.toFixed(2)}円
          </div>
          <div>
            <strong className="text-slate-900">移動平均（長期）:</strong>{' '}
            {evaluation.technical_indicators.moving_averages.ma_long.toFixed(2)}円
          </div>
        </div>
      </div>

      {/* ファンダメンタル指標 */}
      <div className="mb-8">
        <h3 className="text-base font-semibold text-slate-900">ファンダメンタル指標</h3>
        <div className="rounded-lg bg-slate-100 p-4 text-sm text-slate-700">
          <div>
            <strong className="text-slate-900">総合スコア:</strong>{' '}
            {evaluation.fundamental_metrics.score} ({evaluation.fundamental_metrics.evaluation})
          </div>
          <div className="mt-4">
            <strong className="text-slate-900">PER評価:</strong>{' '}
            {evaluation.fundamental_metrics.per_evaluation.description}
          </div>
          <div className="mt-2">
            <strong className="text-slate-900">PBR評価:</strong>{' '}
            {evaluation.fundamental_metrics.pbr_evaluation.description}
          </div>
        </div>
      </div>
    </div>
  );
};

export default EvaluationResult;
