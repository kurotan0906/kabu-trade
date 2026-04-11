import { cn } from '@/lib/cn';

interface Props {
  value: number; // 0..100
  tone?: 'brand' | 'success' | 'warn' | 'danger';
  showLabel?: boolean;
  className?: string;
}

const FILL: Record<NonNullable<Props['tone']>, string> = {
  brand: 'fill-brand-600',
  success: 'fill-emerald-500',
  warn: 'fill-amber-500',
  danger: 'fill-rose-500',
};

export const Progress = ({ value, tone = 'brand', showLabel, className }: Props) => {
  const pct = Math.max(0, Math.min(100, value));
  return (
    <div className={cn('w-full', className)}>
      <svg
        className="block h-2 w-full"
        viewBox="0 0 100 2"
        preserveAspectRatio="none"
        role="progressbar"
        aria-valuenow={Math.round(pct)}
        aria-valuemin={0}
        aria-valuemax={100}
      >
        <title>進捗 {pct.toFixed(1)}%</title>
        <rect className="fill-slate-100" x={0} y={0} width={100} height={2} rx={1} />
        <rect className={FILL[tone]} x={0} y={0} width={pct} height={2} rx={1} />
      </svg>
      {showLabel && (
        <div className="mt-1 text-xs tabular-nums text-slate-600">{pct.toFixed(1)}%</div>
      )}
    </div>
  );
};
