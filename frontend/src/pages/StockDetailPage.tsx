import { useEffect, useState } from 'react';
import { useParams } from 'react-router-dom';
import { useStockStore } from '@/store/stockStore';
import StockInfo from '@/components/stock/StockInfo';
import StockChart from '@/components/stock/StockChart';
import PeriodSelector from '@/components/stock/PeriodSelector';
import EvaluationResult from '@/components/stock/EvaluationResult';
import Loading from '@/components/common/Loading';
import ErrorMessage from '@/components/common/ErrorMessage';
import { evaluationApi } from '@/services/api/evaluationApi';
import type { EvaluationResult as EvaluationResultType } from '@/types/evaluation';
import ChartAnalysisPanel from '@/components/stock/ChartAnalysisPanel';
import { chartAnalysisApi } from '@/services/api/chartAnalysisApi';
import type { ChartAnalysis } from '@/types/chartAnalysis';
import AnalysisAxesPanel from '@/components/stock/AnalysisAxesPanel';

const StockDetailPage = () => {
  const { code } = useParams<{ code: string }>();
  const [period, setPeriod] = useState('1y');
  const [evaluation, setEvaluation] = useState<EvaluationResultType | null>(null);
  const [evaluationLoading, setEvaluationLoading] = useState(false);
  const [evaluationError, setEvaluationError] = useState<string | null>(null);
  const [chartAnalysis, setChartAnalysis] = useState<ChartAnalysis | null>(null);
  const [chartAnalysisLoading, setChartAnalysisLoading] = useState(false);
  const [chartAnalysisError, setChartAnalysisError] = useState<string | null>(null);
  const { currentStock, stockPrices, loading, error, fetchStock, fetchPrices, clearError } =
    useStockStore();

  useEffect(() => {
    if (code) {
      fetchStock(code);
      fetchPrices(code, period);
      // 最新のチャート分析があれば取得
      chartAnalysisApi.getLatest(code).then(setChartAnalysis).catch(() => {
        // 未分析の場合はエラーを無視
      });
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [code, period]);

  const handleEvaluate = async () => {
    if (!code) return;
    setEvaluationLoading(true);
    setEvaluationError(null);
    try {
      const result = await evaluationApi.evaluateStock(code, period);
      setEvaluation(result);
    } catch (err: unknown) {
      let errorMessage = '評価の実行に失敗しました';
      if (err instanceof Error) {
        errorMessage = err.message;
      } else if (typeof err === 'object' && err !== null && 'response' in err) {
        const errorObj = err as Record<string, unknown>;
        const response = errorObj.response as Record<string, unknown>;
        if (response && typeof response === 'object' && 'data' in response) {
          const data = response.data as Record<string, unknown>;
          if ('error' in data && typeof data.error === 'object' && data.error !== null) {
            const errorDetail = data.error as Record<string, unknown>;
            if ('message' in errorDetail && typeof errorDetail.message === 'string') {
              errorMessage = errorDetail.message;
            }
          }
        }
      }
      setEvaluationError(errorMessage);
    } finally {
      setEvaluationLoading(false);
    }
  };

  const handleChartAnalysis = async () => {
    if (!code) return;
    setChartAnalysisLoading(true);
    setChartAnalysisError(null);
    try {
      const result = await chartAnalysisApi.getLatest(code);
      setChartAnalysis(result);
    } catch {
      setChartAnalysisError(
        '分析結果が見つかりません。Claude Code でチャート分析を実行してください。'
      );
    } finally {
      setChartAnalysisLoading(false);
    }
  };

  const handlePeriodChange = (newPeriod: string) => {
    setPeriod(newPeriod);
    if (code) {
      fetchPrices(code, newPeriod);
    }
  };

  if (loading && !currentStock) {
    return <Loading />;
  }

  if (error) {
    return (
      <div>
        <ErrorMessage message={error} onClose={clearError} />
        <button onClick={() => code && fetchStock(code)}>再試行</button>
      </div>
    );
  }

  if (!currentStock) {
    return <div>銘柄情報が見つかりません</div>;
  }

  return (
    <div>
      <StockInfo stock={currentStock} />
      {stockPrices && (
        <div>
          <PeriodSelector currentPeriod={period} onPeriodChange={handlePeriodChange} />
          {loading && <Loading />}
          {stockPrices.prices.length > 0 ? (
            <StockChart prices={stockPrices.prices} period={stockPrices.period} />
          ) : (
            <p>データがありません</p>
          )}
        </div>
      )}

      {/* 評価機能 */}
      <div style={{ marginTop: '2rem' }}>
        <button
          onClick={handleEvaluate}
          disabled={evaluationLoading}
          style={{
            padding: '0.75rem 1.5rem',
            fontSize: '1rem',
            backgroundColor: '#007bff',
            color: 'white',
            border: 'none',
            borderRadius: '4px',
            cursor: evaluationLoading ? 'not-allowed' : 'pointer',
            opacity: evaluationLoading ? 0.6 : 1,
          }}
        >
          {evaluationLoading ? '評価中...' : '評価を実行'}
        </button>

        <button
          onClick={handleChartAnalysis}
          disabled={chartAnalysisLoading}
          style={{
            padding: '0.75rem 1.5rem',
            fontSize: '1rem',
            backgroundColor: '#6200ea',
            color: 'white',
            border: 'none',
            borderRadius: '4px',
            cursor: chartAnalysisLoading ? 'not-allowed' : 'pointer',
            opacity: chartAnalysisLoading ? 0.6 : 1,
            marginLeft: '1rem',
          }}
        >
          {chartAnalysisLoading ? '取得中...' : 'チャート分析を更新'}
        </button>

        {evaluationError && (
          <ErrorMessage message={evaluationError} onClose={() => setEvaluationError(null)} />
        )}

        {evaluation && <EvaluationResult evaluation={evaluation} />}

        {chartAnalysisError && (
          <ErrorMessage
            message={chartAnalysisError}
            onClose={() => setChartAnalysisError(null)}
          />
        )}
        {chartAnalysis && <ChartAnalysisPanel analysis={chartAnalysis} />}

        {/* 多軸分析パネル */}
        {code && <AnalysisAxesPanel symbol={code} />}
      </div>
    </div>
  );
};

export default StockDetailPage;
