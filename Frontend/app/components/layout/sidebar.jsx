'use client';

import Link from 'next/link';
import { usePathname } from 'next/navigation';
import { useState } from 'react';
import { ChevronsLeft, ChevronsRight, Plus } from 'lucide-react';
import { motion } from 'framer-motion';
import { Logo } from '@/components/brand/logo';
import { PRIMARY_NAV } from '@/constants/nav';
import { Button } from '@/components/ui/button';
import { cn } from '@/lib/utils';

export function Sidebar() {
  const pathname = usePathname();
  const [collapsed, setCollapsed] = useState(false);

  return (
    <aside
      className={cn(
        'sticky top-0 hidden h-screen shrink-0 border-r border-line bg-card md:flex md:flex-col',
        collapsed ? 'w-[76px]' : 'w-[252px]'
      )}
    >
      <div className="flex items-center justify-between px-4 pt-5 pb-4">
        <Logo collapsed={collapsed} />
        <button
          onClick={() => setCollapsed((v) => !v)}
          className="rounded-lg p-1.5 text-ink-muted hover:bg-secondary hover:text-ink focus-ring"
          aria-label="Toggle sidebar"
        >
          {collapsed ? <ChevronsRight className="h-4 w-4" /> : <ChevronsLeft className="h-4 w-4" />}
        </button>
      </div>

      <div className="px-3 pb-3">
        <Button
          asChild
          className={cn(
            'h-9 w-full justify-start gap-2 rounded-xl bg-ink text-white hover:bg-ink/90',
            collapsed && 'justify-center px-0'
          )}
        >
          <Link href="/reflection">
            <Plus className="h-4 w-4" />
            {!collapsed && <span className="text-[13px] font-medium">New reflection</span>}
          </Link>
        </Button>
      </div>

      <nav className="mt-1 flex-1 px-2">
        <ul className="space-y-0.5">
          {PRIMARY_NAV.map((item) => {
            const active = pathname === item.href || pathname.startsWith(item.href + '/');
            const Icon = item.icon;
            return (
              <li key={item.id}>
                <Link
                  href={item.href}
                  className={cn(
                    'group relative flex items-center gap-3 rounded-xl px-3 py-2 text-[13.5px] font-medium transition-colors',
                    active
                      ? 'bg-secondary text-ink'
                      : 'text-ink-muted hover:bg-secondary/60 hover:text-ink',
                    collapsed && 'justify-center'
                  )}
                >
                  {active && (
                    <motion.span
                      layoutId="nav-active"
                      className="absolute inset-y-1.5 left-0 w-[3px] rounded-full bg-brand"
                      transition={{ type: 'spring', stiffness: 400, damping: 30 }}
                    />
                  )}
                  <Icon className="h-[18px] w-[18px] shrink-0" />
                  {!collapsed && <span>{item.label}</span>}
                </Link>
              </li>
            );
          })}
        </ul>

        {!collapsed && (
          <div className="mt-6 px-3">
            <p className="text-[11px] font-medium uppercase tracking-wider text-ink-subtle">Collections</p>
            <ul className="mt-2 space-y-0.5">
              {['Founder Journey', 'Product', 'Writing'].map((c) => (
                <li key={c}>
                  <Link
                    href="/stories"
                    className="flex items-center gap-2 rounded-lg px-3 py-1.5 text-[13px] text-ink-muted hover:bg-secondary/60 hover:text-ink"
                  >
                    <span className="h-1.5 w-1.5 rounded-full bg-ink-subtle" />
                    {c}
                  </Link>
                </li>
              ))}
            </ul>
          </div>
        )}
      </nav>

      <div className="border-t border-line p-3">
        {!collapsed ? (
          <div className="rounded-xl bg-secondary/60 p-3">
            <p className="text-[12.5px] font-medium text-ink">CreatorOS is in private beta</p>
            <p className="mt-0.5 text-[11.5px] leading-relaxed text-ink-muted">
              You're shaping a calmer space for creators.
            </p>
          </div>
        ) : (
          <div className="flex justify-center">
            <span className="h-2 w-2 rounded-full bg-brand" />
          </div>
        )}
      </div>
    </aside>
  );
}
