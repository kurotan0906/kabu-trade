import { useEffect, useState } from 'react';
import { Dialog, Field, Input, Select, NumberInput, Button } from '@/components/ui';
import { portfolioApi } from '@/services/api/portfolioApi';
import type { AccountType, HoldingCreate } from '@/types/portfolio';

interface Props {
  open: boolean;
  onClose: () => void;
  symbol: string;
  name?: string | null;
  onCreated?: () => void;
}

const defaultDraft = (symbol: string, name?: string | null): HoldingCreate => ({
  symbol,
  name: name ?? null,
  quantity: 0,
  avg_price: 0,
  purchase_date: null,
  account_type: 'general',
});

export const AddHoldingDialog = ({ open, onClose, symbol, name, onCreated }: Props) => {
  const [draft, setDraft] = useState<HoldingCreate>(() => defaultDraft(symbol, name));
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [success, setSuccess] = useState(false);

  useEffect(() => {
    if (open) {
      setDraft(defaultDraft(symbol, name));
      setError(null);
      setSuccess(false);
    }
  }, [open, symbol, name]);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!draft.symbol || draft.quantity <= 0 || draft.avg_price <= 0) {
      setError('銘柄コード、株数、取得単価を入力してください。');
      return;
    }
    setSubmitting(true);
    setError(null);
    try {
      await portfolioApi.createHolding(draft);
      setSuccess(true);
      onCreated?.();
      setTimeout(() => {
        onClose();
      }, 600);
    } catch (err) {
      const msg = err instanceof Error ? err.message : '登録に失敗しました';
      setError(msg);
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <Dialog open={open} onClose={onClose} title="保有銘柄を追加" size="md">
      <form onSubmit={handleSubmit} className="flex flex-col gap-4">
        <div className="grid grid-cols-2 gap-3">
          <Field label="銘柄コード">
            <Input
              value={draft.symbol}
              onChange={(e) => setDraft({ ...draft, symbol: e.target.value })}
              placeholder="7203.T"
              required
            />
          </Field>
          <Field label="銘柄名">
            <Input
              value={draft.name ?? ''}
              onChange={(e) => setDraft({ ...draft, name: e.target.value })}
              placeholder="トヨタ自動車"
            />
          </Field>
          <Field label="株数">
            <NumberInput
              value={draft.quantity}
              onChange={(v) => setDraft({ ...draft, quantity: v })}
              min={0}
            />
          </Field>
          <Field label="取得単価 (円)">
            <NumberInput
              value={draft.avg_price}
              onChange={(v) => setDraft({ ...draft, avg_price: v })}
              min={0}
              step={0.01}
            />
          </Field>
          <Field label="取得日">
            <Input
              type="date"
              value={draft.purchase_date ?? ''}
              onChange={(e) =>
                setDraft({ ...draft, purchase_date: e.target.value || null })
              }
            />
          </Field>
          <Field label="口座区分">
            <Select
              value={draft.account_type}
              onChange={(e) =>
                setDraft({ ...draft, account_type: e.target.value as AccountType })
              }
            >
              <option value="general">特定/一般</option>
              <option value="nisa_growth">NISA成長枠</option>
              <option value="nisa_tsumitate">NISAつみたて</option>
            </Select>
          </Field>
        </div>

        {error && (
          <div className="rounded-md border border-rose-200 bg-rose-50 px-3 py-2 text-xs text-rose-700">
            {error}
          </div>
        )}
        {success && (
          <div className="rounded-md border border-emerald-200 bg-emerald-50 px-3 py-2 text-xs text-emerald-700">
            追加しました。
          </div>
        )}

        <div className="flex justify-end gap-2 pt-2">
          <Button type="button" variant="secondary" onClick={onClose} disabled={submitting}>
            キャンセル
          </Button>
          <Button type="submit" variant="accent" disabled={submitting}>
            {submitting ? '追加中...' : '追加する'}
          </Button>
        </div>
      </form>
    </Dialog>
  );
};

export default AddHoldingDialog;
