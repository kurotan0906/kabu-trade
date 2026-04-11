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
    <form onSubmit={handleSubmit} className="mb-8">
      <div className="mx-auto flex max-w-md gap-2">
        <input
          type="text"
          value={code}
          onChange={(e) => setCode(e.target.value)}
          placeholder="銘柄コードを入力（例: 7203）"
          className="flex-1 rounded border border-slate-200 px-3 py-2 text-base text-slate-900 placeholder:text-slate-500 focus:border-brand-600 focus:outline-none"
        />
        <button
          type="submit"
          className="cursor-pointer rounded border-none bg-brand-600 px-4 py-2 text-base text-white hover:bg-brand-700"
        >
          検索
        </button>
      </div>
    </form>
  );
};

export default StockSearch;
