import { cn } from '@/lib/utils';

export function EmptyState({ icon: Icon, title, description, action, className }) {
  return (
    <div
      className={cn(
        'flex flex-col items-center justify-center rounded-2xl border border-dashed border-line bg-card/60 px-6 py-14 text-center',
        className
      )}
    >
      {Icon && (
        <div className="mb-3 inline-flex h-10 w-10 items-center justify-center rounded-xl bg-secondary text-ink-muted">
          <Icon className="h-5 w-5" />
        </div>
      )}
      <h3 className="font-display text-[16px] font-semibold text-ink">{title}</h3>
      {description && (
        <p className="mt-1.5 max-w-sm text-[13px] leading-relaxed text-ink-muted">{description}</p>
      )}
      {action && <div className="mt-5">{action}</div>}
    </div>
  );
}
