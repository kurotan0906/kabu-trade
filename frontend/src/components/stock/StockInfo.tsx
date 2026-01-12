/**
 * Stock info component
 */

import type { StockInfo as StockInfoType } from '@/types/stock';

interface StockInfoProps {
  stock: StockInfoType;
}

const StockInfo = ({ stock }: StockInfoProps) => {
  return (
    <div
      style={{
        padding: '1.5rem',
        margin: '1rem 0',
        backgroundColor: '#f5f5f5',
        borderRadius: '8px',
      }}
    >
      <h2 style={{ marginTop: 0 }}>{stock.name} ({stock.code})</h2>
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(2, 1fr)', gap: '1rem' }}>
        {stock.current_price && (
          <div>
            <strong>現在の株価:</strong> {typeof stock.current_price === 'string' 
              ? parseFloat(stock.current_price).toLocaleString() 
              : stock.current_price.toLocaleString()}円
          </div>
        )}
        {stock.sector && (
          <div>
            <strong>業種:</strong> {stock.sector}
          </div>
        )}
        {stock.market_cap && (
          <div>
            <strong>時価総額:</strong> {((typeof stock.market_cap === 'string' 
              ? parseFloat(stock.market_cap) 
              : stock.market_cap) / 1000000000).toFixed(2)}億円
          </div>
        )}
        {stock.per && (
          <div>
            <strong>PER:</strong> {typeof stock.per === 'string' 
              ? parseFloat(stock.per).toFixed(2) 
              : stock.per.toFixed(2)}
          </div>
        )}
        {stock.pbr && (
          <div>
            <strong>PBR:</strong> {typeof stock.pbr === 'string' 
              ? parseFloat(stock.pbr).toFixed(2) 
              : stock.pbr.toFixed(2)}
          </div>
        )}
      </div>
    </div>
  );
};

export default StockInfo;
