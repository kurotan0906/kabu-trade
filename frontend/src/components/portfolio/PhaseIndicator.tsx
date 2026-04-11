interface Props {
  phase: string | null;
  progressRate: number | null;
  profileName?: string | null;
}

const PHASE_META: Record<string, { color: string; bg: string; desc: string }> = {
  積立期: {
    color: '#10b981',
    bg: '#10b98122',
    desc: '進捗30%未満 — 高リスク・高成長を追求',
  },
  成長期: {
    color: '#3b82f6',
    bg: '#3b82f622',
    desc: '進捗30〜70% — 分散とバランス重視',
  },
  安定期: {
    color: '#f59e0b',
    bg: '#f59e0b22',
    desc: '進捗70%以上 — 配当・低ボラで資産保全',
  },
};

const PhaseIndicator = ({ phase, progressRate, profileName }: Props) => {
  if (!phase) {
    return (
      <div style={{ padding: 12, background: '#1f2937', borderRadius: 8, fontSize: 12, color: '#6b7280' }}>
        目標額が未設定のためフェーズ判定できません
      </div>
    );
  }
  const meta = PHASE_META[phase] ?? { color: '#9ca3af', bg: '#9ca3af22', desc: '' };
  return (
    <div style={{ padding: 14, background: meta.bg, borderLeft: `4px solid ${meta.color}`, borderRadius: 8 }}>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'baseline' }}>
        <div>
          <span style={{ fontSize: 18, fontWeight: 700, color: meta.color }}>{phase}</span>
          {profileName && (
            <span style={{ fontSize: 12, color: '#9ca3af', marginLeft: 8 }}>
              推奨プロファイル: {profileName}
            </span>
          )}
        </div>
        <span style={{ fontSize: 13, color: '#e5e7eb' }}>
          進捗 {progressRate != null ? `${progressRate.toFixed(1)}%` : '—'}
        </span>
      </div>
      <div style={{ fontSize: 11, color: '#9ca3af', marginTop: 6 }}>{meta.desc}</div>
      <div
        style={{
          marginTop: 8,
          height: 6,
          background: '#374151',
          borderRadius: 3,
          overflow: 'hidden',
        }}
      >
        <div
          style={{
            width: `${Math.min(100, Math.max(0, progressRate ?? 0))}%`,
            height: '100%',
            background: meta.color,
            transition: 'width 0.3s',
          }}
        />
      </div>
    </div>
  );
};

export default PhaseIndicator;
