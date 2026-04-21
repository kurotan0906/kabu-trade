import { useState } from 'react';
import { Button } from '@/components/ui';
import { paperTradeApi } from '@/services/api/paperTradeApi';
import BuyDialog from './BuyDialog';

interface Props {
  symbol: string;
  name?: string | null;
  size?: 'sm' | 'md';
  className?: string;
}

export const PaperTradeBuyButton = ({ symbol, name, size = 'sm', className }: Props) => {
  const [open, setOpen] = useState(false);
  const [cashBalance, setCashBalance] = useState(0);
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
      setCashBalance(acc.cash_balance);
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
        <Button size={size} variant="accent" onClick={handleClick} disabled={loading}>
          {loading ? '...' : '買い付け'}
        </Button>
        {msg && <span className="text-xs text-rose-600">{msg}</span>}
      </div>
      <BuyDialog
        open={open}
        onClose={() => setOpen(false)}
        cashBalance={cashBalance}
        onSubmitted={() => {}}
        defaultSymbol={symbol}
        defaultName={name ?? ''}
      />
    </>
  );
};

export default PaperTradeBuyButton;
