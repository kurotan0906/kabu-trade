# UI 全体刷新 実装プラン

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** kabu-trade フロントエンドに Tailwind ベースのデザインシステム・AppShell・ダッシュボード型ホーム・機能間導線・モバイル対応を段階的に導入する。

**Architecture:** Vite + React 18 + TypeScript に Tailwind v4 を追加。自前 UI プリミティブ (Card, Button, Stat, Dialog 等) を `components/ui/` に集約し、全ページのインライン style を段階廃止。`AppShell` レイアウトでトップバー + グローバル検索 + モバイルドロワーを共通化する。

**Tech Stack:** Vite 5, React 18, TypeScript 5, React Router v6, Tailwind CSS v4 (`@tailwindcss/vite`), `class-variance-authority`, `clsx`, 既存 `axios` / `zustand` / `lightweight-charts` はそのまま。

**関連仕様:** `docs/superpowers/specs/2026-04-11-ui-overhaul-design.md`

**検証方針:** フロントには単体テストフレームワークが未導入。各タスクの検証は「`npm run build` 成功 + 開発サーバで該当画面を目視」の 2 本立てで行う。プリミティブは Phase A で開発専用ルート `/__ui` に並べて一覧確認する。

---

## ファイル構成（新規 / 変更）

### 新規作成

```
frontend/
├── tailwind.config.ts
├── src/
│   ├── lib/
│   │   └── cn.ts                         # clsx + twMerge ラッパ
│   ├── components/
│   │   ├── ui/
│   │   │   ├── Button.tsx
│   │   │   ├── Card.tsx
│   │   │   ├── Stat.tsx
│   │   │   ├── Badge.tsx
│   │   │   ├── Table.tsx
│   │   │   ├── Input.tsx
│   │   │   ├── Select.tsx
│   │   │   ├── NumberInput.tsx
│   │   │   ├── Dialog.tsx
│   │   │   ├── EmptyState.tsx
│   │   │   ├── PageHeader.tsx
│   │   │   ├── Toolbar.tsx
│   │   │   ├── Progress.tsx
│   │   │   ├── Tabs.tsx
│   │   │   └── index.ts
│   │   ├── layout/
│   │   │   ├── AppShell.tsx
│   │   │   ├── Header.tsx
│   │   │   ├── MobileDrawer.tsx
│   │   │   └── NavLinks.tsx
│   │   ├── search/
│   │   │   └── CommandPalette.tsx
│   │   ├── batch/
│   │   │   └── BatchDialog.tsx
│   │   ├── portfolio/
│   │   │   └── AddHoldingDialog.tsx
│   │   └── home/
│   │       ├── KpiRow.tsx
│   │       ├── TopScoresCard.tsx
│   │       ├── HoldingsQuickCard.tsx
│   │       ├── LatestSignalsCard.tsx
│   │       └── QuickSimulatorCard.tsx
│   └── pages/
│       └── __UiSandboxPage.tsx            # Phase A 専用、Phase A 完了時に削除
```

### 変更

```
frontend/
├── package.json              (依存追加)
├── vite.config.ts            (Tailwind v4 plugin 登録)
├── index.html                (Google Fonts + lang)
├── src/
│   ├── index.css             (Tailwind base + トークン)
│   ├── App.css               (最小化)
│   ├── App.tsx               (Outlet 化)
│   ├── main.tsx              (不変だが確認)
│   ├── pages/
│   │   ├── HomePage.tsx
│   │   ├── StockRankingPage.tsx
│   │   ├── StockDetailPage.tsx
│   │   ├── PortfolioPage.tsx
│   │   ├── SimulatorPage.tsx
│   │   └── AnalysisHistoryPage.tsx
│   └── components/
│       ├── common/           (ErrorMessage, Loading を ui へ移動して削除)
│       ├── advisor/FutureValueChart.tsx  (Tailwind 化)
│       ├── portfolio/PhaseIndicator.tsx  (Tailwind 化)
│       └── stock/*.tsx       (Tailwind 化、StockChart.tsx は除く)
```

### 保護対象（変更禁止）

- `backend/` 配下すべて
- `frontend/src/types/`, `frontend/src/services/api/` (API 契約不変)
- `frontend/src/components/stock/StockChart.tsx` (lightweight-charts ロジック温存)

---

## Phase A: 基盤（独立 PR）

### Task A1: Tailwind v4 と補助依存のインストール

**Files:**
- Modify: `frontend/package.json`

- [ ] **Step 1: 依存を追加**

```bash
cd frontend && npm install -D tailwindcss@^4 @tailwindcss/vite@^4
cd frontend && npm install class-variance-authority tailwind-merge
```

- [ ] **Step 2: インストール結果を確認**

Run: `cd frontend && cat package.json | grep -E 'tailwind|cva|class-variance|tailwind-merge'`
Expected: `tailwindcss`, `@tailwindcss/vite`, `class-variance-authority`, `tailwind-merge` が含まれる（`clsx` は既存）。

- [ ] **Step 3: コミット**

```bash
git add frontend/package.json frontend/package-lock.json
git commit -m "chore: add tailwind v4 and cva for UI overhaul"
```

### Task A2: Vite プラグインと CSS 登録

**Files:**
- Modify: `frontend/vite.config.ts`
- Modify: `frontend/src/index.css`
- Modify: `frontend/src/App.css`

- [ ] **Step 1: vite.config.ts に Tailwind プラグインを登録**

```ts
import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'
import tailwindcss from '@tailwindcss/vite'
import path from 'path'

export default defineConfig({
  plugins: [react(), tailwindcss()],
  resolve: {
    alias: { '@': path.resolve(__dirname, './src') },
  },
  server: {
    port: 5173,
    host: '0.0.0.0',
    proxy: {
      '/api': {
        target: process.env.VITE_API_BASE_URL || 'http://backend:8000',
        changeOrigin: true,
      },
    },
  },
})
```

- [ ] **Step 2: `src/index.css` を Tailwind エントリに差し替え**

```css
@import "tailwindcss";

@theme {
  --font-sans: 'Inter', 'Noto Sans JP', ui-sans-serif, system-ui, sans-serif;
  --color-brand-50: #f5f3ff;
  --color-brand-100: #ede9fe;
  --color-brand-500: #8b5cf6;
  --color-brand-600: #7c3aed;
  --color-brand-700: #6d28d9;
}

html, body, #root { height: 100%; }
body {
  font-family: var(--font-sans);
  background-color: theme('colors.slate.50');
  color: theme('colors.slate.900');
  -webkit-font-smoothing: antialiased;
}
```

- [ ] **Step 3: `src/App.css` を空にする（内容削除のみ、ファイルは残す）**

```css
/* Tailwind で置換済み。追加のグローバル CSS はここに書かない。 */
```

- [ ] **Step 4: ビルド確認**

Run: `cd frontend && npm run build`
Expected: ビルド成功（型エラー 0、Tailwind が CSS を生成）

- [ ] **Step 5: コミット**

```bash
git add frontend/vite.config.ts frontend/src/index.css frontend/src/App.css
git commit -m "feat(ui): wire tailwind v4 via vite plugin"
```

### Task A3: Google Fonts と HTML 調整

**Files:**
- Modify: `frontend/index.html`

- [ ] **Step 1: index.html を更新**

```html
<!doctype html>
<html lang="ja">
  <head>
    <meta charset="UTF-8" />
    <meta name="viewport" content="width=device-width, initial-scale=1.0, viewport-fit=cover" />
    <title>Kabu Trade</title>
    <link rel="preconnect" href="https://fonts.googleapis.com">
    <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
    <link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&family=Noto+Sans+JP:wght@400;500;700&display=swap" rel="stylesheet">
  </head>
  <body>
    <div id="root"></div>
    <script type="module" src="/src/main.tsx"></script>
  </body>
</html>
```

- [ ] **Step 2: ビルド確認**

Run: `cd frontend && npm run build`
Expected: 成功

- [ ] **Step 3: コミット**

```bash
git add frontend/index.html
git commit -m "feat(ui): load Inter + Noto Sans JP"
```

### Task A4: `cn` ユーティリティ

**Files:**
- Create: `frontend/src/lib/cn.ts`

- [ ] **Step 1: cn.ts を作成**

```ts
import { clsx, type ClassValue } from 'clsx';
import { twMerge } from 'tailwind-merge';

export function cn(...inputs: ClassValue[]): string {
  return twMerge(clsx(inputs));
}
```

- [ ] **Step 2: ビルド確認**

Run: `cd frontend && npm run build`
Expected: 成功

- [ ] **Step 3: コミット**

```bash
git add frontend/src/lib/cn.ts
git commit -m "feat(ui): add cn helper for tailwind class merging"
```

### Task A5: Button プリミティブ

**Files:**
- Create: `frontend/src/components/ui/Button.tsx`

- [ ] **Step 1: Button.tsx を作成**

```tsx
import { forwardRef, type ButtonHTMLAttributes } from 'react';
import { cva, type VariantProps } from 'class-variance-authority';
import { cn } from '@/lib/cn';

const button = cva(
  'inline-flex items-center justify-center gap-2 rounded-md font-medium transition-colors focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-brand-600 disabled:opacity-50 disabled:pointer-events-none',
  {
    variants: {
      variant: {
        primary: 'bg-slate-900 text-white hover:bg-slate-800',
        secondary: 'bg-white text-slate-900 border border-slate-200 hover:bg-slate-50',
        ghost: 'bg-transparent text-slate-600 hover:bg-slate-100',
        destructive: 'bg-rose-600 text-white hover:bg-rose-500',
        accent: 'bg-brand-600 text-white hover:bg-brand-700',
      },
      size: {
        sm: 'h-8 px-3 text-xs',
        md: 'h-9 px-4 text-sm',
        lg: 'h-11 px-6 text-base',
        icon: 'h-9 w-9 p-0',
      },
    },
    defaultVariants: { variant: 'primary', size: 'md' },
  }
);

export type ButtonProps = ButtonHTMLAttributes<HTMLButtonElement> &
  VariantProps<typeof button>;

export const Button = forwardRef<HTMLButtonElement, ButtonProps>(
  ({ className, variant, size, ...props }, ref) => (
    <button ref={ref} className={cn(button({ variant, size }), className)} {...props} />
  )
);
Button.displayName = 'Button';
```

- [ ] **Step 2: ビルド確認**

Run: `cd frontend && npm run build`
Expected: 成功

- [ ] **Step 3: コミット**

```bash
git add frontend/src/components/ui/Button.tsx
git commit -m "feat(ui): add Button primitive"
```

### Task A6: Card プリミティブ群

**Files:**
- Create: `frontend/src/components/ui/Card.tsx`

- [ ] **Step 1: Card.tsx を作成**

```tsx
import type { HTMLAttributes } from 'react';
import { cn } from '@/lib/cn';

export const Card = ({ className, ...props }: HTMLAttributes<HTMLDivElement>) => (
  <div
    className={cn(
      'rounded-lg border border-slate-200 bg-white shadow-sm',
      className
    )}
    {...props}
  />
);

export const CardHeader = ({ className, ...props }: HTMLAttributes<HTMLDivElement>) => (
  <div className={cn('flex items-center justify-between px-5 pt-5 pb-3', className)} {...props} />
);

export const CardTitle = ({ className, ...props }: HTMLAttributes<HTMLHeadingElement>) => (
  <h3 className={cn('text-sm font-semibold text-slate-900', className)} {...props} />
);

export const CardBody = ({ className, ...props }: HTMLAttributes<HTMLDivElement>) => (
  <div className={cn('px-5 pb-5', className)} {...props} />
);

export const CardFooter = ({ className, ...props }: HTMLAttributes<HTMLDivElement>) => (
  <div className={cn('px-5 pb-5 pt-0 flex items-center gap-2', className)} {...props} />
);
```

- [ ] **Step 2: ビルド確認**

Run: `cd frontend && npm run build`
Expected: 成功

- [ ] **Step 3: コミット**

```bash
git add frontend/src/components/ui/Card.tsx
git commit -m "feat(ui): add Card primitives"
```

### Task A7: Stat プリミティブ

**Files:**
- Create: `frontend/src/components/ui/Stat.tsx`

- [ ] **Step 1: Stat.tsx を作成**

```tsx
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
```

