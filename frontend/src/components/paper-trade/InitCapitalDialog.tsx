import { useEffect, useState } from 'react';
import { Dialog, Field, NumberInput, Button } from '@/components/ui';
import { paperTradeApi } from '@/services/api/paperTradeApi';

interface Props {
  open: boolean;
  onClose: () => void;
  onInitialized: () => void;
}

export const InitCapitalDialog = ({ open, onClose, onInitialized }: Props) => {
  const [cash, setCash] = useState(1_000_000);
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (open) {
      setCash(1_000_000);
      setError(null);
    }
  }, [open]);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (cash <= 0) {
      setError('初期資金は 1 円以上で指定してください');
      return;
    }
    setSubmitting(true);
    setError(null);
    try {
      await paperTradeApi.initAccount(cash);
      onInitialized();
      onClose();
    } catch (err) {
      setError(err instanceof Error ? err.message : '初期化に失敗しました');
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <Dialog open={open} onClose={onClose} title="仮想口座を作成" size="sm">
      <form onSubmit={handleSubmit} className="flex flex-col gap-4">
        <p className="text-sm text-slate-600">
          この資金を元手に擬似的な売買を行います。リセットするまで変更できません。
        </p>
        <Field label="初期資金 (円)">
          <NumberInput value={cash} onChange={setCash} min={0} step={100_000} />
        </Field>
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
            {submitting ? '作成中...' : '作成する'}
          </Button>
        </div>
      </form>
    </Dialog>
  );
};

export default InitCapitalDialog;
