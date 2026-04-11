import type { ProfileKey } from '@/types/stockScore';
import { cn } from '@/lib/cn';

interface Props {
  value: ProfileKey | 'none';
  onChange: (v: ProfileKey | 'none') => void;
  showAuto?: boolean;
}

const TABS: { key: ProfileKey | 'none'; label: string; activeClass: string }[] = [
  { key: 'none', label: '総合', activeClass: 'bg-violet-500 text-white' },
  { key: 'growth', label: '成長型', activeClass: 'bg-emerald-500 text-white' },
  { key: 'balanced', label: 'バランス型', activeClass: 'bg-blue-500 text-white' },
  { key: 'income', label: 'インカム型', activeClass: 'bg-amber-500 text-white' },
  { key: 'auto', label: '自動 (フェーズ)', activeClass: 'bg-pink-500 text-white' },
];

const ProfileSelector = ({ value, onChange, showAuto = true }: Props) => {
  const tabs = showAuto ? TABS : TABS.filter((t) => t.key !== 'auto');
  return (
    <div className="inline-flex gap-1 rounded-lg bg-slate-100 p-1">
      {tabs.map((t) => {
        const active = value === t.key;
        return (
          <button
            key={t.key}
            onClick={() => onChange(t.key)}
            className={cn(
              'cursor-pointer rounded-md border-none px-3.5 py-1.5 text-xs font-semibold transition-colors',
              active ? t.activeClass : 'bg-transparent text-slate-500 hover:text-slate-900'
            )}
          >
            {t.label}
          </button>
        );
      })}
    </div>
  );
};

export default ProfileSelector;
