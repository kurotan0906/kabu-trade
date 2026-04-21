import { useState } from 'react';
import { Button } from '@/components/ui';
import { paperTradeApi } from '@/services/api/paperTradeApi';
import type { PaperHolding } from '@/types/paperTrade';
import SellDialog from './SellDialog';

interface Props {
  symbol: string;
  size?: 'sm' | 'md';
  className?: string;
}

export const PaperTradeSellButton = ({ symbol, size = 'sm', className }: Props) => {
  const [open, setOpen] = useState(false);
  const [holding, setHolding] = useState<PaperHolding | null>(null);
  const [loading, setLoading] = useState(false);
  const [msg, setMsg] = useState<string | null>(null);

  const handleClick = async () => {
    setLoading(true);
    setMsg(null);
    try {
      const acc = await paperTradeApi.getAccount();
      if (!acc.initialized) {
        setMsg('口座未作成');
        setTimeout(() => setMsg(null), 3000);
        return;
      }
      const holdings = await paperTradeApi.listHoldings();
      const found = holdings.find((h) => h.symbol === symbol);
      if (!found) {
        setMsg('未保有');
        setTimeout(() => setMsg(null), 3000);
        return;
      }
      setHolding(found);
      setOpen(true);
    } catch {
      setMsg('取得失敗');
      setTimeout(() => setMsg(null), 3000);
    } finally {
      setLoading(false);
    }
  };

  return (
    <>
      <div className={`inline-flex flex-col items-center gap-0.5 ${className ?? ''}`}>
        <Button size={size} variant="secondary" onClick={handleClick} disabled={loading}>
          {loading ? '...' : '売却'}
        </Button>
        {msg && <span className="text-xs text-slate-500">{msg}</span>}
      </div>
      <SellDialog
        open={open}
        onClose={() => { setOpen(false); setHolding(null); }}
        holding={holding}
        onSubmitted={() => {}}
      />
    </>
  );
};

export default PaperTradeSellButton;
