'use client';

import { cn } from '@/lib/utils';

export function PageHeader({ eyebrow, title, description, children }) {
  return (
    <div className="flex flex-wrap items-end justify-between gap-4">
      <div>
        {eyebrow && (
          <p className="text-[12px] font-medium uppercase tracking-[0.18em] text-ink-subtle">{eyebrow}</p>
        )}
        <h1 className="mt-1.5 font-display text-[30px] font-semibold tracking-tight text-ink md:text-[36px]">{title}</h1>
        {description && (
          <p className="mt-1.5 max-w-xl text-[13.5px] text-ink-muted">{description}</p>
        )}
      </div>
      {children}
    </div>
  );
}
