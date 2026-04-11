import type { ReactNode } from 'react';

interface Props {
  title: string;
  description?: string;
  icon?: ReactNode;
  action?: ReactNode;
}

export const EmptyState = ({ title, description, icon, action }: Props) => (
  <div className="flex flex-col items-center justify-center gap-3 rounded-lg border border-dashed border-slate-200 bg-white p-10 text-center">
    {icon && <div className="text-3xl text-slate-300">{icon}</div>}
    <div className="text-sm font-semibold text-slate-900">{title}</div>
    {description && <p className="max-w-sm text-sm text-slate-500">{description}</p>}
    {action && <div className="mt-2">{action}</div>}
  </div>
);
