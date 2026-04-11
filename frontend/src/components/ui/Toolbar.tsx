import type { HTMLAttributes } from 'react';
import { cn } from '@/lib/cn';

export const Toolbar = ({ className, ...props }: HTMLAttributes<HTMLDivElement>) => (
  <div
    className={cn('mb-4 flex flex-wrap items-center gap-2 rounded-lg bg-white p-2 shadow-sm border border-slate-200', className)}
    {...props}
  />
);
