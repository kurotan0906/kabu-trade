import { NavLink } from 'react-router-dom';
import { useEffect } from 'react';
import { NAV_ITEMS } from './NavLinks';
import { cn } from '@/lib/cn';

interface Props {
  open: boolean;
  onClose: () => void;
}

export const MobileDrawer = ({ open, onClose }: Props) => {
  useEffect(() => {
    if (!open) return;
    const onKey = (e: KeyboardEvent) => {
      if (e.key === 'Escape') onClose();
    };
    window.addEventListener('keydown', onKey);
    return () => window.removeEventListener('keydown', onKey);
  }, [open, onClose]);

  if (!open) return null;
  return (
    <div role="dialog" aria-modal="true" className="fixed inset-0 z-50 md:hidden">
      <div
        className="absolute inset-0 bg-slate-900/40 backdrop-blur-sm"
        onClick={onClose}
      />
      <aside className="absolute inset-y-0 left-0 w-64 bg-white shadow-xl flex flex-col">
        <div className="flex items-center justify-between px-4 h-14 border-b border-slate-200">
          <span className="font-bold text-slate-900">メニュー</span>
          <button
            aria-label="閉じる"
            onClick={onClose}
            className="text-slate-500"
          >
            ✕
          </button>
        </div>
        <nav className="flex-1 p-2 space-y-1">
          {NAV_ITEMS.map((item) => (
            <NavLink
              key={item.to}
              to={item.to}
              end={item.to === '/'}
              onClick={onClose}
              className={({ isActive }) =>
                cn(
                  'flex items-center gap-3 rounded-md px-3 py-2 text-sm font-medium',
                  isActive
                    ? 'bg-brand-50 text-brand-700'
                    : 'text-slate-700 hover:bg-slate-100'
                )
              }
            >
              <span className="text-base">{item.icon}</span>
              {item.label}
            </NavLink>
          ))}
        </nav>
      </aside>
    </div>
  );
};