- [ ] **Step 2: ビルド確認 + コミット**

```bash
cd frontend && npm run build
git add frontend/src/components/ui/Stat.tsx
git commit -m "feat(ui): add Stat primitive"
```

### Task A8: Badge プリミティブ

**Files:**
- Create: `frontend/src/components/ui/Badge.tsx`

- [ ] **Step 1: Badge.tsx を作成**

```tsx
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
```

- [ ] **Step 2: ビルド確認 + コミット**

```bash
cd frontend && npm run build
git add frontend/src/components/ui/Badge.tsx
git commit -m "feat(ui): add Badge primitive"
```

### Task A9: Table プリミティブ

**Files:**
- Create: `frontend/src/components/ui/Table.tsx`

- [ ] **Step 1: Table.tsx を作成**

```tsx
import type { HTMLAttributes, TableHTMLAttributes, TdHTMLAttributes, ThHTMLAttributes } from 'react';
import { cn } from '@/lib/cn';

export const Table = ({ className, ...props }: TableHTMLAttributes<HTMLTableElement>) => (
  <div className="w-full overflow-x-auto rounded-lg border border-slate-200 bg-white shadow-sm">
    <table className={cn('w-full border-collapse text-sm', className)} {...props} />
  </div>
);

export const Thead = ({ className, ...props }: HTMLAttributes<HTMLTableSectionElement>) => (
  <thead className={cn('bg-slate-50 border-b border-slate-200', className)} {...props} />
);

export const Tbody = ({ className, ...props }: HTMLAttributes<HTMLTableSectionElement>) => (
  <tbody className={cn('divide-y divide-slate-100', className)} {...props} />
);

export const Tr = ({ className, ...props }: HTMLAttributes<HTMLTableRowElement>) => (
  <tr className={cn('hover:bg-slate-50 transition-colors', className)} {...props} />
);

export const Th = ({ className, ...props }: ThHTMLAttributes<HTMLTableCellElement>) => (
  <th
    className={cn(
      'px-4 py-3 text-left text-xs font-semibold uppercase tracking-wide text-slate-500',
      className
    )}
    {...props}
  />
);

export const Td = ({ className, ...props }: TdHTMLAttributes<HTMLTableCellElement>) => (
  <td className={cn('px-4 py-3 text-slate-900', className)} {...props} />
);
```

- [ ] **Step 2: ビルド確認 + コミット**

```bash
cd frontend && npm run build
git add frontend/src/components/ui/Table.tsx
git commit -m "feat(ui): add Table primitives"
```

### Task A10: Input / Select / NumberInput

**Files:**
- Create: `frontend/src/components/ui/Input.tsx`
- Create: `frontend/src/components/ui/Select.tsx`
- Create: `frontend/src/components/ui/NumberInput.tsx`

- [ ] **Step 1: Input.tsx**

```tsx
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
```

- [ ] **Step 2: Select.tsx**

```tsx
import { forwardRef, type SelectHTMLAttributes } from 'react';
import { cn } from '@/lib/cn';

export const Select = forwardRef<HTMLSelectElement, SelectHTMLAttributes<HTMLSelectElement>>(
  ({ className, ...props }, ref) => (
    <select
      ref={ref}
      className={cn(
        'h-9 w-full rounded-md border border-slate-200 bg-white px-3 text-sm text-slate-900 focus:border-brand-500 focus:outline-none focus:ring-2 focus:ring-brand-100',
        className
      )}
      {...props}
    />
  )
);
Select.displayName = 'Select';
```

- [ ] **Step 3: NumberInput.tsx**

```tsx
import { forwardRef, type InputHTMLAttributes } from 'react';
import { Input } from './Input';

type Props = Omit<InputHTMLAttributes<HTMLInputElement>, 'type' | 'value' | 'onChange'> & {
  value: number;
  onChange: (value: number) => void;
};

export const NumberInput = forwardRef<HTMLInputElement, Props>(
  ({ value, onChange, step = 1, ...rest }, ref) => (
    <Input
      ref={ref}
      type="number"
      value={Number.isFinite(value) ? value : ''}
      step={step}
      onChange={(e) => {
        const n = Number(e.target.value);
        onChange(Number.isFinite(n) ? n : 0);
      }}
      {...rest}
    />
  )
);
NumberInput.displayName = 'NumberInput';
```

- [ ] **Step 4: ビルド確認 + コミット**

```bash
cd frontend && npm run build
git add frontend/src/components/ui/Input.tsx frontend/src/components/ui/Select.tsx frontend/src/components/ui/NumberInput.tsx
git commit -m "feat(ui): add Input/Select/NumberInput primitives"
```

### Task A11: Dialog プリミティブ

**Files:**
- Create: `frontend/src/components/ui/Dialog.tsx`

- [ ] **Step 1: Dialog.tsx を作成**

```tsx
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
```

- [ ] **Step 2: ビルド確認 + コミット**

```bash
cd frontend && npm run build
git add frontend/src/components/ui/Dialog.tsx
git commit -m "feat(ui): add Dialog primitive"
```

### Task A12: EmptyState / PageHeader / Toolbar

**Files:**
- Create: `frontend/src/components/ui/EmptyState.tsx`
- Create: `frontend/src/components/ui/PageHeader.tsx`
- Create: `frontend/src/components/ui/Toolbar.tsx`

- [ ] **Step 1: EmptyState.tsx**

```tsx
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
```

- [ ] **Step 2: PageHeader.tsx**

```tsx
import type { ReactNode } from 'react';

interface Props {
  title: string;
  description?: string;
  actions?: ReactNode;
}

export const PageHeader = ({ title, description, actions }: Props) => (
  <div className="mb-6 flex flex-wrap items-end justify-between gap-3">
    <div>
      <h1 className="text-xl font-bold text-slate-900">{title}</h1>
      {description && <p className="mt-1 text-sm text-slate-500">{description}</p>}
    </div>
    {actions && <div className="flex items-center gap-2">{actions}</div>}
  </div>
);
```

- [ ] **Step 3: Toolbar.tsx**

```tsx
import type { HTMLAttributes } from 'react';
import { cn } from '@/lib/cn';

export const Toolbar = ({ className, ...props }: HTMLAttributes<HTMLDivElement>) => (
  <div
    className={cn('mb-4 flex flex-wrap items-center gap-2 rounded-lg bg-white p-2 shadow-sm border border-slate-200', className)}
    {...props}
  />
);
```

- [ ] **Step 4: ビルド確認 + コミット**

```bash
cd frontend && npm run build
git add frontend/src/components/ui/EmptyState.tsx frontend/src/components/ui/PageHeader.tsx frontend/src/components/ui/Toolbar.tsx
git commit -m "feat(ui): add EmptyState/PageHeader/Toolbar primitives"
```

### Task A13: Progress プリミティブ

**Files:**
- Create: `frontend/src/components/ui/Progress.tsx`

- [ ] **Step 1: Progress.tsx**

```tsx
import { cn } from '@/lib/cn';

interface Props {
  value: number; // 0..100
  tone?: 'brand' | 'success' | 'warn' | 'danger';
  showLabel?: boolean;
  className?: string;
}

const BAR: Record<NonNullable<Props['tone']>, string> = {
  brand: 'bg-brand-600',
  success: 'bg-emerald-500',
  warn: 'bg-amber-500',
  danger: 'bg-rose-500',
};

export const Progress = ({ value, tone = 'brand', showLabel, className }: Props) => {
  const pct = Math.max(0, Math.min(100, value));
  return (
    <div className={cn('w-full', className)}>
      <div className="h-2 w-full overflow-hidden rounded-full bg-slate-100">
        <div className={cn('h-full rounded-full transition-all', BAR[tone])} style={{ width: `${pct}%` }} />
      </div>
      {showLabel && (
        <div className="mt-1 text-xs tabular-nums text-slate-600">{pct.toFixed(1)}%</div>
      )}
    </div>
  );
};
```

- [ ] **Step 2: ビルド確認 + コミット**

```bash
cd frontend && npm run build
git add frontend/src/components/ui/Progress.tsx
git commit -m "feat(ui): add Progress primitive"
```

### Task A14: Tabs プリミティブ

**Files:**
- Create: `frontend/src/components/ui/Tabs.tsx`

- [ ] **Step 1: Tabs.tsx**

```tsx
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
```

- [ ] **Step 2: ビルド確認 + コミット**

```bash
cd frontend && npm run build
git add frontend/src/components/ui/Tabs.tsx
git commit -m "feat(ui): add Tabs primitive"
```

### Task A15: `ui/index.ts` バレルエクスポート

**Files:**
- Create: `frontend/src/components/ui/index.ts`

- [ ] **Step 1: index.ts**

```ts
export { Button } from './Button';
export type { ButtonProps } from './Button';
export { Card, CardHeader, CardTitle, CardBody, CardFooter } from './Card';
export { Stat } from './Stat';
export { Badge } from './Badge';
export { Table, Thead, Tbody, Tr, Th, Td } from './Table';
export { Input, Field } from './Input';
export { Select } from './Select';
export { NumberInput } from './NumberInput';
export { Dialog } from './Dialog';
export { EmptyState } from './EmptyState';
export { PageHeader } from './PageHeader';
export { Toolbar } from './Toolbar';
export { Progress } from './Progress';
export { Tabs, TabsList, TabsTrigger, TabsContent } from './Tabs';
```

- [ ] **Step 2: ビルド確認 + コミット**

```bash
cd frontend && npm run build
git add frontend/src/components/ui/index.ts
git commit -m "feat(ui): barrel export for ui primitives"
```

### Task A16: サンドボックスページと一時ルート

**Files:**
- Create: `frontend/src/pages/__UiSandboxPage.tsx`
- Modify: `frontend/src/App.tsx`

- [ ] **Step 1: サンドボックスページを作成**

```tsx
import { useState } from 'react';
import {
  Button, Card, CardHeader, CardTitle, CardBody, Stat, Badge,
  Table, Thead, Tbody, Tr, Th, Td, Input, Field, Select, NumberInput,
  Dialog, EmptyState, PageHeader, Toolbar, Progress,
  Tabs, TabsList, TabsTrigger, TabsContent,
} from '@/components/ui';

const UiSandboxPage = () => {
  const [open, setOpen] = useState(false);
  const [num, setNum] = useState(100);
  return (
    <div className="mx-auto max-w-5xl p-6 space-y-6">
      <PageHeader
        title="UI Sandbox"
        description="プリミティブ確認用。リリースビルドでは削除する"
        actions={<Button onClick={() => setOpen(true)}>Dialog を開く</Button>}
      />

      <Toolbar>
        <Badge tone="brand">Brand</Badge>
        <Badge tone="success">Success</Badge>
        <Badge tone="warn">Warn</Badge>
        <Badge tone="danger">Danger</Badge>
      </Toolbar>

      <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
        <Stat label="評価額" value="¥640,800" accent="brand" hint="前日比 +0.0%" />
        <Stat label="目標進捗" value="32.04%" accent="success" />
        <Stat label="フェーズ" value={<Badge tone="brand">成長期</Badge>} />
        <Stat label="NISA残枠" value="¥2,272,000" hint="年間上限 ¥2,400,000" />
      </div>

      <Card>
        <CardHeader><CardTitle>Buttons</CardTitle></CardHeader>
        <CardBody className="flex flex-wrap gap-2">
          <Button variant="primary">Primary</Button>
          <Button variant="secondary">Secondary</Button>
          <Button variant="accent">Accent</Button>
          <Button variant="ghost">Ghost</Button>
          <Button variant="destructive">Destructive</Button>
        </CardBody>
      </Card>

      <Card>
        <CardHeader><CardTitle>Progress</CardTitle></CardHeader>
        <CardBody className="space-y-3">
          <Progress value={32} showLabel />
          <Progress value={72} tone="success" showLabel />
        </CardBody>
      </Card>

      <Card>
        <CardHeader><CardTitle>Form</CardTitle></CardHeader>
        <CardBody className="grid gap-3 sm:grid-cols-3">
          <Field label="銘柄コード"><Input placeholder="7203" /></Field>
          <Field label="口座種別">
            <Select defaultValue="general">
              <option value="general">特定</option>
              <option value="nisa">NISA</option>
            </Select>
          </Field>
          <Field label="数量"><NumberInput value={num} onChange={setNum} /></Field>
        </CardBody>
      </Card>

      <Tabs defaultValue="overview">
        <TabsList>
          <TabsTrigger value="overview">概要</TabsTrigger>
          <TabsTrigger value="chart">チャート</TabsTrigger>
          <TabsTrigger value="analysis">分析軸</TabsTrigger>
        </TabsList>
        <TabsContent value="overview"><Card><CardBody>概要タブ</CardBody></Card></TabsContent>
        <TabsContent value="chart"><Card><CardBody>チャートタブ</CardBody></Card></TabsContent>
        <TabsContent value="analysis"><Card><CardBody>分析軸タブ</CardBody></Card></TabsContent>
      </Tabs>

      <Table>
        <Thead>
          <Tr><Th>#</Th><Th>銘柄</Th><Th>スコア</Th><Th>レーティング</Th></Tr>
        </Thead>
        <Tbody>
          <Tr><Td>1</Td><Td>7203 トヨタ</Td><Td>82</Td><Td><Badge tone="success">買い</Badge></Td></Tr>
          <Tr><Td>2</Td><Td>9433 KDDI</Td><Td>78</Td><Td><Badge tone="brand">強い買い</Badge></Td></Tr>
        </Tbody>
      </Table>

      <EmptyState
        title="データがありません"
        description="スコアリングを実行するとここに表示されます"
        action={<Button variant="accent">▶ スコアリング実行</Button>}
      />

      <Dialog open={open} onClose={() => setOpen(false)} title="テスト Dialog" description="Esc / 背景クリックで閉じる">
        <p className="text-sm text-slate-600">コンテンツサンプル</p>
        <div className="mt-4 flex justify-end gap-2">
          <Button variant="secondary" onClick={() => setOpen(false)}>キャンセル</Button>
          <Button onClick={() => setOpen(false)}>OK</Button>
        </div>
      </Dialog>
    </div>
  );
};

export default UiSandboxPage;
```

