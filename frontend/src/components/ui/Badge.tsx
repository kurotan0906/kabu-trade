import type { HTMLAttributes } from 'react';
import { cva, type VariantProps } from 'class-variance-authority';
import { cn } from '@/lib/cn';

const badge = cva(
  'inline-flex items-center gap-1 rounded-full px-2.5 py-0.5 text-xs font-semibold',
  {
    variants: {
      tone: {
        slate: 'bg-slate-100 text-slate-700',
        brand: 'bg-brand-100 text-brand-700',
        success: 'bg-emerald-100 text-emerald-700',
        warn: 'bg-amber-100 text-amber-700',
        danger: 'bg-rose-100 text-rose-700',
        sky: 'bg-sky-100 text-sky-700',
      },
    },
    defaultVariants: { tone: 'slate' },
  }
);

export type BadgeProps = HTMLAttributes<HTMLSpanElement> & VariantProps<typeof badge>;

export const Badge = ({ className, tone, ...props }: BadgeProps) => (
  <span className={cn(badge({ tone }), className)} {...props} />
);
