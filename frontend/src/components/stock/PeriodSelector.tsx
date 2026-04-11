/**
 * Period selector component
 */

import { cn } from '@/lib/cn';

interface PeriodSelectorProps {
  currentPeriod: string;
  onPeriodChange: (period: string) => void;
}

const periods = [
  { value: '1d', label: '1日' },
  { value: '1w', label: '1週間' },
  { value: '1m', label: '1ヶ月' },
  { value: '3m', label: '3ヶ月' },
  { value: '6m', label: '6ヶ月' },
  { value: '1y', label: '1年' },
];

const PeriodSelector = ({ currentPeriod, onPeriodChange }: PeriodSelectorProps) => {
  return (
    <div className="mb-4 flex flex-wrap items-center gap-2">
      <label className="text-sm text-slate-500">期間:</label>
      {periods.map((period) => {
        const active = currentPeriod === period.value;
        return (
          <button
            key={period.value}
            onClick={() => onPeriodChange(period.value)}
            className={cn(
              'cursor-pointer rounded border px-3 py-1 text-sm',
              active
                ? 'border-brand-600 bg-brand-600 text-white'
                : 'border-slate-200 bg-slate-50 text-slate-900 hover:bg-slate-100'
            )}
          >
            {period.label}
          </button>
        );
      })}
    </div>
  );
};

export default PeriodSelector;