- [ ] **Step 2: App.tsx にルート追加（一時的、Phase A 末尾で削除）**

```tsx
import { BrowserRouter, Routes, Route } from 'react-router-dom'
import HomePage from './pages/HomePage'
import StockDetailPage from './pages/StockDetailPage'
import StockRankingPage from './pages/StockRankingPage'
import PortfolioPage from './pages/PortfolioPage'
import SimulatorPage from './pages/SimulatorPage'
import AnalysisHistoryPage from './pages/AnalysisHistoryPage'
import UiSandboxPage from './pages/__UiSandboxPage'
import './App.css'

function App() {
  return (
    <BrowserRouter>
      <Routes>
        <Route path="/" element={<HomePage />} />
        <Route path="/stocks/:code" element={<StockDetailPage />} />
        <Route path="/ranking" element={<StockRankingPage />} />
        <Route path="/portfolio" element={<PortfolioPage />} />
        <Route path="/simulator" element={<SimulatorPage />} />
        <Route path="/history" element={<AnalysisHistoryPage />} />
        <Route path="/__ui" element={<UiSandboxPage />} />
      </Routes>
    </BrowserRouter>
  )
}

export default App
```

- [ ] **Step 3: ビルド確認 + 目視確認**

Run: `cd frontend && npm run build`
Expected: 成功

Run: 開発サーバを起動（既に docker compose で起動中）、`http://localhost:5173/__ui` にアクセス
Expected: 全プリミティブが崩れずに表示される。Dialog が開閉する。Tabs が切り替わる。NumberInput が増減する。

- [ ] **Step 4: コミット**

```bash
git add frontend/src/pages/__UiSandboxPage.tsx frontend/src/App.tsx
git commit -m "feat(ui): add sandbox route for primitive verification"
```

---

## Phase B: AppShell + ダッシュボード化

### Task B1: AppShell と Outlet 化

**Files:**
- Create: `frontend/src/components/layout/AppShell.tsx`
- Create: `frontend/src/components/layout/NavLinks.tsx`
- Modify: `frontend/src/App.tsx`

- [ ] **Step 1: NavLinks.tsx（リンク定義の単一ソース）**

```tsx
export interface NavItem {
  to: string;
  label: string;
  icon: string; // emoji or char
}

export const NAV_ITEMS: NavItem[] = [
  { to: '/', label: 'ホーム', icon: '🏠' },
  { to: '/ranking', label: 'ランキング', icon: '📊' },
  { to: '/portfolio', label: 'ポートフォリオ', icon: '💼' },
  { to: '/simulator', label: 'シミュレータ', icon: '📈' },
  { to: '/history', label: '履歴', icon: '📜' },
];
```

- [ ] **Step 2: AppShell.tsx（Header は Task B2 で作成するので暫定 import）**

```tsx
import { Outlet } from 'react-router-dom';
import { Header } from './Header';

export const AppShell = () => (
  <div className="min-h-screen bg-slate-50 text-slate-900 font-sans">
    <Header />
    <main className="mx-auto max-w-6xl px-4 md:px-6 py-6">
      <Outlet />
    </main>
  </div>
);
```

- [ ] **Step 3: App.tsx を Outlet 化**

```tsx
import { BrowserRouter, Routes, Route } from 'react-router-dom'
import HomePage from './pages/HomePage'
import StockDetailPage from './pages/StockDetailPage'
import StockRankingPage from './pages/StockRankingPage'
import PortfolioPage from './pages/PortfolioPage'
import SimulatorPage from './pages/SimulatorPage'
import AnalysisHistoryPage from './pages/AnalysisHistoryPage'
import UiSandboxPage from './pages/__UiSandboxPage'
import { AppShell } from './components/layout/AppShell'
import './App.css'

function App() {
  return (
    <BrowserRouter>
      <Routes>
        <Route element={<AppShell />}>
          <Route path="/" element={<HomePage />} />
          <Route path="/ranking" element={<StockRankingPage />} />
          <Route path="/portfolio" element={<PortfolioPage />} />
          <Route path="/simulator" element={<SimulatorPage />} />
          <Route path="/history" element={<AnalysisHistoryPage />} />
          <Route path="/stocks/:code" element={<StockDetailPage />} />
          <Route path="/__ui" element={<UiSandboxPage />} />
        </Route>
      </Routes>
    </BrowserRouter>
  )
}

export default App
```

注: Header はまだ未作成なので Task B2 まで **このコミットはビルドを壊す**。B1+B2 を同時にコミットするか、Header スケルトンを先に作る。以下では B2 でまとめてコミット。

- [ ] **Step 4: B2 と合わせて検証するため一旦このタスクではコミットせず、B2 で合流**

### Task B2: Header（デスクトップ）

**Files:**
- Create: `frontend/src/components/layout/Header.tsx`

- [ ] **Step 1: Header.tsx（モバイル/検索/バッチは後続タスクでスタブのまま）**

```tsx
import { NavLink } from 'react-router-dom';
import { NAV_ITEMS } from './NavLinks';
import { Button } from '@/components/ui';
import { cn } from '@/lib/cn';
import { useState } from 'react';
import { MobileDrawer } from './MobileDrawer';

export const Header = () => {
  const [drawerOpen, setDrawerOpen] = useState(false);
  return (
    <header className="sticky top-0 z-40 h-14 border-b border-slate-200 bg-white/80 backdrop-blur">
      <div className="mx-auto flex h-full max-w-6xl items-center gap-4 px-4 md:px-6">
        <button
          type="button"
          aria-label="メニューを開く"
          className="md:hidden text-slate-700"
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
          <Button variant="secondary" size="sm" aria-label="検索">🔍</Button>
          <Button variant="accent" size="sm">▶ バッチ</Button>
        </div>
      </div>
      <MobileDrawer open={drawerOpen} onClose={() => setDrawerOpen(false)} />
    </header>
  );
};
```

- [ ] **Step 2: MobileDrawer スタブ（詳細は B3）**

Create: `frontend/src/components/layout/MobileDrawer.tsx`

```tsx
interface Props { open: boolean; onClose: () => void }

export const MobileDrawer = ({ open, onClose }: Props) => {
  if (!open) return null;
  return (
    <div className="fixed inset-0 z-50 md:hidden" onClick={onClose}>
      <div className="absolute inset-0 bg-slate-900/40 backdrop-blur-sm" />
      <div className="absolute inset-y-0 left-0 w-64 bg-white shadow-xl" />
    </div>
  );
};
```

- [ ] **Step 3: ビルド確認**

Run: `cd frontend && npm run build`
Expected: 成功

- [ ] **Step 4: ブラウザ確認**

`http://localhost:5173/` を開き、各ナビリンクが切り替わることを確認。現在ページが brand-50 背景でハイライトされる。

- [ ] **Step 5: コミット**

```bash
git add frontend/src/components/layout/
git add frontend/src/App.tsx
git commit -m "feat(ui): introduce AppShell with top nav header"
```

### Task B3: MobileDrawer 本実装

**Files:**
- Modify: `frontend/src/components/layout/MobileDrawer.tsx`

- [ ] **Step 1: MobileDrawer.tsx を本実装**

```tsx
import { NavLink } from 'react-router-dom';
import { useEffect } from 'react';
import { NAV_ITEMS } from './NavLinks';
import { cn } from '@/lib/cn';

interface Props { open: boolean; onClose: () => void }

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
      <div className="absolute inset-0 bg-slate-900/40 backdrop-blur-sm" onClick={onClose} />
      <aside className="absolute inset-y-0 left-0 w-64 bg-white shadow-xl flex flex-col">
        <div className="flex items-center justify-between px-4 h-14 border-b border-slate-200">
          <span className="font-bold text-slate-900">メニュー</span>
          <button aria-label="閉じる" onClick={onClose} className="text-slate-500">✕</button>
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
```

- [ ] **Step 2: ビルド + 目視確認（モバイル幅 375px で DevTools Toolbar）**

Run: `cd frontend && npm run build`

DevTools レスポンシブで 375px にし、ハンバーガー → ドロワー展開 → リンククリックで画面遷移しドロワーが閉じる。

- [ ] **Step 3: コミット**

```bash
git add frontend/src/components/layout/MobileDrawer.tsx
git commit -m "feat(ui): complete mobile drawer navigation"
```

### Task B4: CommandPalette（グローバル検索）

**Files:**
- Create: `frontend/src/components/search/CommandPalette.tsx`
- Modify: `frontend/src/components/layout/Header.tsx`

- [ ] **Step 1: CommandPalette.tsx**

```tsx
import { useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { Dialog, Input, Button } from '@/components/ui';

interface Props { open: boolean; onClose: () => void }

const normalizeCode = (raw: string): string | null => {
  const trimmed = raw.trim().replace(/\.T$/i, '');
  if (/^\d{4}$/.test(trimmed)) return trimmed;
  return null;
};

export const CommandPalette = ({ open, onClose }: Props) => {
  const navigate = useNavigate();
  const [q, setQ] = useState('');
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (!open) {
      setQ('');
      setError(null);
    }
  }, [open]);

  const submit = () => {
    const code = normalizeCode(q);
    if (!code) {
      setError('4桁の銘柄コードを入力してください（例: 7203）');
      return;
    }
    onClose();
    navigate(`/stocks/${code}`);
  };

  return (
    <Dialog open={open} onClose={onClose} title="銘柄検索" description="銘柄コード (4桁) を入力">
      <form
        onSubmit={(e) => {
          e.preventDefault();
          submit();
        }}
        className="space-y-3"
      >
        <Input
          autoFocus
          placeholder="例: 7203"
          value={q}
          onChange={(e) => {
            setQ(e.target.value);
            setError(null);
          }}
        />
        {error && <p className="text-xs text-rose-600">{error}</p>}
        <div className="flex justify-end gap-2">
          <Button type="button" variant="secondary" onClick={onClose}>キャンセル</Button>
          <Button type="submit">開く →</Button>
        </div>
      </form>
    </Dialog>
  );
};
```

- [ ] **Step 2: Header にショートカット購読と検索ボタンを統合**

