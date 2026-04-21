import { useEffect, useState } from 'react';
import { Dialog, Field, Input, NumberInput, Button } from '@/components/ui';
import { paperTradeApi } from '@/services/api/paperTradeApi';

interface Props {
  open: boolean;
  onClose: () => void;
  cashBalance: number;
  onSubmitted: () => void;
  defaultSymbol?: string;
  defaultName?: string;
}

export const BuyDialog = ({
  open,
  onClose,
  cashBalance,
  onSubmitted,
  defaultSymbol = '',
  defaultName = '',
}: Props) => {
  const [symbol, setSymbol] = useState(defaultSymbol);
  const [name, setName] = useState(defaultName);
  const [quantity, setQuantity] = useState(100);
  const [price, setPrice] = useState(0);
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (open) {
      setSymbol(defaultSymbol);
      setName(defaultName);
      setQuantity(100);
      setPrice(0);
      setError(null);
    }
  }, [open, defaultSymbol, defaultName]);

  const totalCost = price > 0 ? price * quantity : null;
  const shortage = totalCost != null && totalCost > cashBalance ? totalCost - cashBalance : 0;

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!symbol.trim()) {
      setError('銘柄コードを入力してください');
      return;
    }
    if (quantity <= 0 || quantity % 100 !== 0) {
      setError('数量は100株単位で指定してください');
      return;
    }
    setSubmitting(true);
    setError(null);
    try {
      await paperTradeApi.createTrade({
        action: 'buy',
        symbol: symbol.trim(),
        quantity,
        price: price > 0 ? price : undefined,
        name: name || undefined,
      });
      onSubmitted();
      onClose();
    } catch (err) {
      setError(err instanceof Error ? err.message : '買い付けに失敗しました');
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <Dialog open={open} onClose={onClose} title="買い付け" size="md">
      <form onSubmit={handleSubmit} className="flex flex-col gap-4">
        <div className="grid grid-cols-2 gap-3">
          <Field label="銘柄コード">
            <Input
              value={symbol}
              onChange={(e) => setSymbol(e.target.value)}
              placeholder="7203.T"
              required
            />
          </Field>
          <Field label="銘柄名（任意）">
            <Input
              value={name}
              onChange={(e) => setName(e.target.value)}
              placeholder="トヨタ自動車"
            />
          </Field>
          <Field label="数量（100株単位）">
            <NumberInput value={quantity} onChange={setQuantity} min={100} step={100} />
          </Field>
          <Field label="約定価格（0で現在値）">
            <NumberInput value={price} onChange={setPrice} min={0} step={1} />
          </Field>
        </div>
        <div className="rounded-md bg-slate-50 px-3 py-2 text-sm text-slate-700">
          <div>
            概算コスト:{' '}
            {totalCost != null ? `¥${Math.round(totalCost).toLocaleString()}` : '現在値で計算されます'}
          </div>
          <div>現金残高: ¥{Math.round(cashBalance).toLocaleString()}</div>
        </div>
        {shortage > 0 && (
          <div className="rounded-md border border-rose-200 bg-rose-50 px-3 py-2 text-xs text-rose-700">
            残高不足: ¥{Math.round(shortage).toLocaleString()} 不足しています
          </div>
        )}
        {error && (
          <div className="rounded-md border border-rose-200 bg-rose-50 px-3 py-2 text-xs text-rose-700">
            {error}
          </div>
        )}
        <div className="flex justify-end gap-2 pt-2">
          <Button type="button" variant="secondary" onClick={onClose} disabled={submitting}>
            キャンセル
          </Button>
          <Button type="submit" variant="accent" disabled={submitting || shortage > 0}>
            {submitting ? '実行中...' : '買い付け実行'}
          </Button>
        </div>
      </form>
    </Dialog>
  );
};

export default BuyDialog;
