import type { ChartAnalysis } from '@/types/chartAnalysis';

interface ChartAnalysisPanelProps {
  analysis: ChartAnalysis;
}

const trendLabel: Record<string, string> = {
  bullish: '強気 (Bullish)',
  bearish: '弱気 (Bearish)',
  neutral: '中立 (Neutral)',
};

const trendColor: Record<string, string> = {
  bullish: '#4caf50',
  bearish: '#f44336',
  neutral: '#ff9800',
};

const recommendationLabel: Record<string, string> = {
  buy: '買い (Buy)',
  sell: '売り (Sell)',
  hold: '様子見 (Hold)',
};

const recommendationColor: Record<string, string> = {
  buy: '#4caf50',
  sell: '#f44336',
  hold: '#ff9800',
};

const ChartAnalysisPanel = ({ analysis }: ChartAnalysisPanelProps) => {
  const formattedDate = new Date(analysis.created_at).toLocaleString('ja-JP');

  return (
    <div
      style={{
        border: '1px solid #e0e0e0',
        borderRadius: '8px',
        padding: '1.5rem',
        marginTop: '1rem',
      }}
    >
      <div
        style={{
          display: 'flex',
          justifyContent: 'space-between',
          alignItems: 'center',
          marginBottom: '1rem',
        }}
      >
        <h3 style={{ margin: 0 }}>AI チャート分析</h3>
        <span style={{ fontSize: '0.85rem', color: '#757575' }}>
          最終更新: {formattedDate}
        </span>
      </div>

      <div
        style={{
          display: 'grid',
          gridTemplateColumns: 'repeat(2, 1fr)',
          gap: '1rem',
          marginBottom: '1rem',
        }}
      >
        <div
          style={{
            padding: '1rem',
            backgroundColor: '#f5f5f5',
            borderRadius: '4px',
          }}
        >
          <div style={{ fontSize: '0.85rem', color: '#757575' }}>トレンド</div>
          <div
            style={{
              fontWeight: 'bold',
              color: trendColor[analysis.trend] ?? '#757575',
            }}
          >
            {trendLabel[analysis.trend] ?? analysis.trend}
          </div>
        </div>
        <div
          style={{
            padding: '1rem',
            backgroundColor: '#f5f5f5',
            borderRadius: '4px',
          }}
        >
          <div style={{ fontSize: '0.85rem', color: '#757575' }}>推奨</div>
          <div
            style={{
              fontWeight: 'bold',
              color: recommendationColor[analysis.recommendation] ?? '#757575',
            }}
          >
            {recommendationLabel[analysis.recommendation] ?? analysis.recommendation}
          </div>
        </div>
      </div>

      {analysis.signals && Object.keys(analysis.signals).length > 0 && (
        <div style={{ marginBottom: '1rem' }}>
          <h4 style={{ marginTop: 0, marginBottom: '0.5rem' }}>シグナル</h4>
          <ul style={{ margin: 0, paddingLeft: '1.5rem' }}>
            {Object.entries(analysis.signals).map(([key, value]) =>
              value ? (
                <li key={key} style={{ marginBottom: '0.25rem' }}>
                  <strong>{key.toUpperCase()}:</strong> {value}
                </li>
              ) : null
            )}
          </ul>
        </div>
      )}

      <div>
        <h4 style={{ marginTop: 0, marginBottom: '0.5rem' }}>サマリー</h4>
        <p style={{ margin: 0, lineHeight: 1.6, color: '#333' }}>
          {analysis.summary}
        </p>
      </div>
    </div>
  );
};

export default ChartAnalysisPanel;
