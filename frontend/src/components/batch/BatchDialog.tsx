import { useEffect, useState } from 'react';
import { Dialog, Button, Progress, Badge } from '@/components/ui';
import { scoresApi } from '@/services/api/scoresApi';
import type { BatchStatus } from '@/types/stockScore';

interface Props {
  open: boolean;
  onClose: () => void;
}

const STATUS_TONE: Record<BatchStatus['status'], 'slate' | 'brand' | 'success' | 'danger'> = {
  idle: 'slate',
  running: 'brand',
  done: 'success',
  error: 'danger',
};

const STATUS_LABEL: Record<BatchStatus['status'], string> = {
  idle: '待機中',
  running: '実行中',
  done: '完了',
  error: 'エラー',
};

export const BatchDialog = ({ open, onClose }: Props) => {
  const [status, setStatus] = useState<BatchStatus | null>(null);
  const [starting, setStarting] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (!open) return;
    let cancelled = false;
    let timer: number | undefined;

    const poll = async () => {
      try {
        const s = await scoresApi.getBatchStatus();
        if (!cancelled) setStatus(s);
      } catch {
        if (!cancelled) setError('状態取得に失敗しました');
      }
    };

    poll();
    timer = window.setInterval(poll, 5000);
    return () => {
      cancelled = true;
      if (timer) window.clearInterval(timer);
    };
  }, [open]);

  const handleStart = async () => {
    setStarting(true);
    setError(null);
    try {
      await scoresApi.triggerBatch();
      const s = await scoresApi.getBatchStatus();
      setStatus(s);
    } catch {
      setError('バッチ起動に失敗しました');
    } finally {
      setStarting(false);
    }
  };

  const pct = status && status.total ? (status.processed / status.total) * 100 : 0;
  const isRunning = status?.status === 'running';

  return (
    <Dialog
      open={open}
      onClose={onClose}
      title="スコアリングバッチ"
      description="全銘柄の再スコアリングを実行します"
    >
      <div className="space-y-4">
        <div className="flex items-center gap-2">
          <span className="text-xs text-slate-500">状態:</span>
          {status ? (
            <Badge tone={STATUS_TONE[status.status] ?? 'slate'}>
              {STATUS_LABEL[status.status] ?? status.status}
            </Badge>
          ) : (
            <span className="text-xs text-slate-400">取得中...</span>
          )}
        </div>

        {status && (
          <div>
            <Progress value={pct} tone="brand" />
            <div className="mt-1 text-xs text-slate-600 tabular-nums">
              {status.processed ?? 0} / {status.total ?? 0}
              {status.finished_at &&
                ` · 完了 ${new Date(status.finished_at).toLocaleString('ja-JP')}`}
            </div>
          </div>
        )}

        {error && <p className="text-xs text-rose-600">{error}</p>}

        <div className="flex justify-end gap-2">
          <Button variant="secondary" onClick={onClose}>閉じる</Button>
          <Button
            variant="accent"
            disabled={starting || isRunning}
            onClick={handleStart}
          >
            {isRunning ? '実行中...' : starting ? '開始中...' : '▶ 実行'}
          </Button>
        </div>
      </div>
    </Dialog>
  );
};
