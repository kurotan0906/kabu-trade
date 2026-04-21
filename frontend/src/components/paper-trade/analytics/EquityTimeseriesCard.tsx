import { Card, CardBody, EmptyState } from '@/components/ui';
import type { IndicatorProps } from './registry';

export const EquityTimeseriesCard = ({ data }: IndicatorProps) => {
  const series = data.equity_timeseries;

  if (series.length === 0) {
    return (
      <Card>
        <CardBody>
          <h3 className="mb-3 text-base font-semibold text-slate-900">投下資本・損益の推移</h3>
          <EmptyState title="推移データがありません" description="" />
        </CardBody>
      </Card>
    );
  }

  const W = 800;
  const H = 260;
  const pad = { l: 80, r: 20, t: 10, b: 30 };
  const iW = W - pad.l - pad.r;
  const iH = H - pad.t - pad.b;

  const allVals = series.flatMap((d) => [d.invested, d.realized_pl, d.unrealized_pl, d.total_pl]);
  const minY = Math.min(...allVals);
  const maxY = Math.max(...allVals);
  const rangeY = maxY - minY || 1;

  const xScale = (i: number) => pad.l + (i / Math.max(series.length - 1, 1)) * iW;
  const yScale = (v: number) => pad.t + iH - ((v - minY) / rangeY) * iH;

  const path = (key: keyof typeof series[0]) =>
    series
      .map((d, i) => `${i === 0 ? 'M' : 'L'} ${xScale(i)} ${yScale(d[key] as number)}`)
      .join(' ');

  const yTicks = 4;
  const tickVals = Array.from({ length: yTicks + 1 }, (_, i) => minY + (rangeY / yTicks) * i);
  const xLabelStep = Math.max(1, Math.floor(series.length / 6));

  const lines = [
    { key: 'invested' as const, color: '#64748b', label: '投下資本累計' },
    { key: 'realized_pl' as const, color: '#10b981', label: '実現損益累計' },
    { key: 'unrealized_pl' as const, color: '#f59e0b', label: '含み損益' },
    { key: 'total_pl' as const, color: '#2563eb', label: '合計損益' },
  ];

  return (
    <Card>
      <CardBody>
        <h3 className="mb-3 text-base font-semibold text-slate-900">投下資本・損益の推移</h3>
        <div className="w-full overflow-x-auto">
          <svg viewBox={`0 0 ${W} ${H}`} className="h-auto w-full">
            {tickVals.map((v) => (
              <g key={v}>
                <line x1={pad.l} x2={W - pad.r} y1={yScale(v)} y2={yScale(v)} stroke="#e2e8f0" strokeDasharray="2 4" />
                <text x={pad.l - 6} y={yScale(v) + 4} fill="#64748b" fontSize="10" textAnchor="end">
                  {`¥${(v / 10000).toFixed(0)}万`}
                </text>
              </g>
            ))}
            {series.filter((_, i) => i % xLabelStep === 0).map((d) => {
              const idx = series.indexOf(d);
              return (
                <text key={d.date} x={xScale(idx)} y={H - pad.b + 16} fill="#64748b" fontSize="10" textAnchor="middle">
                  {d.date.slice(5)}
                </text>
              );
            })}
            {lines.map(({ key, color }) => (
              <path key={key} d={path(key)} fill="none" stroke={color} strokeWidth="1.5" />
            ))}
            <g transform={`translate(${pad.l + 10}, ${pad.t + 4})`}>
              {lines.map(({ color, label }, i) => (
                <g key={label} transform={`translate(${i * 110}, 0)`}>
                  <rect width="14" height="2" y="5" fill={color} />
                  <text x="18" y="9" fill="#475569" fontSize="10">{label}</text>
                </g>
              ))}
            </g>
          </svg>
        </div>
      </CardBody>
    </Card>
  );
};

export default EquityTimeseriesCard;
