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

const StockDetailPage = () => {
  const { code } = useParams<{ code: string }>();
  const [period, setPeriod] = useState('1y');
  const [evaluation, setEvaluation] = useState<EvaluationResultType | null>(null);
  const [evaluationLoading, setEvaluationLoading] = useState(false);
  const [evaluationError, setEvaluationError] = useState<string | null>(null);
  const { currentStock, stockPrices, loading, error, fetchStock, fetchPrices, clearError } =
    useStockStore();

  useEffect(() => {
    if (code) {
      fetchStock(code);
      fetchPrices(code, period);
    }
  }, [code, fetchStock, fetchPrices, period]);

  const handleEvaluate = async () => {
    if (!code) return;
    setEvaluationLoading(true);
    setEvaluationError(null);
    try {
      const result = await evaluationApi.evaluateStock(code, period);
      setEvaluation(result);
    } catch (err: any) {
      setEvaluationError(
        err.response?.data?.error?.message ||
          err.message ||
          '評価の実行に失敗しました'
      );
    } finally {
      setEvaluationLoading(false);
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

        {evaluationError && (
          <ErrorMessage message={evaluationError} onClose={() => setEvaluationError(null)} />
        )}

        {evaluation && <EvaluationResult evaluation={evaluation} />}
      </div>
    </div>
  );
};

export default StockDetailPage;
