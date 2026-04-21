export interface NavItem {
  to: string;
  label: string;
  icon: string;
}

export const NAV_ITEMS: NavItem[] = [
  { to: '/', label: 'ホーム', icon: '🏠' },
  { to: '/ranking', label: 'ランキング', icon: '📊' },
  { to: '/portfolio', label: 'ポートフォリオ', icon: '💼' },
  { to: '/simulator', label: 'シミュレータ', icon: '📈' },
  { to: '/paper-trade', label: 'ペーパートレード', icon: '🧪' },
  { to: '/history', label: '履歴', icon: '📜' },
];