```tsx
import { NavLink } from 'react-router-dom';
import { NAV_ITEMS } from './NavLinks';
import { Button } from '@/components/ui';
import { cn } from '@/lib/cn';
import { useEffect, useState } from 'react';
import { MobileDrawer } from './MobileDrawer';
import { CommandPalette } from '@/components/search/CommandPalette';

export const Header = () => {
  const [drawerOpen, setDrawerOpen] = useState(false);
  const [searchOpen, setSearchOpen] = useState(false);

  useEffect(() => {
    const onKey = (e: KeyboardEvent) => {
      if ((e.metaKey || e.ctrlKey) && e.key.toLowerCase() === 'k') {
        e.preventDefault();
        setSearchOpen(true);
      }
    };
    window.addEventListener('keydown', onKey);
    return () => window.removeEventListener('keydown', onKey);
  }, []);

  return (
    <header className="sticky top-0 z-40 h-14 border-b border-slate-200 bg-white/80 backdrop-blur">
      <div className="mx-auto flex h-full max-w-6xl items-center gap-4 px-4 md:px-6">
        <button
          type="button"
          aria-label="メニューを開く"
          className="md:hidden text-slate-700 text-xl"
          onClick={() => setDrawerOpen(true)}
        >☰</button>

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
                  isActive ? 'text-brand-700 bg-brand-50' : 'text-slate-600 hover:text-slate-900 hover:bg-slate-100'
                )
              }
            >
              {item.label}
            </NavLink>
          ))}
        </nav>

        <div className="ml-auto flex items-center gap-2">
          <Button
            variant="secondary"
            size="sm"
            onClick={() => setSearchOpen(true)}
            aria-label="銘柄検索"
          >
            🔍 <span className="hidden md:inline text-slate-400 text-xs">⌘K</span>
          </Button>
          <Button variant="accent" size="sm">▶ バッチ</Button>
        </div>
      </div>
      <MobileDrawer open={drawerOpen} onClose={() => setDrawerOpen(false)} />
      <CommandPalette open={searchOpen} onClose={() => setSearchOpen(false)} />
    </header>
  );
};
```

- [ ] **Step 3: ビルド + 動作確認**

Run: `cd frontend && npm run build`
ブラウザで `⌘K` (Mac) / `Ctrl+K` (Win) を押して Dialog が開く。`7203` と入力 → Enter で `/stocks/7203` に遷移する。

- [ ] **Step 4: コミット**

```bash
git add frontend/src/components/search/CommandPalette.tsx frontend/src/components/layout/Header.tsx
git commit -m "feat(ui): add global command palette (cmd+k)"
```

### Task B5: BatchDialog とヘッダー統合

**Files:**
- Create: `frontend/src/components/batch/BatchDialog.tsx`
- Modify: `frontend/src/components/layout/Header.tsx`

- [ ] **Step 1: BatchDialog.tsx**

```tsx
import { useEffect, useState } from 'react';
import { Dialog, Button, Progress, Badge } from '@/components/ui';
import { scoresApi } from '@/services/api/scoresApi';
import type { BatchStatus } from '@/types/stockScore';

interface Props { open: boolean; onClose: () => void }

const STATUS_TONE: Record<string, 'slate' | 'brand' | 'success' | 'danger'> = {
  idle: 'slate',
  running: 'brand',
  completed: 'success',
  failed: 'danger',
};

export const BatchDialog = ({ open, onClose }: Props) => {
  const [status, setStatus] = useState<BatchStatus | null>(null);
  const [starting, setStarting] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (!open) return;
    let cancelled = false;
    let timer: number | undefined;

    const poll = async () => {
      try {
        const s = await scoresApi.getBatchStatus();
        if (!cancelled) setStatus(s);
      } catch (e) {
        if (!cancelled) setError('状態取得に失敗しました');
      }
    };

    poll();
    timer = window.setInterval(poll, 5000);
    return () => {
      cancelled = true;
      if (timer) window.clearInterval(timer);
    };
  }, [open]);

  const handleStart = async () => {
    setStarting(true);
    setError(null);
    try {
      await scoresApi.triggerBatch();
      const s = await scoresApi.getBatchStatus();
      setStatus(s);
    } catch {
      setError('バッチ起動に失敗しました');
    } finally {
      setStarting(false);
    }
  };

  const pct = status && status.total ? (status.processed / status.total) * 100 : 0;
  const isRunning = status?.status === 'running';

  return (
    <Dialog open={open} onClose={onClose} title="スコアリングバッチ" description="全銘柄の再スコアリングを実行します">
      <div className="space-y-4">
        <div className="flex items-center gap-2">
          <span className="text-xs text-slate-500">状態:</span>
          {status ? (
            <Badge tone={STATUS_TONE[status.status] ?? 'slate'}>{status.status}</Badge>
          ) : (
            <span className="text-xs text-slate-400">取得中...</span>
          )}
        </div>

        {status && (
          <div>
            <Progress value={pct} tone="brand" />
            <div className="mt-1 text-xs text-slate-600 tabular-nums">
              {status.processed ?? 0} / {status.total ?? 0}
              {status.finished_at && ` · 完了 ${new Date(status.finished_at).toLocaleString('ja-JP')}`}
            </div>
          </div>
        )}

        {error && <p className="text-xs text-rose-600">{error}</p>}

        <div className="flex justify-end gap-2">
          <Button variant="secondary" onClick={onClose}>閉じる</Button>
          <Button variant="accent" disabled={starting || isRunning} onClick={handleStart}>
            {isRunning ? '実行中...' : starting ? '開始中...' : '▶ 実行'}
          </Button>
        </div>
      </div>
    </Dialog>
  );
};
```

- [ ] **Step 2: Header の「▶ バッチ」ボタンを Dialog 起動に差し替え**

```tsx
// Header.tsx 内
import { BatchDialog } from '@/components/batch/BatchDialog';
// ...
const [batchOpen, setBatchOpen] = useState(false);
// JSX の `▶ バッチ` ボタンを以下に:
<Button variant="accent" size="sm" onClick={() => setBatchOpen(true)}>▶ バッチ</Button>
// header 閉じタグ前に:
<BatchDialog open={batchOpen} onClose={() => setBatchOpen(false)} />
```

- [ ] **Step 3: ビルド + 動作確認**

Run: `cd frontend && npm run build`
ヘッダーの `▶ バッチ` をクリック → Dialog 表示 → 状態バッジと Progress 表示を確認。

- [ ] **Step 4: コミット**

```bash
git add frontend/src/components/batch/BatchDialog.tsx frontend/src/components/layout/Header.tsx
git commit -m "feat(ui): batch dialog replaces alert-based trigger"
```

### Task B6: HomePage ダッシュボード骨組み

**Files:**
- Modify: `frontend/src/pages/HomePage.tsx`

- [ ] **Step 1: HomePage.tsx を骨組みに差し替え**

```tsx
import { KpiRow } from '@/components/home/KpiRow';
import { TopScoresCard } from '@/components/home/TopScoresCard';
import { HoldingsQuickCard } from '@/components/home/HoldingsQuickCard';
import { LatestSignalsCard } from '@/components/home/LatestSignalsCard';
import { QuickSimulatorCard } from '@/components/home/QuickSimulatorCard';
import { PageHeader } from '@/components/ui';

const HomePage = () => (
  <>
    <PageHeader title="ダッシュボード" description="ポートフォリオとスコアの俯瞰" />
    <div className="space-y-6">
      <KpiRow />
      <div className="grid gap-6 lg:grid-cols-3">
        <div className="lg:col-span-2"><TopScoresCard /></div>
        <HoldingsQuickCard />
      </div>
      <div className="grid gap-6 lg:grid-cols-2">
        <LatestSignalsCard />
        <QuickSimulatorCard />
      </div>
    </div>
  </>
);

export default HomePage;
```

- [ ] **Step 2: 各コンポーネントのスタブを先に作る**

以下 5 ファイルを同内容のスタブとして作成（次のタスクで実装）:

```tsx
// frontend/src/components/home/KpiRow.tsx
import { Card, CardBody } from '@/components/ui';
export const KpiRow = () => <Card><CardBody>KpiRow (stub)</CardBody></Card>;
```

同じパターンで `TopScoresCard.tsx`, `HoldingsQuickCard.tsx`, `LatestSignalsCard.tsx`, `QuickSimulatorCard.tsx` を作成（関数名だけ変える）。

- [ ] **Step 3: ビルド + ブラウザ確認**

Run: `cd frontend && npm run build`
`http://localhost:5173/` を開くとダッシュボードの枠と 5 つのスタブが並ぶ。

- [ ] **Step 4: コミット**

```bash
git add frontend/src/pages/HomePage.tsx frontend/src/components/home/
git commit -m "feat(home): scaffold dashboard layout with stub cards"
```

### Task B7: KpiRow 本実装

**Files:**
- Modify: `frontend/src/components/home/KpiRow.tsx`

- [ ] **Step 1: 実装**

```tsx
import { useEffect, useState } from 'react';
import { Stat, Badge, Progress } from '@/components/ui';
import { portfolioApi } from '@/services/api/portfolioApi';
import type { PortfolioSummary } from '@/types/portfolio';

const PHASE_TONE: Record<string, 'sky' | 'brand' | 'success'> = {
  '積立期': 'sky',
  '成長期': 'brand',
  '安定期': 'success',
};

const formatYen = (v: number | null | undefined) => {
  if (v == null) return '—';
  return `¥${Math.round(v).toLocaleString()}`;
};

export const KpiRow = () => {
  const [summary, setSummary] = useState<PortfolioSummary | null>(null);

  useEffect(() => {
    portfolioApi.getSummary().then(setSummary).catch(() => setSummary(null));
  }, []);

  const progress = summary?.progress_rate ?? 0;
  const phase = summary?.current_phase ?? null;

  return (
    <div className="grid gap-4 grid-cols-2 lg:grid-cols-4">
      <Stat label="評価額" value={formatYen(summary?.total_value)} accent="brand" />
      <Stat
        label="目標進捗"
        value={summary?.target_amount ? `${progress.toFixed(1)}%` : '—'}
        hint={summary?.target_amount ? <Progress value={progress} /> : '目標未設定'}
        accent="success"
      />
      <Stat
        label="フェーズ"
        value={phase ? <Badge tone={PHASE_TONE[phase] ?? 'slate'}>{phase}</Badge> : '—'}
      />
      <Stat label="NISA残枠" value={formatYen(summary?.nisa_remaining)} hint="年間上限 ¥2,400,000" />
    </div>
  );
};
```

注: `PortfolioSummary` 型は既存の `frontend/src/types/portfolio.ts` にある想定。もし無ければ `services/api/portfolioApi.ts` の戻り値に合わせて参照する。必要なら `as any` ではなく最小の型定義をその場で作らずに、既存の型を必ず参照する。

- [ ] **Step 2: 型確認**

Run: `cd frontend && grep -R "PortfolioSummary" src/types src/services/api`
もし未定義なら次を `src/types/portfolio.ts` に追記:

```ts
export interface PortfolioSummary {
  total_value: number;
  total_cost: number;
  unrealized_pl: number;
  holdings_count: number;
  target_amount: number | null;
  progress_rate: number | null;
  nisa_remaining: number;
  current_phase: string | null;
}
```

そして `portfolioApi.getSummary` の戻り値型にする。

- [ ] **Step 3: ビルド + ブラウザで `/` を開きカード表示確認**

Run: `cd frontend && npm run build`

- [ ] **Step 4: コミット**

```bash
git add frontend/src/components/home/KpiRow.tsx
git add frontend/src/types/portfolio.ts frontend/src/services/api/portfolioApi.ts 2>/dev/null || true
git commit -m "feat(home): implement KPI row"
```

### Task B8: TopScoresCard

**Files:**
- Modify: `frontend/src/components/home/TopScoresCard.tsx`

- [ ] **Step 1: 実装**

