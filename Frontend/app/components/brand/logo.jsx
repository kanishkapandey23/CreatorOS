import Link from 'next/link';
import { cn } from '@/lib/utils';

export function Logo({ href = '/', collapsed = false, className }) {
  return (
    <Link
      href={href}
      className={cn(
        'inline-flex items-center gap-2 font-display font-semibold text-ink',
        className
      )}
    >
      <span className="relative inline-flex h-8 w-8 items-center justify-center rounded-xl bg-ink text-white shadow-soft">
        <span className="absolute -right-0.5 -top-0.5 h-2 w-2 rounded-full bg-brand ring-2 ring-canvas" />
        <span className="text-[13px] font-display tracking-tight">C</span>
      </span>
      {!collapsed && (
        <span className="text-[15px] tracking-tight">
          Creator<span className="text-ink">OS</span>
        </span>
      )}
    </Link>
  );
}
