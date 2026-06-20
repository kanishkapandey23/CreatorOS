'use client';

import { cn } from '@/lib/utils';

export function ChipSelect({ options, value, onChange, className }) {
  return (
    <div className={cn('flex flex-wrap gap-2', className)}>
      {options.map((opt) => {
        const id = typeof opt === 'string' ? opt : opt.id;
        const label = typeof opt === 'string' ? opt : opt.label;
        const selected = value === id;
        return (
          <button
            key={id}
            type="button"
            onClick={() => onChange(id)}
            className={cn(
              'rounded-full border px-3.5 py-2 text-[13px] font-medium transition-colors',
              selected
                ? 'border-ink bg-ink text-white'
                : 'border-line bg-card text-ink-muted hover:border-ink-subtle hover:text-ink'
            )}
          >
            {label}
          </button>
        );
      })}
    </div>
  );
}