```tsx
import { useEffect, useState } from 'react';
import { Link } from 'react-router-dom';
import { Card, CardHeader, CardTitle, CardBody, Badge, Progress, EmptyState, Button } from '@/components/ui';
import { scoresApi } from '@/services/api/scoresApi';
import type { StockScore } from '@/types/stockScore';

const RATING_TONE: Record<string, 'brand' | 'success' | 'slate' | 'warn' | 'danger'> = {
  '強い買い': 'brand',
  '買い': 'success',
  '中立': 'slate',
  '売り': 'warn',
  '強い売り': 'danger',
};

export const TopScoresCard = () => {
  const [scores, setScores] = useState<StockScore[] | null>(null);
  useEffect(() => {
    scoresApi.listScores('total_score', 5).then(setScores).catch(() => setScores([]));
  }, []);

  if (scores === null) return <Card><CardBody className="text-sm text-slate-500">読み込み中...</CardBody></Card>;

  return (
    <Card>
      <CardHeader>
        <CardTitle>スコア TOP 5</CardTitle>
        <Link to="/ranking" className="text-xs text-brand-600 hover:underline">すべて見る →</Link>
      </CardHeader>
      <CardBody>
        {scores.length === 0 ? (
          <EmptyState
            title="スコアデータがありません"
            description="ヘッダーの ▶ バッチ からスコアリングを実行してください"
            action={<Button variant="accent" size="sm">▶ バッチ</Button>}
          />
        ) : (
          <ul className="divide-y divide-slate-100">
            {scores.map((s, i) => (
              <li key={s.id}>
                <Link
                  to={`/stocks/${s.symbol.replace('.T', '')}`}
                  className="flex items-center gap-3 py-2.5 hover:bg-slate-50 rounded-md -mx-2 px-2"
                >
                  <span className="w-6 text-xs text-slate-400 tabular-nums">{i + 1}</span>
                  <div className="flex-1 min-w-0">
                    <div className="text-sm font-semibold text-slate-900">{s.symbol}</div>
                    <div className="text-xs text-slate-500 truncate">{s.name}</div>
                  </div>
                  <div className="w-32"><Progress value={s.total_score ?? 0} /></div>
                  <div className="w-12 text-right text-sm font-bold tabular-nums text-brand-600">
                    {Math.round(s.total_score ?? 0)}
                  </div>
                  {s.rating && <Badge tone={RATING_TONE[s.rating] ?? 'slate'}>{s.rating}</Badge>}
                </Link>
              </li>
            ))}
          </ul>
        )}
      </CardBody>
    </Card>
  );
};
```

- [ ] **Step 2: ビルド + コミット**

```bash
cd frontend && npm run build
git add frontend/src/components/home/TopScoresCard.tsx
git commit -m "feat(home): implement top scores card"
```

### Task B9: HoldingsQuickCard

**Files:**
- Modify: `frontend/src/components/home/HoldingsQuickCard.tsx`

- [ ] **Step 1: 実装**

```tsx
import { useEffect, useState } from 'react';
import { Link } from 'react-router-dom';
import { Card, CardHeader, CardTitle, CardBody, EmptyState, Button } from '@/components/ui';
import { portfolioApi } from '@/services/api/portfolioApi';
import type { Holding } from '@/types/portfolio';

export const HoldingsQuickCard = () => {
  const [holdings, setHoldings] = useState<Holding[] | null>(null);

  useEffect(() => {
    portfolioApi.listHoldings().then((xs) => setHoldings(xs.slice(0, 5))).catch(() => setHoldings([]));
  }, []);

  if (holdings === null) return <Card><CardBody className="text-sm text-slate-500">読み込み中...</CardBody></Card>;

  return (
    <Card>
      <CardHeader>
        <CardTitle>保有銘柄</CardTitle>
        <Link to="/portfolio" className="text-xs text-brand-600 hover:underline">詳細 →</Link>
      </CardHeader>
      <CardBody>
        {holdings.length === 0 ? (
          <EmptyState
            title="まだ保有銘柄がありません"
            action={<Link to="/portfolio"><Button variant="accent" size="sm">＋ 追加</Button></Link>}
          />
        ) : (
          <ul className="divide-y divide-slate-100">
            {holdings.map((h) => (
              <li key={h.id}>
                <Link
                  to={`/stocks/${h.symbol.replace('.T', '')}`}
                  className="flex items-center justify-between py-2.5 hover:bg-slate-50 rounded-md -mx-2 px-2"
                >
                  <div className="min-w-0">
                    <div className="text-sm font-semibold text-slate-900">{h.symbol}</div>
                    <div className="text-xs text-slate-500 truncate">{h.name}</div>
                  </div>
                  <div className="text-right">
                    <div className="text-sm text-slate-900 tabular-nums">{h.quantity}株</div>
                    <div className="text-xs text-slate-500 tabular-nums">¥{Math.round(h.avg_price).toLocaleString()}</div>
                  </div>
                </Link>
              </li>
            ))}
          </ul>
        )}
      </CardBody>
    </Card>
  );
};
```

- [ ] **Step 2: ビルド + コミット**

```bash
cd frontend && npm run build
git add frontend/src/components/home/HoldingsQuickCard.tsx
git commit -m "feat(home): implement holdings quick card"
```

### Task B10: LatestSignalsCard

**Files:**
- Modify: `frontend/src/components/home/LatestSignalsCard.tsx`

- [ ] **Step 1: 実装**

```tsx
import { useEffect, useState } from 'react';
import { Link } from 'react-router-dom';
import { Card, CardHeader, CardTitle, CardBody, Badge, EmptyState } from '@/components/ui';
import { tradingviewApi } from '@/services/api/tradingviewApi';
import type { TradingViewSignal } from '@/types/tradingviewSignal';

const TONE: Record<string, 'success' | 'brand' | 'slate' | 'warn' | 'danger'> = {
  STRONG_BUY: 'success',
  BUY: 'brand',
  NEUTRAL: 'slate',
  SELL: 'warn',
  STRONG_SELL: 'danger',
};

export const LatestSignalsCard = () => {
  const [sigs, setSigs] = useState<TradingViewSignal[] | null>(null);
  useEffect(() => {
    tradingviewApi.listSignals().then((xs) => setSigs(xs.slice(0, 5))).catch(() => setSigs([]));
  }, []);

  if (sigs === null) return <Card><CardBody className="text-sm text-slate-500">読み込み中...</CardBody></Card>;

  return (
    <Card>
      <CardHeader><CardTitle>最新 TV シグナル</CardTitle></CardHeader>
      <CardBody>
        {sigs.length === 0 ? (
          <EmptyState title="シグナルがまだありません" description="ランキング画面の TVバッチ分析 から Claude に依頼してください" />
        ) : (
          <ul className="divide-y divide-slate-100">
            {sigs.map((sig) => (
              <li key={sig.id ?? sig.symbol}>
                <Link
                  to={`/stocks/${sig.symbol.replace('.T', '')}`}
                  className="flex items-center justify-between py-2.5 hover:bg-slate-50 rounded-md -mx-2 px-2"
                >
                  <div className="flex items-center gap-2">
                    <span className="text-sm font-semibold text-slate-900">{sig.symbol}</span>
                    {sig.recommendation && (
                      <Badge tone={TONE[sig.recommendation] ?? 'slate'}>
                        {sig.recommendation.replaceAll('_', ' ')}
                      </Badge>
                    )}
                  </div>
                  <span className="text-xs text-slate-500">
                    {sig.analyzed_at ? new Date(sig.analyzed_at).toLocaleString('ja-JP') : ''}
                  </span>
                </Link>
              </li>
            ))}
          </ul>
        )}
      </CardBody>
    </Card>
  );
};
```

注: `TradingViewSignal` の `id`, `analyzed_at`, `recommendation` フィールド名は既存型に合わせる。異なる場合は `frontend/src/types/tradingviewSignal.ts` を確認して修正する。

- [ ] **Step 2: ビルド + コミット**

```bash
cd frontend && npm run build
git add frontend/src/components/home/LatestSignalsCard.tsx
git commit -m "feat(home): implement latest TV signals card"
```

### Task B11: QuickSimulatorCard

**Files:**
- Modify: `frontend/src/components/home/QuickSimulatorCard.tsx`

- [ ] **Step 1: 実装**

```tsx
import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { Card, CardHeader, CardTitle, CardBody, Field, NumberInput, Button } from '@/components/ui';

export const QuickSimulatorCard = () => {
  const navigate = useNavigate();
  const [monthly, setMonthly] = useState(30_000);
  const [rate, setRate] = useState(5.0);
  const [years, setYears] = useState(20);

  const handleGo = () => {
    const params = new URLSearchParams({
      monthly: String(monthly),
      rate: String(rate),
      years: String(years),
    });
    navigate(`/simulator?${params.toString()}`);
  };

  return (
    <Card>
      <CardHeader><CardTitle>クイックシミュレータ</CardTitle></CardHeader>
      <CardBody>
        <div className="grid gap-3 sm:grid-cols-3">
          <Field label="毎月積立 (円)"><NumberInput value={monthly} onChange={setMonthly} step={1000} /></Field>
          <Field label="想定年利 (%)"><NumberInput value={rate} onChange={setRate} step={0.1} /></Field>
          <Field label="期間 (年)"><NumberInput value={years} onChange={setYears} /></Field>
        </div>
        <div className="mt-4 flex justify-end">
          <Button variant="accent" onClick={handleGo}>シミュレータで詳細 →</Button>
        </div>
      </CardBody>
    </Card>
  );
};
```

- [ ] **Step 2: ビルド + 遷移確認**

ホームのクイックカードで値を入れ「シミュレータで詳細」→ URL にクエリが載ることを確認（値の反映は Phase D で実装）。

- [ ] **Step 3: コミット**

```bash
cd frontend && npm run build
git add frontend/src/components/home/QuickSimulatorCard.tsx
git commit -m "feat(home): implement quick simulator card"
```

---

## Phase C: 主要ページ刷新

### Task C1: AddHoldingDialog（共通化）

**Files:**
- Create: `frontend/src/components/portfolio/AddHoldingDialog.tsx`

- [ ] **Step 1: 実装**

```tsx
import { useState } from 'react';
import { Dialog, Field, Input, NumberInput, Select, Button } from '@/components/ui';
import { portfolioApi } from '@/services/api/portfolioApi';

interface Props {
  open: boolean;
  onClose: () => void;
  symbol: string;
  name?: string;
  onCreated?: () => void;
}

const today = () => new Date().toISOString().slice(0, 10);

export const AddHoldingDialog = ({ open, onClose, symbol, name = '', onCreated }: Props) => {
  const [quantity, setQuantity] = useState(100);
  const [avgPrice, setAvgPrice] = useState(0);
  const [purchaseDate, setPurchaseDate] = useState(today());
  const [accountType, setAccountType] = useState<'general' | 'nisa'>('general');
  const [submitting, setSubmitting] = useState(false);
  const [success, setSuccess] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setSubmitting(true);
    setError(null);
    try {
      await portfolioApi.createHolding({
        symbol,
        name,
        quantity,
        avg_price: avgPrice,
        purchase_date: purchaseDate,
        account_type: accountType,
      });
      setSuccess(true);
      onCreated?.();
      setTimeout(() => {
        setSuccess(false);
        onClose();
      }, 1500);
    } catch {
      setError('作成に失敗しました');
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <Dialog open={open} onClose={onClose} title="ポートフォリオに追加" description={`${symbol} ${name}`}>
      <form onSubmit={handleSubmit} className="space-y-3">
        <div className="grid gap-3 sm:grid-cols-2">
          <Field label="数量"><NumberInput value={quantity} onChange={setQuantity} /></Field>
          <Field label="平均取得単価 (円)"><NumberInput value={avgPrice} onChange={setAvgPrice} /></Field>
          <Field label="購入日">
            <Input type="date" value={purchaseDate} onChange={(e) => setPurchaseDate(e.target.value)} />
          </Field>
          <Field label="口座種別">
            <Select value={accountType} onChange={(e) => setAccountType(e.target.value as 'general' | 'nisa')}>
              <option value="general">特定</option>
              <option value="nisa">NISA</option>
            </Select>
          </Field>
        </div>
        {error && <p className="text-xs text-rose-600">{error}</p>}
        {success && <p className="text-xs text-emerald-600">追加しました ✓</p>}
        <div className="flex justify-end gap-2">
          <Button type="button" variant="secondary" onClick={onClose}>キャンセル</Button>
          <Button type="submit" variant="accent" disabled={submitting}>
            {submitting ? '追加中...' : '＋ 追加'}
          </Button>
        </div>
      </form>
    </Dialog>
  );
};
```

注: `portfolioApi.createHolding` の引数型は既存 API に合わせる。引数キーが異なる場合は現行シグネチャを優先。

- [ ] **Step 2: ビルド + コミット**

```bash
cd frontend && npm run build
git add frontend/src/components/portfolio/AddHoldingDialog.tsx
git commit -m "feat(portfolio): add shared holding dialog component"
```

