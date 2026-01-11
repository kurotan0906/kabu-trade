/**
 * Stock chart component
 */

import {
  LineChart,
  Line,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
  ResponsiveContainer,
} from 'recharts';
import type { StockPriceData } from '@/types/stock';

interface StockChartProps {
  prices: StockPriceData[];
  period: string;
}

const StockChart = ({ prices, period }: StockChartProps) => {
  // データをチャート用にフォーマット
  const chartData = prices.map((price) => ({
    date: new Date(price.date).toLocaleDateString('ja-JP', {
      month: 'short',
      day: 'numeric',
    }),
    close: price.close,
    open: price.open,
    high: price.high,
    low: price.low,
  }));

  return (
    <div style={{ width: '100%', height: '400px', marginTop: '2rem' }}>
      <h3>株価チャート ({period})</h3>
      <ResponsiveContainer width="100%" height="100%">
        <LineChart
          data={chartData}
          margin={{
            top: 5,
            right: 30,
            left: 20,
            bottom: 5,
          }}
        >
          <CartesianGrid strokeDasharray="3 3" />
          <XAxis
            dataKey="date"
            angle={-45}
            textAnchor="end"
            height={80}
            interval="preserveStartEnd"
          />
          <YAxis
            domain={['dataMin - 100', 'dataMax + 100']}
            tickFormatter={(value) => `${value.toLocaleString()}円`}
          />
          <Tooltip
            formatter={(value: number) => `${value.toLocaleString()}円`}
            labelStyle={{ color: '#333' }}
          />
          <Legend />
          <Line
            type="monotone"
            dataKey="close"
            stroke="#8884d8"
            name="終値"
            strokeWidth={2}
            dot={false}
          />
        </LineChart>
      </ResponsiveContainer>
    </div>
  );
};

export default StockChart;
