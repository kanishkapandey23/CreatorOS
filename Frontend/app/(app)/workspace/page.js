'use client';

import Link from 'next/link';
import { useQuery } from '@tanstack/react-query';
import { motion } from 'framer-motion';
import { ArrowRight, Sparkles, Plus, BookOpen, CalendarRange, PenLine } from 'lucide-react';
import { workspaceService } from '@/services/workspace.service';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { useAuth } from '@/providers/auth-provider';

const easing = { duration: 0.35, ease: [0.22, 1, 0.36, 1] };

export default function WorkspacePage() {
  const { user } = useAuth();
  const { data, isLoading } = useQuery({ queryKey: ['workspace'], queryFn: () => workspaceService.getHome() });

  const first = user?.name?.split(' ')[0] || 'there';

  return (
    <div className="mx-auto w-full max-w-6xl px-5 py-10 md:px-8 md:py-14">
      <motion.header initial={{ opacity: 0, y: 6 }} animate={{ opacity: 1, y: 0 }} transition={easing}>
        <p className="text-[12px] font-medium uppercase tracking-[0.18em] text-ink-subtle">{new Date().toLocaleDateString(undefined, { weekday: 'long', month: 'long', day: 'numeric' })}</p>
        <h1 className="mt-2 font-display text-[34px] font-semibold tracking-tight text-ink md:text-[40px]">
          Good to see you, {first}.
        </h1>
        <p className="mt-2 max-w-xl text-[14.5px] text-ink-muted">A few small stories are already taking shape. Pick up where you left off — or start something new.</p>
      </motion.header>

      {/* Continue Reflection */}
      <motion.section
        initial={{ opacity: 0, y: 10 }} animate={{ opacity: 1, y: 0 }} transition={{ ...easing, delay: 0.05 }}
        className="mt-8"
      >
        <div className="card-elev relative overflow-hidden p-7 md:p-8">
          <div className="pointer-events-none absolute -right-16 -top-16 h-48 w-48 rounded-full bg-brand-soft blur-3xl" />
          <div className="relative flex flex-col items-start justify-between gap-5 md:flex-row md:items-center">
            <div className="max-w-2xl">
              <div className="inline-flex items-center gap-2 rounded-full bg-secondary px-2.5 py-1 text-[11px] font-medium text-ink-muted">
                <Sparkles className="h-3 w-3 text-brand" /> Continue reflection
              </div>
              <h2 className="mt-3 font-display text-[22px] font-semibold leading-snug text-ink md:text-[26px]">
                What did you change your mind about this week?
              </h2>
              <div className="mt-4 flex items-center gap-3 text-[12.5px] text-ink-muted">
                <div className="h-1.5 w-40 overflow-hidden rounded-full bg-secondary">
                  <div className="h-full w-1/2 rounded-full bg-brand" />
                </div>
                {data?.continueReflection?.progress || 3} of {data?.continueReflection?.total || 6} prompts
              </div>
            </div>
            <Button asChild className="h-11 rounded-xl bg-ink px-5 text-[13.5px] text-white hover:bg-ink/90">
              <Link href="/reflection">Continue<ArrowRight className="ml-2 h-4 w-4" /></Link>
            </Button>
          </div>
        </div>
      </motion.section>

      <div className="mt-10 grid gap-6 md:grid-cols-3">
        {/* Recent Stories */}
        <section className="md:col-span-2">
          <div className="mb-4 flex items-center justify-between">
            <h3 className="font-display text-[18px] font-semibold text-ink">Recent stories</h3>
            <Link href="/stories" className="text-[12.5px] text-ink-muted hover:text-ink">Open Story Bank →</Link>
          </div>
          <div className="grid gap-3 sm:grid-cols-2">
            {(data?.recentStories || []).map((s) => (
              <Link key={s.id} href={`/stories/${s.id}`} className="card-elev group p-5 transition-shadow hover:shadow-pop">
                <div className="flex items-center justify-between text-[11px] uppercase tracking-wider text-ink-subtle">
                  <span>{s.emotion}</span>
                  <span>{s.potential}% potential</span>
                </div>
                <p className="mt-2 font-display text-[16px] font-semibold leading-snug text-ink group-hover:text-ink">{s.title}</p>
                <p className="mt-1.5 line-clamp-2 text-[13px] text-ink-muted">{s.summary}</p>
                <div className="mt-4 flex items-center gap-2">
                  <Badge variant="outline" className="rounded-full border-line bg-canvas text-[11px] font-normal text-ink-muted">{s.category}</Badge>
                  <Badge variant="outline" className="rounded-full border-line bg-canvas text-[11px] font-normal capitalize text-ink-muted">{s.status}</Badge>
                </div>
              </Link>
            ))}
          </div>
        </section>

        {/* Weekly plan & balance */}
        <section className="space-y-6">
          <div className="card-elev p-5">
            <div className="flex items-center justify-between">
              <h3 className="font-display text-[15.5px] font-semibold text-ink">Weekly plan</h3>
              <Link href="/planner" className="text-[12px] text-ink-muted hover:text-ink">Open →</Link>
            </div>
            <ul className="mt-3 space-y-2.5">
              {(data?.weeklyPlan || []).map((p, i) => (
                <li key={i} className="flex items-center gap-3">
                  <div className="flex h-8 w-9 shrink-0 flex-col items-center justify-center rounded-lg border border-line text-[10.5px] font-medium text-ink-muted">
                    <span>{p.day}</span>
                  </div>
                  <div className="min-w-0 flex-1">
                    <p className="truncate text-[13px] font-medium text-ink">{p.title}</p>
                    <p className="text-[11.5px] capitalize text-ink-subtle">{p.status}</p>
                  </div>
                </li>
              ))}
            </ul>
          </div>
          <div className="card-elev p-5">
            <h3 className="font-display text-[15.5px] font-semibold text-ink">Content balance</h3>
            <p className="mt-1 text-[12px] text-ink-muted">A gentle look at how your stories balance.</p>
            <div className="mt-4 space-y-3">
              {[
                { l: 'Story', v: data?.balance?.story || 60, c: 'bg-brand' },
                { l: 'Lesson', v: data?.balance?.lesson || 25, c: 'bg-violet' },
                { l: 'Opinion', v: data?.balance?.opinion || 15, c: 'bg-ink' },
              ].map((b) => (
                <div key={b.l}>
                  <div className="mb-1 flex items-center justify-between text-[11.5px] text-ink-muted">
                    <span>{b.l}</span><span>{b.v}%</span>
                  </div>
                  <div className="h-1.5 w-full overflow-hidden rounded-full bg-secondary">
                    <div className={`h-full ${b.c}`} style={{ width: `${b.v}%` }} />
                  </div>
                </div>
              ))}
            </div>
          </div>
        </section>
      </div>

      {/* Quick actions */}
      <section className="mt-10">
        <h3 className="font-display text-[18px] font-semibold text-ink">Quick actions</h3>
        <div className="mt-3 grid gap-3 sm:grid-cols-2 lg:grid-cols-4">
          {[
            { t: 'Start a reflection', d: 'A 5-minute guided ritual.', icon: Sparkles, href: '/reflection' },
            { t: 'Add a story idea', d: 'Capture a moment quickly.', icon: Plus, href: '/stories' },
            { t: 'Open Story Bank', d: 'Your library of moments.', icon: BookOpen, href: '/stories' },
            { t: 'Plan the week', d: 'Set a calm rhythm.', icon: CalendarRange, href: '/planner' },
          ].map((a) => (
            <Link key={a.t} href={a.href} className="card-elev flex items-start gap-3 p-4 transition-colors hover:bg-secondary/40">
              <div className="inline-flex h-9 w-9 items-center justify-center rounded-xl bg-secondary text-ink">
                <a.icon className="h-[18px] w-[18px]" />
              </div>
              <div>
                <p className="text-[13.5px] font-semibold text-ink">{a.t}</p>
                <p className="text-[12px] text-ink-muted">{a.d}</p>
              </div>
            </Link>
          ))}
        </div>
      </section>

      {isLoading && <p className="mt-10 text-[12px] text-ink-subtle">Loading your workspace…</p>}
    </div>
  );
}