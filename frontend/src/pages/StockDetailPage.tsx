import { useEffect, useState } from 'react';
import { useParams } from 'react-router-dom';
import { useStockStore } from '@/store/stockStore';
import StockInfo from '@/components/stock/StockInfo';
import StockChart from '@/components/stock/StockChart';
import PeriodSelector from '@/components/stock/PeriodSelector';
import Loading from '@/components/common/Loading';
import ErrorMessage from '@/components/common/ErrorMessage';

const StockDetailPage = () => {
  const { code } = useParams<{ code: string }>();
  const [period, setPeriod] = useState('1y');
  const { currentStock, stockPrices, loading, error, fetchStock, fetchPrices, clearError } =
    useStockStore();

  useEffect(() => {
    if (code) {
      fetchStock(code);
      fetchPrices(code, period);
    }
  }, [code, fetchStock, fetchPrices, period]);

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
    </div>
  );
};

export default StockDetailPage;
