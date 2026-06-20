'use client';

import { useState } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import Link from 'next/link';
import { useRouter } from 'next/navigation';
import { motion, AnimatePresence } from 'framer-motion';
import {
  Bell,
  X,
  CalendarRange,
  Compass,
  PenLine,
  Check,
  Clock,
  Sparkles,
} from 'lucide-react';
import { Button } from '@/components/ui/button';
import { notificationService } from '@/services/notification.service';

const TYPE_ICONS = {
  reminder: Clock,
  nudge: Sparkles,
  overdue: CalendarRange,
  digest: Bell,
  strategy: Compass,
};

export function NotificationPanel({ open, onClose }) {
  const router = useRouter();
  const queryClient = useQueryClient();

  const { data, isLoading } = useQuery({
    queryKey: ['notifications'],
    queryFn: () => notificationService.list(),
    enabled: open,
    refetchInterval: open ? 60000 : false,
  });

  const { data: digest } = useQuery({
    queryKey: ['notifications', 'digest'],
    queryFn: () => notificationService.getDigest(),
    enabled: open,
  });

  const actionMutation = useMutation({
    mutationFn: async ({ id, action, href }) => {
      await notificationService.markRead(id);
      if (action === 'dismiss') return notificationService.dismiss(id);
      if (action === 'complete') return notificationService.markComplete(id);
      return null;
    },
    onSuccess: (_, vars) => {
      queryClient.invalidateQueries({ queryKey: ['notifications'] });
      if (vars.href && vars.action !== 'dismiss') {
        onClose();
        router.push(vars.href);
      }
    },
  });

  const notifications = data?.notifications || [];
  const unread = data?.unreadCount || 0;

  return (
    <AnimatePresence>
      {open && (
        <>
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            className="fixed inset-0 z-40 bg-ink/10 backdrop-blur-[1px]"
            onClick={onClose}
          />
          <motion.aside
            initial={{ opacity: 0, x: 16 }}
            animate={{ opacity: 1, x: 0 }}
            exit={{ opacity: 0, x: 16 }}
            transition={{ duration: 0.25 }}
            className="fixed right-0 top-14 z-50 flex h-[calc(100vh-3.5rem)] w-full max-w-md flex-col border-l border-line bg-canvas shadow-pop"
          >
            <div className="flex items-center justify-between border-b border-line px-5 py-4">
              <div>
                <p className="font-display text-[17px] font-semibold text-ink">Notifications</p>
                <p className="text-[12px] text-ink-muted">{unread ? `${unread} unread` : 'All caught up'}</p>
              </div>
              <button onClick={onClose} className="rounded-lg p-1.5 text-ink-muted hover:bg-secondary">
                <X className="h-4 w-4" />
              </button>
            </div>

            {digest && (
              <div className="border-b border-line bg-brand-soft/30 px-5 py-4">
                <p className="text-[11px] font-medium uppercase tracking-wider text-brand">This week</p>
                <p className="mt-1 text-[13px] leading-relaxed text-ink">{digest.message}</p>
                <p className="mt-2 text-[12px] text-ink-muted">Focus: {digest.suggestedFocus}</p>
              </div>
            )}

            <div className="flex-1 overflow-y-auto px-4 py-3">
              {isLoading ? (
                <p className="p-4 text-center text-[13px] text-ink-muted">Loading…</p>
              ) : notifications.length === 0 ? (
                <div className="flex flex-col items-center justify-center px-4 py-16 text-center">
                  <Bell className="h-8 w-8 text-ink-subtle" />
                  <p className="mt-3 text-[14px] font-medium text-ink">Nothing right now</p>
                  <p className="mt-1 text-[12.5px] text-ink-muted">Schedule a draft in Planner and we will nudge you gently.</p>
                </div>
              ) : (
                <div className="space-y-2">
                  {notifications.map((n) => {
                    const Icon = TYPE_ICONS[n.type] || Bell;
                    return (
                      <div
                        key={n.id}
                        className={`rounded-2xl border p-4 transition-colors ${
                          n.read ? 'border-line/60 bg-card/60' : 'border-line bg-card shadow-soft'
                        }`}
                      >
                        <div className="flex gap-3">
                          <div className="mt-0.5 flex h-8 w-8 shrink-0 items-center justify-center rounded-lg bg-secondary">
                            <Icon className="h-4 w-4 text-brand" />
                          </div>
                          <div className="min-w-0 flex-1">
                            <p className="text-[13.5px] font-medium text-ink">{n.title}</p>
                            <p className="mt-1 text-[12.5px] leading-relaxed text-ink-muted">{n.body}</p>
                            <div className="mt-3 flex flex-wrap gap-2">
                              {n.actionHref && (
                                <Button
                                  size="sm"
                                  onClick={() => actionMutation.mutate({ id: n.id, action: 'go', href: n.actionHref })}
                                  className="h-7 rounded-lg bg-ink text-[11px] text-white hover:bg-ink/90"
                                >
                                  {n.actionLabel || 'Open'}
                                </Button>
                              )}
                              {n.draftId && (
                                <Button
                                  size="sm"
                                  variant="outline"
                                  onClick={() => actionMutation.mutate({ id: n.id, action: 'complete', href: null })}
                                  className="h-7 rounded-lg border-line text-[11px]"
                                >
                                  <Check className="mr-1 h-3 w-3" /> Mark complete
                                </Button>
                              )}
                              <Button
                                size="sm"
                                variant="ghost"
                                onClick={() => actionMutation.mutate({ id: n.id, action: 'dismiss', href: null })}
                                className="h-7 rounded-lg text-[11px] text-ink-muted"
                              >
                                Dismiss
                              </Button>
                            </div>
                          </div>
                        </div>
                      </div>
                    );
                  })}
                </div>
              )}
            </div>

            <div className="border-t border-line px-5 py-3">
              <Button asChild variant="outline" className="w-full rounded-xl border-line text-[12.5px]">
                <Link href="/planner" onClick={onClose}>
                  <CalendarRange className="mr-2 h-3.5 w-3.5" /> Open Planner
                </Link>
              </Button>
            </div>
          </motion.aside>
        </>
      )}
    </AnimatePresence>
  );
}

export function NotificationBell() {
  const [open, setOpen] = useState(false);
  const { data } = useQuery({
    queryKey: ['notifications'],
    queryFn: () => notificationService.list(),
    refetchInterval: 120000,
  });
  const unread = data?.unreadCount || 0;

  return (
    <>
      <button
        onClick={() => setOpen(true)}
        className="relative rounded-lg p-2 text-ink-muted hover:bg-secondary hover:text-ink focus-ring"
        aria-label="Notifications"
      >
        <Bell className="h-[18px] w-[18px]" />
        {unread > 0 && (
          <span className="absolute right-1 top-1 flex h-4 min-w-4 items-center justify-center rounded-full bg-brand px-1 text-[9px] font-medium text-white">
            {unread > 9 ? '9+' : unread}
          </span>
        )}
      </button>
      <NotificationPanel open={open} onClose={() => setOpen(false)} />
    </>
  );
}
