import { useEffect, useState } from 'react';
import { useSearchParams } from 'react-router-dom';
import { advisorApi } from '@/services/api/advisorApi';
import FutureValueChart from '@/components/advisor/FutureValueChart';
import type { SimulateResponse } from '@/types/advisor';
import {
  PageHeader,
  Card,
  CardHeader,
  CardTitle,
  CardBody,
  Stat,
  Button,
  Field,
  NumberInput,
} from '@/components/ui';

const formatYen = (v: number) => `¥${Math.round(v).toLocaleString()}`;

const SimulatorPage = () => {
  const [params] = useSearchParams();
  const [pv, setPv] = useState(Number(params.get('pv') ?? 1_000_000));
  const [monthly, setMonthly] = useState(Number(params.get('monthly') ?? 50_000));
  const [rate, setRate] = useState(Number(params.get('rate') ?? 5.0));
  const [years, setYears] = useState(Number(params.get('years') ?? 20));
  const [result, setResult] = useState<SimulateResponse | null>(null);
  const [loading, setLoading] = useState(false);

  const [goal, setGoal] = useState(20_000_000);
  const [requiredMsg, setRequiredMsg] = useState<string>('');

  const handleSimulate = async () => {
    setLoading(true);
    try {
      const res = await advisorApi.simulate({
        pv,
        monthly_investment: monthly,
        annual_rate: rate / 100,
        years,
      });
      setResult(res);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    // URL クエリで値が渡されたら初回自動実行
    if (params.get('monthly') || params.get('rate')) {
      void handleSimulate();
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  const handleRequiredRate = async () => {
    const res = await advisorApi.requiredRate({
      goal,
      pv,
      n_months: years * 12,
      monthly_investment: monthly,
    });
    setRequiredMsg(
      res.annual_rate_percent == null
        ? '計算不能'
        : res.annual_rate_percent > 200
          ? '実質到達不可能'
          : `必要年利: ${res.annual_rate_percent}%`
    );
  };

  return (
    <>
      <PageHeader
        title="将来価値シミュレータ"
        description="積立と想定年利から将来評価額を試算"
      />

      <Card className="mb-6">
        <CardHeader>
          <CardTitle>入力</CardTitle>
        </CardHeader>
        <CardBody>
          <div className="grid gap-3 sm:grid-cols-2 lg:grid-cols-4">
            <Field label="現在評価額 (円)">
              <NumberInput value={pv} onChange={setPv} step={10_000} />
            </Field>
            <Field label="毎月積立 (円)">
              <NumberInput value={monthly} onChange={setMonthly} step={1000} />
            </Field>
            <Field label="想定年利 (%)">
              <NumberInput value={rate} onChange={setRate} step={0.1} />
            </Field>
            <Field label="期間 (年)">
              <NumberInput value={years} onChange={setYears} />
            </Field>
          </div>
          <div className="mt-4 flex justify-end">
            <Button variant="accent" onClick={handleSimulate} disabled={loading}>
              {loading ? '計算中...' : '▶ 実行'}
            </Button>
          </div>
        </CardBody>
      </Card>

      {result && (
        <>
          <div className="grid gap-4 grid-cols-1 sm:grid-cols-3 mb-6">
            <Stat label="最終評価額" value={formatYen(result.final_value)} accent="brand" />
            <Stat label="拠出累計" value={formatYen(result.total_contributed)} />
            <Stat
              label="運用益"
              value={formatYen(result.total_gain)}
              accent={result.total_gain >= 0 ? 'success' : 'danger'}
            />
          </div>
          <Card className="mb-6">
            <CardBody>
              <FutureValueChart data={result.timeseries} />
            </CardBody>
          </Card>
        </>
      )}

      <Card>
        <CardHeader>
          <CardTitle>必要年利逆算</CardTitle>
        </CardHeader>
        <CardBody>
          <div className="flex flex-wrap items-end gap-3">
            <Field label="目標額 (円)">
              <NumberInput value={goal} onChange={setGoal} step={100_000} />
            </Field>
            <Button variant="secondary" onClick={handleRequiredRate}>
              計算
            </Button>
            {requiredMsg && <span className="text-sm text-slate-700">{requiredMsg}</span>}
          </div>
        </CardBody>
      </Card>
    </>
  );
};

export default SimulatorPage;
