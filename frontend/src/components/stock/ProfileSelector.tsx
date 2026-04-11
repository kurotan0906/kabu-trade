import type { ProfileKey } from '@/types/stockScore';

interface Props {
  value: ProfileKey | 'none';
  onChange: (v: ProfileKey | 'none') => void;
  showAuto?: boolean;
}

const TABS: { key: ProfileKey | 'none'; label: string; color: string }[] = [
  { key: 'none', label: '総合', color: '#a78bfa' },
  { key: 'growth', label: '成長型', color: '#10b981' },
  { key: 'balanced', label: 'バランス型', color: '#3b82f6' },
  { key: 'income', label: 'インカム型', color: '#f59e0b' },
  { key: 'auto', label: '自動 (フェーズ)', color: '#ec4899' },
];

const ProfileSelector = ({ value, onChange, showAuto = true }: Props) => {
  const tabs = showAuto ? TABS : TABS.filter((t) => t.key !== 'auto');
  return (
    <div style={{ display: 'flex', gap: 4, background: '#1f2937', padding: 4, borderRadius: 8 }}>
      {tabs.map((t) => {
        const active = value === t.key;
        return (
          <button
            key={t.key}
            onClick={() => onChange(t.key)}
            style={{
              padding: '6px 14px',
              fontSize: 12,
              fontWeight: 600,
              background: active ? t.color : 'transparent',
              color: active ? '#0f172a' : '#9ca3af',
              border: 'none',
              borderRadius: 6,
              cursor: 'pointer',
              transition: 'all 0.15s',
            }}
          >
            {t.label}
          </button>
        );
      })}
    </div>
  );
};

export default ProfileSelector;
