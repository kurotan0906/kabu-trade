/**
 * Period selector component
 */

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
    <div style={{ marginBottom: '1rem' }}>
      <label style={{ marginRight: '0.5rem' }}>期間:</label>
      {periods.map((period) => (
        <button
          key={period.value}
          onClick={() => onPeriodChange(period.value)}
          style={{
            margin: '0 0.25rem',
            padding: '0.5rem 1rem',
            backgroundColor: currentPeriod === period.value ? '#007bff' : '#f0f0f0',
            color: currentPeriod === period.value ? 'white' : '#333',
            border: '1px solid #ccc',
            borderRadius: '4px',
            cursor: 'pointer',
          }}
        >
          {period.label}
        </button>
      ))}
    </div>
  );
};

export default PeriodSelector;
