import { cn } from '@/lib/cn';

interface Props {
  value: number; // 0..100
  tone?: 'brand' | 'success' | 'warn' | 'danger';
  showLabel?: boolean;
  className?: string;
}

const BAR: Record<NonNullable<Props['tone']>, string> = {
  brand: 'bg-brand-600',
  success: 'bg-emerald-500',
  warn: 'bg-amber-500',
  danger: 'bg-rose-500',
};

export const Progress = ({ value, tone = 'brand', showLabel, className }: Props) => {
  const pct = Math.max(0, Math.min(100, value));
  return (
    <div className={cn('w-full', className)}>
      <div className="h-2 w-full overflow-hidden rounded-full bg-slate-100">
        <div className={cn('h-full rounded-full transition-all', BAR[tone])} style={{ width: `${pct}%` }} />
      </div>
      {showLabel && (
        <div className="mt-1 text-xs tabular-nums text-slate-600">{pct.toFixed(1)}%</div>
      )}
    </div>
  );
};
