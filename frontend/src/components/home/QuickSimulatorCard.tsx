import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import {
  Card,
  CardHeader,
  CardTitle,
  CardBody,
  Field,
  NumberInput,
  Button,
} from '@/components/ui';

export const QuickSimulatorCard = () => {
  const navigate = useNavigate();
  const [monthly, setMonthly] = useState(30_000);
  const [rate, setRate] = useState(5.0);
  const [years, setYears] = useState(20);

  const handleGo = () => {
    const params = new URLSearchParams({
      monthly: String(monthly),
      rate: String(rate),
      years: String(years),
    });
    navigate(`/simulator?${params.toString()}`);
  };

  return (
    <Card>
      <CardHeader>
        <CardTitle>クイックシミュレータ</CardTitle>
      </CardHeader>
      <CardBody>
        <div className="grid gap-3 sm:grid-cols-3">
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
          <Button variant="accent" onClick={handleGo}>
            シミュレータで詳細 →
          </Button>
        </div>
      </CardBody>
    </Card>
  );
};
