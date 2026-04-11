import type { ReactNode } from 'react';
import { cn } from '@/lib/cn';

interface StatProps {
  label: string;
  value: ReactNode;
  hint?: ReactNode;
  accent?: 'default' | 'brand' | 'success' | 'warn' | 'danger';
  className?: string;
}

const ACCENT: Record<NonNullable<StatProps['accent']>, string> = {
  default: 'text-slate-900',
  brand: 'text-brand-600',
  success: 'text-emerald-600',
  warn: 'text-amber-600',
  danger: 'text-rose-600',
};

export const Stat = ({ label, value, hint, accent = 'default', className }: StatProps) => (
  <div className={cn('rounded-lg border border-slate-200 bg-white p-5 shadow-sm', className)}>
    <div className="text-xs font-medium uppercase tracking-wide text-slate-500">{label}</div>
    <div className={cn('mt-2 text-2xl font-bold tabular-nums', ACCENT[accent])}>{value}</div>
    {hint && <div className="mt-1 text-xs text-slate-500">{hint}</div>}
  </div>
);
