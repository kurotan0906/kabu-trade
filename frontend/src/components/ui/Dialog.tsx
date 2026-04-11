import { useEffect, useRef, type ReactNode } from 'react';
import { cn } from '@/lib/cn';

interface DialogProps {
  open: boolean;
  onClose: () => void;
  title?: string;
  description?: string;
  children: ReactNode;
  size?: 'sm' | 'md' | 'lg';
  position?: 'center' | 'drawer-left';
}

const SIZE: Record<NonNullable<DialogProps['size']>, string> = {
  sm: 'max-w-sm',
  md: 'max-w-lg',
  lg: 'max-w-2xl',
};

export const Dialog = ({
  open,
  onClose,
  title,
  description,
  children,
  size = 'md',
  position = 'center',
}: DialogProps) => {
  const ref = useRef<HTMLDivElement>(null);

  useEffect(() => {
    if (!open) return;
    const onKey = (e: KeyboardEvent) => {
      if (e.key === 'Escape') onClose();
    };
    window.addEventListener('keydown', onKey);
    return () => window.removeEventListener('keydown', onKey);
  }, [open, onClose]);

  if (!open) return null;

  const panelClass =
    position === 'drawer-left'
      ? 'fixed inset-y-0 left-0 w-72 bg-white shadow-xl'
      : cn(
          'fixed left-1/2 top-1/2 -translate-x-1/2 -translate-y-1/2 w-full rounded-lg bg-white shadow-xl',
          SIZE[size]
        );

  return (
    <div
      role="dialog"
      aria-modal="true"
      aria-label={title}
      className="fixed inset-0 z-50"
    >
      <div
        className="absolute inset-0 bg-slate-900/40 backdrop-blur-sm"
        onClick={onClose}
      />
      <div ref={ref} className={panelClass}>
        {(title || description) && (
          <div className="px-5 pt-5 pb-3 border-b border-slate-100">
            {title && <h2 className="text-base font-semibold text-slate-900">{title}</h2>}
            {description && <p className="mt-1 text-sm text-slate-500">{description}</p>}
          </div>
        )}
        <div className="px-5 py-5">{children}</div>
      </div>
    </div>
  );
};