### Task C2: StockRankingPage 刷新

**Files:**
- Modify: `frontend/src/pages/StockRankingPage.tsx`

- [ ] **Step 1: Tailwind ベースに全面書き換え**

```tsx
import { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { scoresApi } from '@/services/api/scoresApi';
import type { StockScore, BatchStatus, ProfileKey } from '@/types/stockScore';
import { tradingviewApi } from '@/services/api/tradingviewApi';
import type { TradingViewSignal } from '@/types/tradingviewSignal';
import ProfileSelector from '@/components/stock/ProfileSelector';
import {
  PageHeader, Card, CardBody, Table, Thead, Tbody, Tr, Th, Td,
  Badge, Progress, Button, EmptyState, Toolbar,
} from '@/components/ui';
import { AddHoldingDialog } from '@/components/portfolio/AddHoldingDialog';

const RATING_TONE: Record<string, 'brand' | 'success' | 'slate' | 'warn' | 'danger'> = {
  '強い買い': 'brand', '買い': 'success', '中立': 'slate', '売り': 'warn', '強い売り': 'danger',
};
const TV_TONE: Record<string, 'success' | 'brand' | 'slate' | 'warn' | 'danger'> = {
  STRONG_BUY: 'success', BUY: 'brand', NEUTRAL: 'slate', SELL: 'warn', STRONG_SELL: 'danger',
};

const StockRankingPage = () => {
  const navigate = useNavigate();
  const [scores, setScores] = useState<StockScore[]>([]);
  const [batchStatus, setBatchStatus] = useState<BatchStatus | null>(null);
  const [tvSignals, setTvSignals] = useState<Record<string, TradingViewSignal>>({});
  const [profile, setProfile] = useState<ProfileKey | 'none'>('none');
  const [loading, setLoading] = useState(true);
  const [addTarget, setAddTarget] = useState<StockScore | null>(null);

  useEffect(() => {
    setLoading(true);
    const profileParam: ProfileKey | undefined = profile === 'none' ? undefined : profile;
    Promise.all([
      scoresApi.listScores('total_score', 100, profileParam),
      scoresApi.getBatchStatus(),
      tradingviewApi.listSignals().catch(() => [] as TradingViewSignal[]),
    ])
      .then(([s, b, tv]) => {
        setScores(s);
        setBatchStatus(b);
        const map: Record<string, TradingViewSignal> = {};
        tv.forEach((sig) => { map[sig.symbol] = sig; });
        setTvSignals(map);
      })
      .finally(() => setLoading(false));
  }, [profile]);

  const lastUpdated = batchStatus?.finished_at
    ? new Date(batchStatus.finished_at).toLocaleString('ja-JP')
    : '未実行';

  return (
    <>
      <PageHeader
        title="銘柄スコアランキング"
        description={`最終更新: ${lastUpdated}${batchStatus?.status === 'running' ? ' (実行中...)' : ''}`}
      />

      <Toolbar>
        <ProfileSelector value={profile} onChange={setProfile} />
      </Toolbar>

      {loading ? (
        <Card><CardBody className="text-sm text-slate-500">読み込み中...</CardBody></Card>
      ) : scores.length === 0 ? (
        <EmptyState
          title="スコアデータがありません"
          description="ヘッダーの ▶ バッチ からスコアリングを開始してください"
        />
      ) : (
        <>
          {/* Desktop table */}
          <div className="hidden md:block">
            <Table>
              <Thead>
                <Tr>
                  <Th className="w-10">#</Th>
                  <Th>銘柄</Th>
                  <Th>{profile === 'none' ? '総合スコア' : scores[0]?.profile_name ?? 'プロファイル'}</Th>
                  <Th>レーティング</Th>
                  <Th>ファンダ</Th>
                  <Th>テクニカル</Th>
                  <Th>TVシグナル</Th>
                  <Th className="w-24"></Th>
                </Tr>
              </Thead>
              <Tbody>
                {scores.map((s, i) => {
                  const tvSig = tvSignals[s.symbol.replace('.T', '')];
                  const shownScore = profile === 'none' ? s.total_score : (s.profile_score ?? s.total_score);
                  return (
                    <Tr key={s.id} className="group">
                      <Td className="text-slate-400 tabular-nums">{i + 1}</Td>
                      <Td>
                        <button
                          onClick={() => navigate(`/stocks/${s.symbol.replace('.T', '')}`)}
                          className="text-left"
                        >
                          <div className="font-semibold text-slate-900">{s.symbol}</div>
                          <div className="text-xs text-slate-500">{s.name}</div>
                        </button>
                      </Td>
                      <Td>
                        <div className="flex items-center gap-2 w-40">
                          <Progress value={shownScore ?? 0} />
                          <span className="text-xs font-semibold text-brand-600 tabular-nums w-8">
                            {Math.round(shownScore ?? 0)}
                          </span>
                        </div>
                      </Td>
                      <Td>{s.rating ? <Badge tone={RATING_TONE[s.rating] ?? 'slate'}>{s.rating}</Badge> : '—'}</Td>
                      <Td className="tabular-nums text-sky-600 font-semibold">
                        {s.fundamental_score !== null ? Math.round(s.fundamental_score) : '—'}
                      </Td>
                      <Td className="tabular-nums text-emerald-600 font-semibold">
                        {s.technical_score !== null ? Math.round(s.technical_score) : '—'}
                      </Td>
                      <Td>
                        {tvSig ? (
                          <Badge tone={TV_TONE[tvSig.recommendation ?? ''] ?? 'slate'}>
                            {(tvSig.recommendation ?? '—').replaceAll('_', ' ')}
                          </Badge>
                        ) : '—'}
                      </Td>
                      <Td>
                        <div className="flex gap-1 opacity-0 group-hover:opacity-100 transition-opacity">
                          <Button
                            size="icon"
                            variant="ghost"
                            aria-label="保有に追加"
                            onClick={() => setAddTarget(s)}
                          >＋</Button>
                          <Button
                            size="sm"
                            variant="secondary"
                            onClick={() => navigate(`/stocks/${s.symbol.replace('.T', '')}`)}
                          >詳細</Button>
                        </div>
                      </Td>
                    </Tr>
                  );
                })}
              </Tbody>
            </Table>
          </div>

          {/* Mobile cards */}
          <div className="md:hidden space-y-3">
            {scores.map((s, i) => {
              const tvSig = tvSignals[s.symbol.replace('.T', '')];
              const shownScore = profile === 'none' ? s.total_score : (s.profile_score ?? s.total_score);
              return (
                <Card key={s.id}>
                  <CardBody className="space-y-2">
                    <div className="flex items-center justify-between">
                      <div>
                        <div className="text-xs text-slate-400">#{i + 1}</div>
                        <div className="font-semibold text-slate-900">{s.symbol}</div>
                        <div className="text-xs text-slate-500">{s.name}</div>
                      </div>
                      {s.rating && <Badge tone={RATING_TONE[s.rating] ?? 'slate'}>{s.rating}</Badge>}
                    </div>
                    <Progress value={shownScore ?? 0} showLabel />
                    <div className="flex gap-4 text-xs text-slate-600">
                      <span>ファンダ {s.fundamental_score ?? '—'}</span>
                      <span>テクニカル {s.technical_score ?? '—'}</span>
                      {tvSig && (
                        <Badge tone={TV_TONE[tvSig.recommendation ?? ''] ?? 'slate'}>
                          {(tvSig.recommendation ?? '—').replaceAll('_', ' ')}
                        </Badge>
                      )}
                    </div>
                    <div className="flex gap-2 pt-1">
                      <Button size="sm" variant="secondary" className="flex-1"
                        onClick={() => navigate(`/stocks/${s.symbol.replace('.T', '')}`)}>詳細</Button>
                      <Button size="sm" variant="accent" onClick={() => setAddTarget(s)}>＋ 追加</Button>
                    </div>
                  </CardBody>
                </Card>
              );
            })}
          </div>
        </>
      )}

      {addTarget && (
        <AddHoldingDialog
          open
          onClose={() => setAddTarget(null)}
          symbol={addTarget.symbol}
          name={addTarget.name ?? ''}
        />
      )}
    </>
  );
};

export default StockRankingPage;
```

- [ ] **Step 2: ビルド + 目視確認**

Run: `cd frontend && npm run build`
`/ranking` を 1280px と 375px で確認。

- [ ] **Step 3: コミット**

```bash
git add frontend/src/pages/StockRankingPage.tsx
git commit -m "feat(ranking): tailwind rewrite with mobile cards and quick actions"
```

### Task C3: StockDetailPage 刷新（Tabs + 保有追加ボタン）

**Files:**
- Modify: `frontend/src/pages/StockDetailPage.tsx`

- [ ] **Step 1: 現行を確認**

Run: `cat frontend/src/pages/StockDetailPage.tsx`

注: 実装ディテールは現行構成に依存するため、既存の `StockInfo`, `ChartAnalysisPanel`, `AnalysisAxesPanel` を Card でラップしつつ Tabs を導入する。以下テンプレ:

- [ ] **Step 2: StockDetailPage.tsx を書き換え**

```tsx
import { useParams } from 'react-router-dom';
import { useState } from 'react';
import { PageHeader, Button, Tabs, TabsList, TabsTrigger, TabsContent, Card, CardBody } from '@/components/ui';
import StockInfo from '@/components/stock/StockInfo';
import ChartAnalysisPanel from '@/components/stock/ChartAnalysisPanel';
import AnalysisAxesPanel from '@/components/stock/AnalysisAxesPanel';
import { AddHoldingDialog } from '@/components/portfolio/AddHoldingDialog';

const StockDetailPage = () => {
  const { code } = useParams<{ code: string }>();
  const [addOpen, setAddOpen] = useState(false);
  if (!code) return null;
  const symbol = `${code}.T`;

  return (
    <>
      <PageHeader
        title={`銘柄 ${code}`}
        actions={<Button variant="accent" onClick={() => setAddOpen(true)}>＋ ポートフォリオに追加</Button>}
      />

      <Tabs defaultValue="overview">
        <TabsList>
          <TabsTrigger value="overview">概要</TabsTrigger>
          <TabsTrigger value="chart">チャート</TabsTrigger>
          <TabsTrigger value="analysis">分析軸</TabsTrigger>
        </TabsList>

        <TabsContent value="overview">
          <Card><CardBody><StockInfo code={code} /></CardBody></Card>
        </TabsContent>
        <TabsContent value="chart">
          <Card><CardBody><ChartAnalysisPanel code={code} /></CardBody></Card>
        </TabsContent>
        <TabsContent value="analysis">
          <Card><CardBody><AnalysisAxesPanel code={code} /></CardBody></Card>
        </TabsContent>
      </Tabs>

      <AddHoldingDialog
        open={addOpen}
        onClose={() => setAddOpen(false)}
        symbol={symbol}
      />
    </>
  );
};

export default StockDetailPage;
```

注: `StockInfo`, `ChartAnalysisPanel`, `AnalysisAxesPanel` の props が `code` 以外を必要とする場合は現行呼び出しに合わせる。

- [ ] **Step 3: 既存の子コンポーネント内インライン style を除去（別コミット可）**

以下ファイルのインライン style を Tailwind class に置換:
- `frontend/src/components/stock/StockInfo.tsx`
- `frontend/src/components/stock/ChartAnalysisPanel.tsx`
- `frontend/src/components/stock/AnalysisAxesPanel.tsx`
- `frontend/src/components/stock/PeriodSelector.tsx`
- `frontend/src/components/stock/StockSearch.tsx`
- `frontend/src/components/stock/EvaluationResult.tsx`
- `frontend/src/components/stock/ProfileSelector.tsx`

パターン: `style={{ padding: 16, background: '#1f2937' }}` → `className="p-4 bg-slate-100"` 等、slate-50/100/200/900 と brand-600/700 を基本とする。`StockChart.tsx` は保護対象のため触らない。

- [ ] **Step 4: ビルド + 目視確認 + コミット**

```bash
cd frontend && npm run build
git add frontend/src/pages/StockDetailPage.tsx frontend/src/components/stock/
git commit -m "feat(detail): tabs layout and add-to-portfolio button"
```

### Task C4: PortfolioPage 刷新

