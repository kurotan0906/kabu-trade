import { forwardRef, type InputHTMLAttributes } from 'react';
import { cn } from '@/lib/cn';

export const Input = forwardRef<HTMLInputElement, InputHTMLAttributes<HTMLInputElement>>(
  ({ className, ...props }, ref) => (
    <input
      ref={ref}
      className={cn(
        'h-9 w-full rounded-md border border-slate-200 bg-white px-3 text-sm text-slate-900 placeholder:text-slate-400 focus:border-brand-500 focus:outline-none focus:ring-2 focus:ring-brand-100',
        className
      )}
      {...props}
    />
  )
);
Input.displayName = 'Input';

interface FieldProps {
  label: string;
  hint?: string;
  children: React.ReactNode;
}
export const Field = ({ label, hint, children }: FieldProps) => (
  <label className="flex flex-col gap-1">
    <span className="text-xs font-medium text-slate-600">{label}</span>
    {children}
    {hint && <span className="text-xs text-slate-500">{hint}</span>}
  </label>
);
