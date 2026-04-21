import { useEffect, useState } from 'react';
import { Dialog, Field, NumberInput, Button } from '@/components/ui';
import { paperTradeApi } from '@/services/api/paperTradeApi';
import type { PaperHolding } from '@/types/paperTrade';

interface Props {
  open: boolean;
  onClose: () => void;
  holding: PaperHolding | null;
  onSubmitted: () => void;
}

export const SellDialog = ({ open, onClose, holding, onSubmitted }: Props) => {
  const [quantity, setQuantity] = useState(100);
  const [price, setPrice] = useState(0);
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (open && holding) {
      setQuantity(Math.min(100, holding.quantity));
      setPrice(holding.current_price ?? 0);
      setError(null);
    }
  }, [open, holding]);

  if (!holding) return null;

  const resolvedPrice = price > 0 ? price : (holding.current_price ?? 0);
  const expectedPl = (resolvedPrice - holding.avg_price) * quantity;

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (quantity <= 0 || quantity % 100 !== 0) {
      setError('数量は100株単位で指定してください');
      return;
    }
    if (quantity > holding.quantity) {
      setError(`保有数量を超えています（保有: ${holding.quantity}株）`);
      return;
    }
    setSubmitting(true);
    setError(null);
    try {
      await paperTradeApi.createTrade({
        action: 'sell',
        symbol: holding.symbol,
        quantity,
        price: price > 0 ? price : undefined,
      });
      onSubmitted();
      onClose();
    } catch (err) {
      setError(err instanceof Error ? err.message : '売却に失敗しました');
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <Dialog open={open} onClose={onClose} title={`売却: ${holding.symbol}`} size="md">
      <form onSubmit={handleSubmit} className="flex flex-col gap-4">
        <div className="text-sm text-slate-600">
          保有: {holding.quantity.toLocaleString()}株 / 平均取得単価: ¥{holding.avg_price.toLocaleString()}
        </div>
        <div className="grid grid-cols-2 gap-3">
          <Field label="数量（100株単位）">
            <NumberInput value={quantity} onChange={setQuantity} min={100} max={holding.quantity} step={100} />
          </Field>
          <Field label="約定価格（0で現在値）">
            <NumberInput value={price} onChange={setPrice} min={0} step={1} />
          </Field>
        </div>
        <div className="rounded-md bg-slate-50 px-3 py-2 text-sm text-slate-700">
          想定実現損益: ¥{Math.round(expectedPl).toLocaleString()}
        </div>
        {error && (
          <div className="rounded-md border border-rose-200 bg-rose-50 px-3 py-2 text-xs text-rose-700">
            {error}
          </div>
        )}
        <div className="flex justify-end gap-2 pt-2">
          <Button type="button" variant="secondary" onClick={onClose} disabled={submitting}>
            キャンセル
          </Button>
          <Button type="submit" variant="accent" disabled={submitting}>
            {submitting ? '実行中...' : '売却実行'}
          </Button>
        </div>
      </form>
    </Dialog>
  );
};

export default SellDialog;