**Files:**
- Modify: `frontend/src/pages/PortfolioPage.tsx`

- [ ] **Step 1: 現行構造を確認 → Tailwind + Dialog 化で書き換え**

```tsx
import { useEffect, useState } from 'react';
import { Link } from 'react-router-dom';
import {
  PageHeader, Button, Card, CardBody, CardHeader, CardTitle,
  Stat, Badge, Progress, Table, Thead, Tbody, Tr, Th, Td,
  Dialog, Field, Input, NumberInput, Select, EmptyState,
} from '@/components/ui';
import { portfolioApi } from '@/services/api/portfolioApi';
import type { Holding, PortfolioSummary, PortfolioSettings } from '@/types/portfolio';

const PHASE_TONE: Record<string, 'sky' | 'brand' | 'success'> = {
  '積立期': 'sky', '成長期': 'brand', '安定期': 'success',
};
const formatYen = (v: number | null | undefined) =>
  v == null ? '—' : `¥${Math.round(v).toLocaleString()}`;

const PortfolioPage = () => {
  const [summary, setSummary] = useState<PortfolioSummary | null>(null);
  const [holdings, setHoldings] = useState<Holding[]>([]);
  const [settings, setSettings] = useState<PortfolioSettings | null>(null);
  const [settingsOpen, setSettingsOpen] = useState(false);
  const [addOpen, setAddOpen] = useState(false);

  const reload = () => {
    portfolioApi.getSummary().then(setSummary).catch(() => setSummary(null));
    portfolioApi.listHoldings().then(setHoldings).catch(() => setHoldings([]));
    portfolioApi.getSettings().then(setSettings).catch(() => setSettings(null));
  };
  useEffect(reload, []);

  const handleDelete = async (id: number) => {
    if (!confirm('削除しますか?')) return;
    await portfolioApi.deleteHolding(id);
    reload();
  };

  return (
    <>
      <PageHeader
        title="ポートフォリオ"
        actions={
          <div className="flex gap-2">
            <Button variant="secondary" onClick={() => setSettingsOpen(true)}>⚙ 設定</Button>
            <Button variant="accent" onClick={() => setAddOpen(true)}>＋ 保有追加</Button>
          </div>
        }
      />

      <div className="grid gap-4 grid-cols-2 lg:grid-cols-4 mb-6">
        <Stat label="評価額" value={formatYen(summary?.total_value)} accent="brand" />
        <Stat
          label="目標進捗"
          value={summary?.progress_rate != null ? `${summary.progress_rate.toFixed(1)}%` : '—'}
          hint={summary?.progress_rate != null ? <Progress value={summary.progress_rate} /> : '目標未設定'}
          accent="success"
        />
        <Stat
          label="フェーズ"
          value={summary?.current_phase ? <Badge tone={PHASE_TONE[summary.current_phase] ?? 'slate'}>{summary.current_phase}</Badge> : '—'}
        />
        <Stat label="NISA残枠" value={formatYen(summary?.nisa_remaining)} hint="年間 ¥2,400,000" />
      </div>

      <Card>
        <CardHeader><CardTitle>保有銘柄</CardTitle></CardHeader>
        <CardBody>
          {holdings.length === 0 ? (
            <EmptyState
              title="まだ保有銘柄がありません"
              action={<Button variant="accent" onClick={() => setAddOpen(true)}>＋ 追加</Button>}
            />
          ) : (
            <Table>
              <Thead>
                <Tr>
                  <Th>銘柄</Th>
                  <Th>数量</Th>
                  <Th>平均単価</Th>
                  <Th>購入日</Th>
                  <Th>口座</Th>
                  <Th></Th>
                </Tr>
              </Thead>
              <Tbody>
                {holdings.map((h) => (
                  <Tr key={h.id}>
                    <Td>
                      <Link
                        to={`/stocks/${h.symbol.replace('.T', '')}`}
                        className="text-brand-600 hover:underline font-semibold"
                      >
                        {h.symbol}
                      </Link>
                      <div className="text-xs text-slate-500">{h.name}</div>
                    </Td>
                    <Td className="tabular-nums">{h.quantity}</Td>
                    <Td className="tabular-nums">¥{Math.round(h.avg_price).toLocaleString()}</Td>
                    <Td className="text-slate-500">{h.purchase_date}</Td>
                    <Td><Badge tone={h.account_type === 'nisa' ? 'success' : 'slate'}>{h.account_type}</Badge></Td>
                    <Td>
                      <Button size="sm" variant="ghost" onClick={() => handleDelete(h.id)}>削除</Button>
                    </Td>
                  </Tr>
                ))}
              </Tbody>
            </Table>
          )}
        </CardBody>
      </Card>

      <Dialog open={settingsOpen} onClose={() => setSettingsOpen(false)} title="ポートフォリオ設定">
        <PortfolioSettingsForm
          initial={settings}
          onSaved={() => {
            setSettingsOpen(false);
            reload();
          }}
        />
      </Dialog>

      <Dialog open={addOpen} onClose={() => setAddOpen(false)} title="保有銘柄を追加">
        <AddHoldingForm onCreated={() => {
          setAddOpen(false);
          reload();
        }} />
      </Dialog>
    </>
  );
};

interface SettingsFormProps {
  initial: PortfolioSettings | null;
  onSaved: () => void;
}
const PortfolioSettingsForm = ({ initial, onSaved }: SettingsFormProps) => {
  const [targetAmount, setTargetAmount] = useState(initial?.target_amount ?? 2_000_000);
  const [targetDeadline, setTargetDeadline] = useState(initial?.target_deadline ?? '2028-12-31');
  const [monthly, setMonthly] = useState(initial?.monthly_investment ?? 30_000);
  const [nisa, setNisa] = useState(initial?.nisa_used_current_year ?? 0);
  const [saving, setSaving] = useState(false);

  const submit = async (e: React.FormEvent) => {
    e.preventDefault();
    setSaving(true);
    try {
      await portfolioApi.updateSettings({
        target_amount: targetAmount,
        target_deadline: targetDeadline,
        monthly_investment: monthly,
        nisa_used_current_year: nisa,
      });
      onSaved();
    } finally {
      setSaving(false);
    }
  };

  return (
    <form onSubmit={submit} className="space-y-3">
      <div className="grid gap-3 sm:grid-cols-2">
        <Field label="目標額 (円)"><NumberInput value={targetAmount} onChange={setTargetAmount} step={100_000} /></Field>
        <Field label="目標期限"><Input type="date" value={targetDeadline} onChange={(e) => setTargetDeadline(e.target.value)} /></Field>
        <Field label="毎月積立 (円)"><NumberInput value={monthly} onChange={setMonthly} step={1000} /></Field>
        <Field label="NISA 使用額 (円)"><NumberInput value={nisa} onChange={setNisa} step={10_000} /></Field>
      </div>
      <div className="flex justify-end">
        <Button type="submit" variant="accent" disabled={saving}>{saving ? '保存中...' : '保存'}</Button>
      </div>
    </form>
  );
};

interface AddFormProps { onCreated: () => void }
const AddHoldingForm = ({ onCreated }: AddFormProps) => {
  const [symbol, setSymbol] = useState('');
  const [name, setName] = useState('');
  const [quantity, setQuantity] = useState(100);
  const [avgPrice, setAvgPrice] = useState(0);
  const [purchaseDate, setPurchaseDate] = useState(new Date().toISOString().slice(0, 10));
  const [accountType, setAccountType] = useState<'general' | 'nisa'>('general');
  const [submitting, setSubmitting] = useState(false);

  const submit = async (e: React.FormEvent) => {
    e.preventDefault();
    setSubmitting(true);
    try {
      await portfolioApi.createHolding({
        symbol: symbol.includes('.') ? symbol : `${symbol}.T`,
        name,
        quantity,
        avg_price: avgPrice,
        purchase_date: purchaseDate,
        account_type: accountType,
      });
      onCreated();
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <form onSubmit={submit} className="space-y-3">
      <div className="grid gap-3 sm:grid-cols-2">
        <Field label="銘柄コード"><Input placeholder="7203" value={symbol} onChange={(e) => setSymbol(e.target.value)} required /></Field>
        <Field label="銘柄名"><Input value={name} onChange={(e) => setName(e.target.value)} /></Field>
        <Field label="数量"><NumberInput value={quantity} onChange={setQuantity} /></Field>
        <Field label="平均単価 (円)"><NumberInput value={avgPrice} onChange={setAvgPrice} /></Field>
        <Field label="購入日"><Input type="date" value={purchaseDate} onChange={(e) => setPurchaseDate(e.target.value)} /></Field>
        <Field label="口座種別">
          <Select value={accountType} onChange={(e) => setAccountType(e.target.value as 'general' | 'nisa')}>
            <option value="general">特定</option>
            <option value="nisa">NISA</option>
          </Select>
        </Field>
      </div>
      <div className="flex justify-end">
        <Button type="submit" variant="accent" disabled={submitting}>{submitting ? '追加中...' : '＋ 追加'}</Button>
      </div>
    </form>
  );
};

export default PortfolioPage;
```

注: `PortfolioSettings` 型、`portfolioApi.updateSettings` / `deleteHolding` / `createHolding` の引数は既存 API に合わせる。異なる場合は現行呼び出しを優先して本タスクコード側を修正。`PhaseIndicator` コンポーネントは Stat に置換したため不要だが、既存ファイルは Phase D で削除。

- [ ] **Step 2: ビルド + 目視確認 + コミット**

```bash
cd frontend && npm run build
git add frontend/src/pages/PortfolioPage.tsx
git commit -m "feat(portfolio): tailwind rewrite with dialog-based forms"
```

---

## Phase D: 補助ページ + 最終掃除

### Task D1: SimulatorPage 刷新 + URL クエリ対応

**Files:**
- Modify: `frontend/src/pages/SimulatorPage.tsx`

- [ ] **Step 1: 書き換え**

```tsx
import { useEffect, useState } from 'react';
import { useSearchParams } from 'react-router-dom';
import { advisorApi } from '@/services/api/advisorApi';
import FutureValueChart from '@/components/advisor/FutureValueChart';
import type { SimulateResponse } from '@/types/advisor';
import {
  PageHeader, Card, CardHeader, CardTitle, CardBody,
  Stat, Button, Field, NumberInput,
} from '@/components/ui';

const formatYen = (v: number) => `¥${Math.round(v).toLocaleString()}`;

const SimulatorPage = () => {
  const [params] = useSearchParams();
  const [pv, setPv] = useState(Number(params.get('pv') ?? 1_000_000));
  const [monthly, setMonthly] = useState(Number(params.get('monthly') ?? 50_000));
  const [rate, setRate] = useState(Number(params.get('rate') ?? 5.0));
  const [years, setYears] = useState(Number(params.get('years') ?? 20));
  const [result, setResult] = useState<SimulateResponse | null>(null);
  const [loading, setLoading] = useState(false);

  const [goal, setGoal] = useState(20_000_000);
  const [requiredMsg, setRequiredMsg] = useState<string>('');

  const handleSimulate = async () => {
    setLoading(true);
    try {
      const res = await advisorApi.simulate({
        pv,
        monthly_investment: monthly,
        annual_rate: rate / 100,
        years,
      });
      setResult(res);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    // URL クエリで値が渡されたら初回自動実行
    if (params.get('monthly') || params.get('rate')) {
      void handleSimulate();
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  const handleRequiredRate = async () => {
    const res = await advisorApi.requiredRate({
      goal, pv, n_months: years * 12, monthly_investment: monthly,
    });
    setRequiredMsg(
      res.annual_rate_percent == null
        ? '計算不能'
        : res.annual_rate_percent > 200
          ? '実質到達不可能'
          : `必要年利: ${res.annual_rate_percent}%`
    );
  };

  return (
    <>
      <PageHeader title="将来価値シミュレータ" description="積立と想定年利から将来評価額を試算" />

      <Card className="mb-6">
        <CardHeader><CardTitle>入力</CardTitle></CardHeader>
        <CardBody>
          <div className="grid gap-3 sm:grid-cols-2 lg:grid-cols-4">
            <Field label="現在評価額 (円)"><NumberInput value={pv} onChange={setPv} step={10_000} /></Field>
            <Field label="毎月積立 (円)"><NumberInput value={monthly} onChange={setMonthly} step={1000} /></Field>
            <Field label="想定年利 (%)"><NumberInput value={rate} onChange={setRate} step={0.1} /></Field>
            <Field label="期間 (年)"><NumberInput value={years} onChange={setYears} /></Field>
          </div>
          <div className="mt-4 flex justify-end">
            <Button variant="accent" onClick={handleSimulate} disabled={loading}>
              {loading ? '計算中...' : '▶ 実行'}
            </Button>
          </div>
        </CardBody>
      </Card>

      {result && (
        <>
          <div className="grid gap-4 grid-cols-1 sm:grid-cols-3 mb-6">
            <Stat label="最終評価額" value={formatYen(result.final_value)} accent="brand" />
            <Stat label="拠出累計" value={formatYen(result.total_contributed)} />
            <Stat
              label="運用益"
              value={formatYen(result.total_gain)}
              accent={result.total_gain >= 0 ? 'success' : 'danger'}
            />
          </div>
          <Card className="mb-6">
            <CardBody>
              <FutureValueChart data={result.timeseries} />
            </CardBody>
          </Card>
        </>
      )}

      <Card>
        <CardHeader><CardTitle>必要年利逆算</CardTitle></CardHeader>
        <CardBody>
          <div className="flex flex-wrap items-end gap-3">
            <Field label="目標額 (円)"><NumberInput value={goal} onChange={setGoal} step={100_000} /></Field>
            <Button variant="secondary" onClick={handleRequiredRate}>計算</Button>
            {requiredMsg && <span className="text-sm text-slate-700">{requiredMsg}</span>}
          </div>
        </CardBody>
      </Card>
    </>
  );
};

export default SimulatorPage;
```

