import { useEffect, useState } from 'react';
import { Dialog, Field, Input, Select, NumberInput, Button } from '@/components/ui';
import { portfolioApi } from '@/services/api/portfolioApi';
import type { AccountType, Holding, HoldingCreate } from '@/types/portfolio';

type Mode = 'create' | 'edit';

interface Props {
  open: boolean;
  onClose: () => void;
  mode: Mode;
  /** create モード時の初期 symbol（省略時は空文字） */
  defaultSymbol?: string;
  /** create モード時の初期 name */
  defaultName?: string | null;
  /** edit モード時の編集対象 holding（mode="edit" の時は必須） */
  holding?: Holding;
  /** 作成/保存成功時に呼ばれる */
  onSaved?: () => void;
}

const emptyDraft = (symbol: string, name?: string | null): HoldingCreate => ({
  symbol,
  name: name ?? null,
  quantity: 0,
  avg_price: 0,
  purchase_date: null,
  account_type: 'general',
});

const draftFromHolding = (h: Holding): HoldingCreate => ({
  symbol: h.symbol,
  name: h.name,
  quantity: h.quantity,
  avg_price: h.avg_price,
  purchase_date: h.purchase_date,
  account_type: h.account_type,
});

export const HoldingDialog = ({
  open,
  onClose,
  mode,
  defaultSymbol = '',
  defaultName = null,
  holding,
  onSaved,
}: Props) => {
  const [draft, setDraft] = useState<HoldingCreate>(() =>
    mode === 'edit' && holding ? draftFromHolding(holding) : emptyDraft(defaultSymbol, defaultName)
  );
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [success, setSuccess] = useState(false);

  useEffect(() => {
    if (!open) return;
    if (mode === 'edit' && holding) {
      setDraft(draftFromHolding(holding));
    } else {
      setDraft(emptyDraft(defaultSymbol, defaultName));
    }
    setError(null);
    setSuccess(false);
  }, [open, mode, holding, defaultSymbol, defaultName]);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!draft.symbol || draft.quantity <= 0 || draft.avg_price <= 0) {
      setError('銘柄コード、株数、取得単価を入力してください。');
      return;
    }
    if (mode === 'edit' && !holding) {
      setError('編集対象が見つかりません。');
      return;
    }
    setSubmitting(true);
    setError(null);
    try {
      if (mode === 'edit' && holding) {
        await portfolioApi.updateHolding(holding.id, {
          name: draft.name,
          quantity: draft.quantity,
          avg_price: draft.avg_price,
          purchase_date: draft.purchase_date,
          account_type: draft.account_type,
        });
      } else {
        await portfolioApi.createHolding(draft);
      }
      setSuccess(true);
      onSaved?.();
      setTimeout(() => {
        onClose();
      }, 600);
    } catch (err) {
      const msg =
        err instanceof Error
          ? err.message
          : mode === 'edit'
            ? '保存に失敗しました'
            : '登録に失敗しました';
      setError(msg);
    } finally {
      setSubmitting(false);
    }
  };

  const title = mode === 'edit' ? '保有銘柄を編集' : '保有銘柄を追加';
  const submitLabel = mode === 'edit' ? '保存' : '追加する';
  const submittingLabel = mode === 'edit' ? '保存中...' : '追加中...';
  const successLabel = mode === 'edit' ? '保存しました。' : '追加しました。';

  return (
    <Dialog open={open} onClose={onClose} title={title} size="md">
      <form onSubmit={handleSubmit} className="flex flex-col gap-4">
        <div className="grid grid-cols-2 gap-3">
          <Field label="銘柄コード">
            <Input
              value={draft.symbol}
              onChange={(e) => setDraft({ ...draft, symbol: e.target.value })}
              placeholder="7203.T"
              required
              disabled={mode === 'edit'}
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
            {successLabel}
          </div>
        )}

        <div className="flex justify-end gap-2 pt-2">
          <Button type="button" variant="secondary" onClick={onClose} disabled={submitting}>
            キャンセル
          </Button>
          <Button type="submit" variant="accent" disabled={submitting}>
            {submitting ? submittingLabel : submitLabel}
          </Button>
        </div>
      </form>
    </Dialog>
  );
};

export default HoldingDialog;
