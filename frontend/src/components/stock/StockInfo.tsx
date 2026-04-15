/**
 * Stock info component
 */

import type { StockInfo as StockInfoType } from '@/types/stock';

interface StockInfoProps {
  stock: StockInfoType;
}

const StockInfo = ({ stock }: StockInfoProps) => {
  return (
    <div className="my-4 rounded-lg bg-slate-100 p-6">
      <div className="flex flex-wrap items-center gap-x-3 gap-y-1">
        <h2 className="mt-0 text-lg font-semibold text-slate-900">
          {stock.name} ({stock.code})
        </h2>
        <a
          href={`https://finance.yahoo.com/quote/${stock.code}.T`}
          target="_blank"
          rel="noopener noreferrer"
          className="text-xs text-violet-600 underline hover:text-violet-800"
        >
          Yahoo Finance ↗
        </a>
        <a
          href={`https://finance.yahoo.co.jp/quote/${stock.code}.T`}
          target="_blank"
          rel="noopener noreferrer"
          className="text-xs text-violet-600 underline hover:text-violet-800"
        >
          Yahoo!ファイナンス(JP) ↗
        </a>
      </div>
      <div className="mt-3 grid grid-cols-2 gap-4 text-sm text-slate-700">
        {stock.current_price && (
          <div>
            <strong className="text-slate-900">現在の株価:</strong>{' '}
            {typeof stock.current_price === 'string'
              ? parseFloat(stock.current_price).toLocaleString()
              : stock.current_price.toLocaleString()}
            円
          </div>
        )}
        {stock.sector && (
          <div>
            <strong className="text-slate-900">業種:</strong> {stock.sector}
          </div>
        )}
        {stock.market_cap && (
          <div>
            <strong className="text-slate-900">時価総額:</strong>{' '}
            {(
              (typeof stock.market_cap === 'string'
                ? parseFloat(stock.market_cap)
                : stock.market_cap) / 1000000000
            ).toFixed(2)}
            億円
          </div>
        )}
        {stock.per && (
          <div>
            <strong className="text-slate-900">PER:</strong>{' '}
            {typeof stock.per === 'string'
              ? parseFloat(stock.per).toFixed(2)
              : stock.per.toFixed(2)}
          </div>
        )}
        {stock.pbr && (
          <div>
            <strong className="text-slate-900">PBR:</strong>{' '}
            {typeof stock.pbr === 'string'
              ? parseFloat(stock.pbr).toFixed(2)
              : stock.pbr.toFixed(2)}
          </div>
        )}
      </div>
    </div>
  );
};

export default StockInfo;
