import { NavLink } from 'react-router-dom';
import { useState } from 'react';
import { NAV_ITEMS } from './NavLinks';
import { Button } from '@/components/ui';
import { cn } from '@/lib/cn';
import { MobileDrawer } from './MobileDrawer';

export const Header = () => {
  const [drawerOpen, setDrawerOpen] = useState(false);
  return (
    <header className="sticky top-0 z-40 h-14 border-b border-slate-200 bg-white/80 backdrop-blur">
      <div className="mx-auto flex h-full max-w-6xl items-center gap-4 px-4 md:px-6">
        <button
          type="button"
          aria-label="メニューを開く"
          className="md:hidden text-slate-700 text-xl"
          onClick={() => setDrawerOpen(true)}
        >
          ☰
        </button>

        <NavLink to="/" className="font-bold text-slate-900 tracking-tight">
          KABU<span className="text-brand-600"> TRADE</span>
        </NavLink>

        <nav className="hidden md:flex items-center gap-1 ml-6">
          {NAV_ITEMS.map((item) => (
            <NavLink
              key={item.to}
              to={item.to}
              end={item.to === '/'}
              className={({ isActive }) =>
                cn(
                  'px-3 py-1.5 text-sm font-medium rounded-md transition-colors',
                  isActive
                    ? 'text-brand-700 bg-brand-50'
                    : 'text-slate-600 hover:text-slate-900 hover:bg-slate-100'
                )
              }
            >
              {item.label}
            </NavLink>
          ))}
        </nav>

        <div className="ml-auto flex items-center gap-2">
          <Button variant="secondary" size="sm" aria-label="銘柄検索">
            🔍
          </Button>
          <Button variant="accent" size="sm">▶ バッチ</Button>
        </div>
      </div>
      <MobileDrawer open={drawerOpen} onClose={() => setDrawerOpen(false)} />
    </header>
  );
};
