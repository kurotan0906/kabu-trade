/**
 * Stock search component
 */

import { useState } from 'react';
import { useNavigate } from 'react-router-dom';

const StockSearch = () => {
  const [code, setCode] = useState('');
  const navigate = useNavigate();

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (code.trim()) {
      navigate(`/stocks/${code.trim()}`);
    }
  };

  return (
    <form onSubmit={handleSubmit} style={{ marginBottom: '2rem' }}>
      <div style={{ display: 'flex', gap: '0.5rem', maxWidth: '400px', margin: '0 auto' }}>
        <input
          type="text"
          value={code}
          onChange={(e) => setCode(e.target.value)}
          placeholder="銘柄コードを入力（例: 7203）"
          style={{
            flex: 1,
            padding: '0.5rem',
            fontSize: '1rem',
            border: '1px solid #ccc',
            borderRadius: '4px',
          }}
        />
        <button
          type="submit"
          style={{
            padding: '0.5rem 1rem',
            fontSize: '1rem',
            backgroundColor: '#007bff',
            color: 'white',
            border: 'none',
            borderRadius: '4px',
            cursor: 'pointer',
          }}
        >
          検索
        </button>
      </div>
    </form>
  );
};

export default StockSearch;
