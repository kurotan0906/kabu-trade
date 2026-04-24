import { useEffect, useState } from 'react';
import { Link, useParams } from 'react-router-dom';
import { useStockStore } from '@/store/stockStore';
import StockInfo from '@/components/stock/StockInfo';
import StockChart from '@/components/stock/StockChart';
import PeriodSelector from '@/components/stock/PeriodSelector';
import EvaluationResult from '@/components/stock/EvaluationResult';
import ChartAnalysisPanel from '@/components/stock/ChartAnalysisPanel';
import AnalysisAxesPanel from '@/components/stock/AnalysisAxesPanel';
import { evaluationApi } from '@/services/api/evaluationApi';
import { chartAnalysisApi } from '@/services/api/chartAnalysisApi';
import type { EvaluationResult as EvaluationResultType } from '@/types/evaluation';
import type { ChartAnalysis } from '@/types/chartAnalysis';
import {
  PageHeader,
  Button,
  Tabs,
  TabsList,
  TabsTrigger,
  TabsContent,
  Card,
  CardBody,
  EmptyState,
} from '@/components/ui';
import HoldingDialog from '@/components/portfolio/HoldingDialog';
import PaperTradeBuyButton from '@/components/paper-trade/PaperTradeBuyButton';
import PaperTradeSellButton from '@/components/paper-trade/PaperTradeSellButton';

const StockDetailPage = () => {
  const { code } = useParams<{ code: string }>();
  const [period, setPeriod] = useState('1y');
  const [evaluation, setEvaluation] = useState<EvaluationResultType | null>(null);
  const [evaluationLoading, setEvaluationLoading] = useState(false);
  const [evaluationError, setEvaluationError] = useState<string | null>(null);
  const [chartAnalysis, setChartAnalysis] = useState<ChartAnalysis | null>(null);
  const [chartAnalysisLoading, setChartAnalysisLoading] = useState(false);
  const [chartAnalysisError, setChartAnalysisError] = useState<string | null>(null);
  const [axesRefreshKey, setAxesRefreshKey] = useState(0);
  const [addOpen, setAddOpen] = useState(false);
  const { currentStock, stockPrices, loading, error, fetchStock, fetchPrices, clearError } =
    useStockStore();

  useEffect(() => {
    if (code) {
      fetchStock(code);
      fetchPrices(code, period);
      chartAnalysisApi
        .getLatest(code)
        .then(setChartAnalysis)
        .catch(() => {
          // ignore when no analysis exists
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
      const result = await chartAnalysisApi.generate(code);
      setChartAnalysis(result);
    } catch {
      setChartAnalysisError(
        'チャート分析の生成に失敗しました（株価データを取得できない可能性があります）。'
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
    return <div className="p-6 text-sm text-slate-500">読み込み中...</div>;
  }

  if (error) {
    return (
      <div className="flex flex-col gap-3">
        <div className="rounded-md border border-rose-200 bg-rose-50 px-4 py-3 text-sm text-rose-700">
          {error}
        </div>
        <div>
          <Button
            variant="secondary"
            onClick={() => {
              clearError();
              if (code) fetchStock(code);
            }}
          >
            再試行
          </Button>
        </div>
      </div>
    );
  }

  if (!currentStock) {
    return <EmptyState title="銘柄情報が見つかりません" />;
  }

  return (
    <div>
      <PageHeader
        title={`${currentStock.name ?? ''} (${currentStock.code})`}
        description="スコア・チャート・多軸分析を確認できます。"
        actions={
          <div className="flex gap-2">
            <Link to={`/paper-trade/symbols/${code}.T`}>
              <Button variant="ghost" size="sm">売買分析</Button>
            </Link>
            <Button variant="secondary" onClick={() => setAddOpen(true)}>
              ポートフォリオに追加
            </Button>
            <PaperTradeBuyButton symbol={`${code}.T`} name={currentStock.name} size="md" />
            <PaperTradeSellButton symbol={`${code}.T`} size="md" />
          </div>
        }
      />

      <Tabs defaultValue="overview">
        <TabsList>
          <TabsTrigger value="overview">概要</TabsTrigger>
          <TabsTrigger value="chart">チャート</TabsTrigger>
          <TabsTrigger value="axes">分析軸</TabsTrigger>
        </TabsList>

        <TabsContent value="overview">
          <div className="flex flex-col gap-4">
            <StockInfo stock={currentStock} />

            <Card>
              <CardBody className="pt-5">
                <div className="flex flex-wrap gap-2">
                  <Button
                    variant="accent"
                    onClick={handleEvaluate}
                    disabled={evaluationLoading}
                  >
                    {evaluationLoading ? '評価中...' : '評価を実行'}
                  </Button>
                  <Button
                    variant="secondary"
                    onClick={handleChartAnalysis}
                    disabled={chartAnalysisLoading}
                  >
                    {chartAnalysisLoading ? '分析中...' : 'チャートを分析'}
                  </Button>
                </div>
                {evaluationError && (
                  <div className="mt-3 rounded-md border border-rose-200 bg-rose-50 px-3 py-2 text-xs text-rose-700">
                    {evaluationError}
                  </div>
                )}
                {chartAnalysisError && (
                  <div className="mt-3 rounded-md border border-amber-200 bg-amber-50 px-3 py-2 text-xs text-amber-700">
                    {chartAnalysisError}
                  </div>
                )}
              </CardBody>
            </Card>

            {evaluation && <EvaluationResult evaluation={evaluation} />}
            {chartAnalysis && <ChartAnalysisPanel analysis={chartAnalysis} />}
          </div>
        </TabsContent>

        <TabsContent value="chart">
          <div className="flex flex-col gap-4">
            <Card>
              <CardBody className="pt-5">
                <PeriodSelector currentPeriod={period} onPeriodChange={handlePeriodChange} />
                {stockPrices && stockPrices.prices.length > 0 ? (
                  <StockChart prices={stockPrices.prices} period={stockPrices.period} />
                ) : (
                  <p className="text-sm text-slate-500">データがありません</p>
                )}
              </CardBody>
            </Card>
          </div>
        </TabsContent>

        <TabsContent value="axes">
          <div className="flex flex-col gap-4">
            <div className="flex justify-end">
              <Button
                variant="secondary"
                size="sm"
                onClick={() => setAxesRefreshKey((k) => k + 1)}
              >
                TradingView 更新
              </Button>
            </div>
            {code && <AnalysisAxesPanel key={axesRefreshKey} symbol={code} />}
          </div>
        </TabsContent>
      </Tabs>

      {currentStock && (
        <HoldingDialog
          mode="create"
          open={addOpen}
          onClose={() => setAddOpen(false)}
          defaultSymbol={currentStock.code}
          defaultName={currentStock.name ?? null}
        />
      )}
    </div>
  );
};

export default StockDetailPage;
