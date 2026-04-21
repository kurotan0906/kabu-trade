import { useEffect, useState } from 'react';
import { Dialog, Field, NumberInput, Button } from '@/components/ui';
import { paperTradeApi } from '@/services/api/paperTradeApi';

interface Props {
  open: boolean;
  onClose: () => void;
  currentInitialCash: number;
  onReset: () => void;
}

export const ResetConfirmDialog = ({ open, onClose, currentInitialCash, onReset }: Props) => {
  const [cash, setCash] = useState(currentInitialCash);
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (open) {
      setCash(currentInitialCash);
      setError(null);
    }
  }, [open, currentInitialCash]);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setSubmitting(true);
    setError(null);
    try {
      await paperTradeApi.resetAccount(cash);
      onReset();
      onClose();
    } catch (err) {
      setError(err instanceof Error ? err.message : 'リセットに失敗しました');
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <Dialog open={open} onClose={onClose} title="仮想口座をリセット" size="sm">
      <form onSubmit={handleSubmit} className="flex flex-col gap-4">
        <div className="rounded-md border border-amber-200 bg-amber-50 px-3 py-2 text-xs text-amber-800">
          保有銘柄・取引履歴・現金残高がすべて消去され、指定した初期資金で再スタートします。
        </div>
        <Field label="新しい初期資金 (円)">
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
          <Button type="submit" variant="destructive" disabled={submitting}>
            {submitting ? 'リセット中...' : 'リセット実行'}
          </Button>
        </div>
      </form>
    </Dialog>
  );
};

export default ResetConfirmDialog;