- [ ] **Step 2: FutureValueChart の軸色とフォントを light テーマに合わせる**

`frontend/src/components/advisor/FutureValueChart.tsx` を編集:
- `stroke="#1f2937"` → `stroke="#e2e8f0"`（グリッド）
- `fill="#6b7280"` → `fill="#64748b"`（テキスト）
- `background:'#0f172a'` → `background:'#ffffff'`
- グラデーション stop の色はそのまま

全体を Tailwind wrapper 内に置き、SVG は `className="w-full h-auto"` に変更（`width/height` props は max 制限として残す）。

- [ ] **Step 3: ビルド + 目視 + コミット**

```bash
cd frontend && npm run build
git add frontend/src/pages/SimulatorPage.tsx frontend/src/components/advisor/FutureValueChart.tsx
git commit -m "feat(simulator): tailwind rewrite and URL query prefill"
```

### Task D2: AnalysisHistoryPage 刷新

**Files:**
- Modify: `frontend/src/pages/AnalysisHistoryPage.tsx`

- [ ] **Step 1: 書き換え**

```tsx
import { useEffect, useState } from 'react';
import { advisorApi } from '@/services/api/advisorApi';
import type { HistoryEntry } from '@/types/advisor';
import { PageHeader, Card, CardBody, Table, Thead, Tbody, Tr, Th, Td, EmptyState } from '@/components/ui';

const formatYen = (v: unknown) => {
  const n = Number(v);
  if (Number.isNaN(n)) return '—';
  return `¥${Math.round(n).toLocaleString()}`;
};

const AnalysisHistoryPage = () => {
  const [entries, setEntries] = useState<HistoryEntry[] | null>(null);

  useEffect(() => {
    advisorApi.listHistory().then(setEntries).catch(() => setEntries([]));
  }, []);

  if (entries === null) {
    return <Card><CardBody className="text-sm text-slate-500">読み込み中...</CardBody></Card>;
  }

  return (
    <>
      <PageHeader title="シミュレーション履歴" description="過去の将来価値計算ログ" />

      {entries.length === 0 ? (
        <EmptyState
          title="履歴がありません"
          description="シミュレータから計算を実行すると記録されます"
        />
      ) : (
        <>
          {/* Desktop */}
          <div className="hidden md:block">
            <Table>
              <Thead>
                <Tr>
                  <Th>日時</Th><Th>現在額</Th><Th>積立</Th><Th>年利</Th><Th>期間</Th><Th>最終評価額</Th><Th>運用益</Th>
                </Tr>
              </Thead>
              <Tbody>
                {entries.map((e) => {
                  const i = e.input_json as Record<string, number>;
                  const r = e.result_json as Record<string, number>;
                  return (
                    <Tr key={e.id}>
                      <Td className="text-slate-500">{new Date(e.created_at).toLocaleString('ja-JP')}</Td>
                      <Td className="tabular-nums">{formatYen(i.pv)}</Td>
                      <Td className="tabular-nums">{formatYen(i.monthly_investment)}/月</Td>
                      <Td className="tabular-nums">{((i.annual_rate ?? 0) * 100).toFixed(2)}%</Td>
                      <Td>{i.years}年</Td>
                      <Td className="tabular-nums font-semibold text-brand-600">{formatYen(r.final_value)}</Td>
                      <Td className={`tabular-nums font-semibold ${(r.total_gain ?? 0) >= 0 ? 'text-emerald-600' : 'text-rose-600'}`}>
                        {formatYen(r.total_gain)}
                      </Td>
                    </Tr>
                  );
                })}
              </Tbody>
            </Table>
          </div>

          {/* Mobile */}
          <div className="md:hidden space-y-3">
            {entries.map((e) => {
              const i = e.input_json as Record<string, number>;
              const r = e.result_json as Record<string, number>;
              return (
                <Card key={e.id}>
                  <CardBody className="space-y-1.5">
                    <div className="text-xs text-slate-500">{new Date(e.created_at).toLocaleString('ja-JP')}</div>
                    <div className="text-lg font-bold text-brand-600 tabular-nums">{formatYen(r.final_value)}</div>
                    <div className="text-xs text-slate-600">
                      {formatYen(i.pv)} + {formatYen(i.monthly_investment)}/月 × {i.years}年 @ {((i.annual_rate ?? 0) * 100).toFixed(1)}%
                    </div>
                    <div className={`text-xs font-semibold ${(r.total_gain ?? 0) >= 0 ? 'text-emerald-600' : 'text-rose-600'}`}>
                      運用益 {formatYen(r.total_gain)}
                    </div>
                  </CardBody>
                </Card>
              );
            })}
          </div>
        </>
      )}
    </>
  );
};

export default AnalysisHistoryPage;
```

- [ ] **Step 2: ビルド + コミット**

```bash
cd frontend && npm run build
git add frontend/src/pages/AnalysisHistoryPage.tsx
git commit -m "feat(history): tailwind rewrite with mobile cards"
```

### Task D3: 最終掃除 (PhaseIndicator 削除 / サンドボックス削除 / grep ゼロ確認)

**Files:**
- Delete: `frontend/src/components/portfolio/PhaseIndicator.tsx`（未使用化した場合）
- Delete: `frontend/src/pages/__UiSandboxPage.tsx`
- Modify: `frontend/src/App.tsx`
- Modify: `frontend/src/components/common/` （ErrorMessage/Loading を ui に吸収する場合）

- [ ] **Step 1: PhaseIndicator の参照を確認**

Run: `cd frontend && grep -R "PhaseIndicator" src`
Expected: 参照がゼロなら削除。残っていれば使用箇所を Stat/Badge+Progress に置き換えてから削除。

- [ ] **Step 2: サンドボックスルート削除**

`App.tsx` から `/__ui` ルートと `UiSandboxPage` import を削除。

```tsx
import { BrowserRouter, Routes, Route } from 'react-router-dom'
import HomePage from './pages/HomePage'
import StockDetailPage from './pages/StockDetailPage'
import StockRankingPage from './pages/StockRankingPage'
import PortfolioPage from './pages/PortfolioPage'
import SimulatorPage from './pages/SimulatorPage'
import AnalysisHistoryPage from './pages/AnalysisHistoryPage'
import { AppShell } from './components/layout/AppShell'
import './App.css'

function App() {
  return (
    <BrowserRouter>
      <Routes>
        <Route element={<AppShell />}>
          <Route path="/" element={<HomePage />} />
          <Route path="/ranking" element={<StockRankingPage />} />
          <Route path="/portfolio" element={<PortfolioPage />} />
          <Route path="/simulator" element={<SimulatorPage />} />
          <Route path="/history" element={<AnalysisHistoryPage />} />
          <Route path="/stocks/:code" element={<StockDetailPage />} />
        </Route>
      </Routes>
    </BrowserRouter>
  )
}

export default App
```

- [ ] **Step 3: インライン style ゼロ確認**

Run: `cd frontend && grep -rn 'style={{' src | grep -v StockChart | grep -v FutureValueChart`
Expected: 出力ゼロ（SVG 内の style を持つ FutureValueChart と StockChart は例外）

もし残っていたら順次 Tailwind class に置換してからコミットする。

- [ ] **Step 4: 未使用ファイル削除**

```bash
rm frontend/src/pages/__UiSandboxPage.tsx
# PhaseIndicator が未参照なら
rm frontend/src/components/portfolio/PhaseIndicator.tsx
```

- [ ] **Step 5: ビルド + 全ルート回帰確認**

Run: `cd frontend && npm run build`
ブラウザで以下を順番に確認:

- `/` ダッシュボードの 4 KPI + TOP5 + 保有 + シグナル + クイックシミュが表示
- TOP5 行クリック → `/stocks/:code`
- `⌘K` → Dialog → 7203 → 詳細ページ遷移
- 詳細「＋ ポートフォリオに追加」→ Dialog 作成成功
- `/portfolio` 銘柄リンク → 詳細へ
- `/ranking` デスクトップ幅でテーブル、375px 幅で Card リスト
- ランキング行ホバー → クイックアクション出現、＋ で AddHoldingDialog
- `/simulator` 入力 → 実行 → グラフ描画
- ホームクイックシミュ「詳細 →」→ `/simulator?monthly=...` で値が反映され自動実行
- `/history` テーブルと Card 表示

- [ ] **Step 6: コミット**

```bash
git add -A frontend/src
git commit -m "chore(ui): cleanup sandbox, phase indicator, and stray inline styles"
```

---

## 全体検証チェックリスト（Phase D 完了時）

- [ ] `npm run build` エラー 0
- [ ] `grep -rn 'style={{' frontend/src | grep -vE 'StockChart|FutureValueChart'` が 0 件
- [ ] `/` `/ranking` `/portfolio` `/simulator` `/history` `/stocks/7203` すべて描画
- [ ] ヘッダーのリンク `isActive` ハイライト確認（デスクトップ）
- [ ] 375px / 768px / 1280px で崩れなし
- [ ] `⌘K` / `Ctrl+K` でグローバル検索 Dialog
- [ ] ヘッダー `▶ バッチ` → Dialog でポーリング表示
- [ ] 導線 A: 詳細 → 「＋ ポートフォリオに追加」→ 成功
- [ ] 導線 B: ポートフォリオの銘柄 Link → 詳細
- [ ] 導線 C: ランキング行ホバー → クイックアクション → AddHoldingDialog
- [ ] 導線 D: ホーム TOP5 / 保有 / シグナルカード → 各詳細ページ
- [ ] 導線 G: `⌘K` から銘柄コード入力で詳細遷移
- [ ] ホームクイックシミュ → クエリ引き継ぎで SimulatorPage 自動実行

## セルフレビュー結果

1. **Spec coverage**: 5 セクション（基盤 / AppShell / ホーム / ページ別 / ロールアウト）すべてに対応タスクあり。A16 サンドボックス、D3 で削除まで仕様どおり。
2. **Placeholder scan**: "TBD"/"TODO"/"実装 later" なし。すべてのコードは動作可能形で記載。
3. **Type consistency**: `PortfolioSummary`, `StockScore`, `TradingViewSignal`, `SimulateResponse`, `HistoryEntry` を一貫使用。`ProfileKey | 'none'` の表記も統一。
4. **Ambiguity**: `AddHoldingDialog` は C1 で共通化し、C2（ランキング）/ C3（詳細）から呼ぶ。PortfolioPage の Add フォームは Dialog 内独立フォーム (`AddHoldingForm`) と使い分ける（引数の `symbol` が予め決まっているか否かの差）。`StockDetailPage` の子コンポーネント props は現行シグネチャを優先して必要に応じ差分吸収する旨を注記済み。
