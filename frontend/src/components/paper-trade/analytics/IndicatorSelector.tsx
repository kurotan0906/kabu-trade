import { useState } from 'react';
import { Button, Dialog } from '@/components/ui';
import type { IndicatorDef } from './registry';

interface Props {
  registry: IndicatorDef[];
  visibleIds: string[];
  onChange: (ids: string[]) => void;
}

export const IndicatorSelector = ({ registry, visibleIds, onChange }: Props) => {
  const [open, setOpen] = useState(false);

  const toggle = (id: string) => {
    if (visibleIds.includes(id)) onChange(visibleIds.filter((v) => v !== id));
    else onChange([...visibleIds, id]);
  };

  const basic = registry.filter((r) => r.category === 'basic');
  const advanced = registry.filter((r) => r.category === 'advanced');

  return (
    <>
      <Button variant="secondary" size="sm" onClick={() => setOpen(true)}>
        表示項目を選択
      </Button>
      <Dialog open={open} onClose={() => setOpen(false)} title="表示する分析項目" size="sm">
        <div className="flex flex-col gap-3">
          <div>
            <div className="mb-2 text-xs font-semibold text-slate-500">基本指標</div>
            {basic.map((ind) => (
              <label key={ind.id} className="flex cursor-pointer items-center gap-2 py-1 text-sm">
                <input
                  type="checkbox"
                  checked={visibleIds.includes(ind.id)}
                  onChange={() => toggle(ind.id)}
                />
                <span>{ind.label}</span>
                {ind.description && (
                  <span className="text-xs text-slate-500">{ind.description}</span>
                )}
              </label>
            ))}
          </div>
          {advanced.length > 0 && (
            <div>
              <div className="mb-2 text-xs font-semibold text-slate-500">詳細指標</div>
              {advanced.map((ind) => (
                <label key={ind.id} className="flex cursor-pointer items-center gap-2 py-1 text-sm">
                  <input
                    type="checkbox"
                    checked={visibleIds.includes(ind.id)}
                    onChange={() => toggle(ind.id)}
                  />
                  <span>{ind.label}</span>
                  {ind.description && (
                    <span className="text-xs text-slate-500">{ind.description}</span>
                  )}
                </label>
              ))}
            </div>
          )}
          <div className="flex justify-end pt-2">
            <Button variant="accent" onClick={() => setOpen(false)}>閉じる</Button>
          </div>
        </div>
      </Dialog>
    </>
  );
};

export default IndicatorSelector;
