import type { SimulatePoint } from '@/types/advisor';

interface Props {
  data: SimulatePoint[];
  width?: number;
  height?: number;
}

const fmtY = (v: number) => {
  if (v >= 1e8) return `${(v / 1e8).toFixed(1)}億`;
  if (v >= 1e4) return `${(v / 1e4).toFixed(0)}万`;
  return `${v}`;
};

const FutureValueChart = ({ data, width = 720, height = 320 }: Props) => {
  if (data.length === 0) return null;
  const pad = { l: 60, r: 20, t: 20, b: 40 };
  const innerW = width - pad.l - pad.r;
  const innerH = height - pad.t - pad.b;

  const maxY = Math.max(...data.map((d) => d.value));
  const minY = 0;
  const maxX = data[data.length - 1].year;

  const xScale = (year: number) => pad.l + (year / maxX) * innerW;
  const yScale = (v: number) => pad.t + innerH - ((v - minY) / (maxY - minY || 1)) * innerH;

  const linePath = (key: keyof SimulatePoint) =>
    data
      .map((d, i) => `${i === 0 ? 'M' : 'L'} ${xScale(d.year)} ${yScale(Number(d[key]))}`)
      .join(' ');

  // Y 軸目盛り
  const yTicks = 5;
  const tickValues = Array.from({ length: yTicks + 1 }, (_, i) => (maxY / yTicks) * i);

  return (
    <div className="w-full">
      <svg
        viewBox={`0 0 ${width} ${height}`}
        className="h-auto w-full rounded-lg bg-white"
      >
        {/* Y grid */}
        {tickValues.map((v) => (
          <g key={v}>
            <line
              x1={pad.l}
              x2={width - pad.r}
              y1={yScale(v)}
              y2={yScale(v)}
              stroke="#e2e8f0"
              strokeDasharray="2 4"
            />
            <text x={pad.l - 6} y={yScale(v) + 4} fill="#64748b" fontSize="10" textAnchor="end">
              {fmtY(v)}
            </text>
          </g>
        ))}

        {/* X labels */}
        {data
          .filter((_, i) => i % Math.max(1, Math.floor(data.length / 8)) === 0)
          .map((d) => (
            <text
              key={d.year}
              x={xScale(d.year)}
              y={height - pad.b + 16}
              fill="#64748b"
              fontSize="10"
              textAnchor="middle"
            >
              {d.year}年
            </text>
          ))}

        {/* 拠出累計（青） */}
        <path d={linePath('contributed')} fill="none" stroke="#60a5fa" strokeWidth="2" />

        {/* 評価額（紫グラデ） */}
        <defs>
          <linearGradient id="grad" x1="0" y1="0" x2="0" y2="1">
            <stop offset="0%" stopColor="#a78bfa" stopOpacity="0.6" />
            <stop offset="100%" stopColor="#a78bfa" stopOpacity="0" />
          </linearGradient>
        </defs>
        <path
          d={`${linePath('value')} L ${xScale(maxX)} ${yScale(0)} L ${xScale(0)} ${yScale(0)} Z`}
          fill="url(#grad)"
        />
        <path d={linePath('value')} fill="none" stroke="#a78bfa" strokeWidth="2.5" />

        {/* 凡例 */}
        <g transform={`translate(${pad.l + 10}, ${pad.t + 10})`}>
          <rect width="14" height="2" y="5" fill="#a78bfa" />
          <text x="20" y="9" fill="#475569" fontSize="11">
            評価額
          </text>
          <rect width="14" height="2" y="20" x="80" fill="#60a5fa" />
          <text x="100" y="24" fill="#475569" fontSize="11">
            拠出累計
          </text>
        </g>
      </svg>
    </div>
  );
};

export default FutureValueChart;
