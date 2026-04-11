import { useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { Dialog, Input, Button } from '@/components/ui';

interface Props {
  open: boolean;
  onClose: () => void;
}

const normalizeCode = (raw: string): string | null => {
  const trimmed = raw.trim().replace(/\.T$/i, '');
  if (/^\d{4}$/.test(trimmed)) return trimmed;
  return null;
};

export const CommandPalette = ({ open, onClose }: Props) => {
  const navigate = useNavigate();
  const [q, setQ] = useState('');
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (!open) {
      setQ('');
      setError(null);
    }
  }, [open]);

  const submit = () => {
    const code = normalizeCode(q);
    if (!code) {
      setError('4桁の銘柄コードを入力してください（例: 7203）');
      return;
    }
    onClose();
    navigate(`/stocks/${code}`);
  };

  return (
    <Dialog
      open={open}
      onClose={onClose}
      title="銘柄検索"
      description="銘柄コード (4桁) を入力"
    >
      <form
        onSubmit={(e) => {
          e.preventDefault();
          submit();
        }}
        className="space-y-3"
      >
        <Input
          autoFocus
          placeholder="例: 7203"
          value={q}
          onChange={(e) => {
            setQ(e.target.value);
            setError(null);
          }}
        />
        {error && <p className="text-xs text-rose-600">{error}</p>}
        <div className="flex justify-end gap-2">
          <Button type="button" variant="secondary" onClick={onClose}>
            キャンセル
          </Button>
          <Button type="submit">開く →</Button>
        </div>
      </form>
    </Dialog>
  );
};
