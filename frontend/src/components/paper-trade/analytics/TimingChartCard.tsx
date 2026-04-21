import { Card, CardBody, EmptyState } from '@/components/ui';
import type { IndicatorProps } from './registry';

export const TimingChartCard = ({ data }: IndicatorProps) => {
  const { price_series, trade_markers } = data.timing;

  if (price_series.length === 0) {
    return (
      <Card>
        <CardBody>
          <h3 className="mb-3 text-base font-semibold text-slate-900">タイミング可視化</h3>
          <EmptyState title="株価データがありません" description="" />
        </CardBody>
      </Card>
    );
  }

  const W = 800;
  const H = 280;
  const pad = { l: 70, r: 20, t: 10, b: 30 };
  const iW = W - pad.l - pad.r;
  const iH = H - pad.t - pad.b;

  const prices = price_series.map((p) => p.close);
  const minY = Math.min(...prices);
  const maxY = Math.max(...prices);
  const rangeY = maxY - minY || 1;

  const xScale = (i: number) => pad.l + (i / Math.max(price_series.length - 1, 1)) * iW;
  const yScale = (v: number) => pad.t + iH - ((v - minY) / rangeY) * iH;

  const dateToIdx = new Map(price_series.map((p, i) => [p.date.slice(0, 10), i]));

  const pricePath = price_series
    .map((p, i) => `${i === 0 ? 'M' : 'L'} ${xScale(i)} ${yScale(p.close)}`)
    .join(' ');

  const yTicks = 4;
  const tickVals = Array.from({ length: yTicks + 1 }, (_, i) => minY + (rangeY / yTicks) * i);
  const xLabelStep = Math.max(1, Math.floor(price_series.length / 6));

  return (
    <Card>
      <CardBody>
        <h3 className="mb-3 text-base font-semibold text-slate-900">タイミング可視化</h3>
        <div className="w-full overflow-x-auto">
          <svg viewBox={`0 0 ${W} ${H}`} className="h-auto w-full">
            {tickVals.map((v) => (
              <g key={v}>
                <line x1={pad.l} x2={W - pad.r} y1={yScale(v)} y2={yScale(v)} stroke="#e2e8f0" strokeDasharray="2 4" />
                <text x={pad.l - 6} y={yScale(v) + 4} fill="#64748b" fontSize="10" textAnchor="end">
                  {`¥${Math.round(v).toLocaleString()}`}
                </text>
              </g>
            ))}
            {price_series.filter((_, i) => i % xLabelStep === 0).map((p, _i) => {
              const idx = price_series.indexOf(p);
              return (
                <text key={p.date} x={xScale(idx)} y={H - pad.b + 16} fill="#64748b" fontSize="10" textAnchor="middle">
                  {p.date.slice(5)}
                </text>
              );
            })}
            <path d={pricePath} fill="none" stroke="#2563eb" strokeWidth="1.5" />
            {trade_markers.map((t, i) => {
              const idx = dateToIdx.get(t.date.slice(0, 10));
              if (idx == null) return null;
              const cx = xScale(idx);
              const cy = yScale(t.price);
              const isBuy = t.action === 'buy';
              return isBuy ? (
                <polygon
                  key={i}
                  points={`${cx},${cy - 8} ${cx - 6},${cy + 4} ${cx + 6},${cy + 4}`}
                  fill="#10b981"
                  opacity="0.9"
                />
              ) : (
                <polygon
                  key={i}
                  points={`${cx},${cy + 8} ${cx - 6},${cy - 4} ${cx + 6},${cy - 4}`}
                  fill="#ef4444"
                  opacity="0.9"
                />
              );
            })}
            <g transform={`translate(${pad.l + 10}, ${pad.t + 6})`}>
              <line x1="0" x2="14" y1="6" y2="6" stroke="#2563eb" strokeWidth="1.5" />
              <text x="18" y="9" fill="#475569" fontSize="11">終値</text>
              <polygon points="46,2 40,12 52,12" fill="#10b981" />
              <text x="56" y="9" fill="#475569" fontSize="11">買い</text>
              <polygon points="86,12 80,2 92,2" fill="#ef4444" />
              <text x="96" y="9" fill="#475569" fontSize="11">売り</text>
            </g>
          </svg>
        </div>
      </CardBody>
    </Card>
  );
};

export default TimingChartCard;
