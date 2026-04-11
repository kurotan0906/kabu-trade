import { createContext, useContext, useState, type ReactNode } from 'react';
import { cn } from '@/lib/cn';

interface Ctx {
  value: string;
  setValue: (v: string) => void;
}
const TabsCtx = createContext<Ctx | null>(null);

interface TabsProps {
  defaultValue: string;
  value?: string;
  onValueChange?: (v: string) => void;
  children: ReactNode;
  className?: string;
}

export const Tabs = ({ defaultValue, value, onValueChange, children, className }: TabsProps) => {
  const [internal, setInternal] = useState(defaultValue);
  const current = value ?? internal;
  const set = (v: string) => {
    if (value === undefined) setInternal(v);
    onValueChange?.(v);
  };
  return (
    <TabsCtx.Provider value={{ value: current, setValue: set }}>
      <div className={className}>{children}</div>
    </TabsCtx.Provider>
  );
};

export const TabsList = ({ children, className }: { children: ReactNode; className?: string }) => (
  <div className={cn('inline-flex items-center gap-1 rounded-md bg-slate-100 p-1', className)}>{children}</div>
);

export const TabsTrigger = ({ value, children }: { value: string; children: ReactNode }) => {
  const ctx = useContext(TabsCtx);
  if (!ctx) throw new Error('TabsTrigger must be inside Tabs');
  const active = ctx.value === value;
  return (
    <button
      type="button"
      onClick={() => ctx.setValue(value)}
      className={cn(
        'rounded px-3 py-1.5 text-xs font-medium transition-colors',
        active ? 'bg-white text-slate-900 shadow-sm' : 'text-slate-600 hover:text-slate-900'
      )}
    >
      {children}
    </button>
  );
};

export const TabsContent = ({ value, children }: { value: string; children: ReactNode }) => {
  const ctx = useContext(TabsCtx);
  if (!ctx) throw new Error('TabsContent must be inside Tabs');
  if (ctx.value !== value) return null;
  return <div className="mt-4">{children}</div>;
};
