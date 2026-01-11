/**
 * Evaluation result component
 */

import type { EvaluationResult as EvaluationResultType } from '@/types/evaluation';

interface EvaluationResultProps {
  evaluation: EvaluationResultType;
}

const EvaluationResult = ({ evaluation }: EvaluationResultProps) => {
  const getScoreColor = (score: number) => {
    if (score >= 70) return '#4caf50'; // 緑
    if (score >= 50) return '#ff9800'; // オレンジ
    return '#f44336'; // 赤
  };

  const getRecommendationColor = (recommendation: string) => {
    switch (recommendation) {
      case '強力':
        return '#4caf50';
      case '推奨':
        return '#8bc34a';
      case '注意':
        return '#ff9800';
      case '非推奨':
      case '様子見':
        return '#f44336';
      default:
        return '#757575';
    }
  };

  return (
    <div style={{ marginTop: '2rem' }}>
      <h2>評価結果</h2>

      {/* スコア表示 */}
      <div
        style={{
          display: 'grid',
          gridTemplateColumns: 'repeat(2, 1fr)',
          gap: '1rem',
          marginBottom: '2rem',
        }}
      >
        <div
          style={{
            padding: '1.5rem',
            backgroundColor: '#f5f5f5',
            borderRadius: '8px',
            textAlign: 'center',
          }}
        >
          <h3 style={{ marginTop: 0 }}>買いスコア</h3>
          <div
            style={{
              fontSize: '3rem',
              fontWeight: 'bold',
              color: getScoreColor(evaluation.buy_score),
            }}
          >
            {evaluation.buy_score}
          </div>
          <div
            style={{
              marginTop: '0.5rem',
              padding: '0.5rem',
              backgroundColor: getRecommendationColor(evaluation.buy_recommendation),
              color: 'white',
              borderRadius: '4px',
              fontWeight: 'bold',
            }}
          >
            {evaluation.buy_recommendation}
          </div>
        </div>

        <div
          style={{
            padding: '1.5rem',
            backgroundColor: '#f5f5f5',
            borderRadius: '8px',
            textAlign: 'center',
          }}
        >
          <h3 style={{ marginTop: 0 }}>売りスコア</h3>
          <div
            style={{
              fontSize: '3rem',
              fontWeight: 'bold',
              color: getScoreColor(evaluation.sell_score),
            }}
          >
            {evaluation.sell_score}
          </div>
          <div
            style={{
              marginTop: '0.5rem',
              padding: '0.5rem',
              backgroundColor: getRecommendationColor(evaluation.sell_recommendation),
              color: 'white',
              borderRadius: '4px',
              fontWeight: 'bold',
            }}
          >
            {evaluation.sell_recommendation}
          </div>
        </div>
      </div>

      {/* 買いシグナル */}
      <div style={{ marginBottom: '2rem' }}>
        <h3>買いシグナル</h3>
        <ul>
          {evaluation.buy_signal.reasons.map((reason, index) => (
            <li key={index} style={{ marginBottom: '0.5rem' }}>
              {reason}
            </li>
          ))}
        </ul>
      </div>

      {/* 売りシグナル */}
      <div style={{ marginBottom: '2rem' }}>
        <h3>売りシグナル</h3>
        <ul>
          {evaluation.sell_signal.reasons.map((reason, index) => (
            <li key={index} style={{ marginBottom: '0.5rem' }}>
              {reason}
            </li>
          ))}
        </ul>
      </div>

      {/* テクニカル指標 */}
      <div style={{ marginBottom: '2rem' }}>
        <h3>テクニカル指標</h3>
        <div
          style={{
            display: 'grid',
            gridTemplateColumns: 'repeat(2, 1fr)',
            gap: '1rem',
          }}
        >
          <div>
            <strong>RSI:</strong> {evaluation.technical_indicators.rsi.toFixed(2)}
          </div>
          <div>
            <strong>移動平均（短期）:</strong>{' '}
            {evaluation.technical_indicators.moving_averages.ma_short.toFixed(2)}円
          </div>
          <div>
            <strong>移動平均（中期）:</strong>{' '}
            {evaluation.technical_indicators.moving_averages.ma_medium.toFixed(2)}円
          </div>
          <div>
            <strong>移動平均（長期）:</strong>{' '}
            {evaluation.technical_indicators.moving_averages.ma_long.toFixed(2)}円
          </div>
        </div>
      </div>

      {/* ファンダメンタル指標 */}
      <div style={{ marginBottom: '2rem' }}>
        <h3>ファンダメンタル指標</h3>
        <div
          style={{
            padding: '1rem',
            backgroundColor: '#f5f5f5',
            borderRadius: '8px',
          }}
        >
          <div>
            <strong>総合スコア:</strong> {evaluation.fundamental_metrics.score} (
            {evaluation.fundamental_metrics.evaluation})
          </div>
          <div style={{ marginTop: '1rem' }}>
            <strong>PER評価:</strong>{' '}
            {evaluation.fundamental_metrics.per_evaluation.description}
          </div>
          <div style={{ marginTop: '0.5rem' }}>
            <strong>PBR評価:</strong>{' '}
            {evaluation.fundamental_metrics.pbr_evaluation.description}
          </div>
        </div>
      </div>
    </div>
  );
};

export default EvaluationResult;
