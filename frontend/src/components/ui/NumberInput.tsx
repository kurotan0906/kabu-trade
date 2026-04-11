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
