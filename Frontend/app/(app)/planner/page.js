'use client';

import { useQuery } from '@tanstack/react-query';
import { motion } from 'framer-motion';
import { Plus, CalendarRange } from 'lucide-react';
import { plannerService } from '@/services/planner.service';
import { Badge } from '@/components/ui/badge';
import { EmptyState } from '@/components/layout/empty-state';

const typeColor = {
  LinkedIn: 'bg-brand-soft text-brand',
  Twitter: 'bg-secondary text-ink',
  Newsletter: 'bg-violet-soft text-violet',
  Reflection: 'bg-success-soft text-success',
};

export default function PlannerPage() {
  const { data: week = [] } = useQuery({ queryKey: ['planner'], queryFn: () => plannerService.getWeek() });

  return (
    <div className="mx-auto w-full max-w-[1200px] px-5 py-10 md:px-8 md:py-12">
      <div className="flex flex-wrap items-end justify-between gap-4">
        <div>
          <p className="text-[12px] font-medium uppercase tracking-[0.18em] text-ink-subtle">Rhythm</p>
          <h1 className="mt-1.5 font-display text-[30px] font-semibold tracking-tight text-ink md:text-[36px]">Planner</h1>
          <p className="mt-1.5 max-w-xl text-[13.5px] text-ink-muted">A gentle weekly view. Plan the stories you'd like to share, when it feels right.</p>
        </div>
        <div className="rounded-xl border border-line bg-card px-3 py-2 text-[12.5px] text-ink-muted">
          Scheduling integrations coming soon.
        </div>
      </div>

      <motion.div initial={{ opacity: 0, y: 8 }} animate={{ opacity: 1, y: 0 }} transition={{ duration: 0.3 }} className="mt-8 grid gap-3 md:grid-cols-7">
        {week.map((d, i) => (
          <div key={d.day} className="card-elev flex min-h-[260px] flex-col p-4">
            <div className="flex items-center justify-between">
              <p className="font-display text-[14px] font-semibold text-ink">{d.day}</p>
              <span className="text-[11px] text-ink-subtle">{d.date}</span>
            </div>
            <div className="mt-3 flex flex-1 flex-col gap-2">
              {d.items.length === 0 ? (
                <button className="flex flex-1 flex-col items-center justify-center rounded-xl border border-dashed border-line text-[11.5px] text-ink-subtle hover:border-ink-subtle hover:text-ink-muted">
                  <Plus className="h-4 w-4" />
                  <span className="mt-1">Add</span>
                </button>
              ) : (
                d.items.map((it) => (
                  <div key={it.id} className="rounded-xl border border-line bg-canvas p-3">
                    <Badge className={`mb-2 rounded-full px-2 py-0.5 text-[10.5px] font-medium ${typeColor[it.type] || 'bg-secondary text-ink'}`}>{it.type}</Badge>
                    <p className="text-[13px] font-medium leading-snug text-ink">{it.title}</p>
                    <p className="mt-1 text-[11px] capitalize text-ink-subtle">{it.status}</p>
                  </div>
                ))
              )}
            </div>
          </div>
        ))}
      </motion.div>

      <div className="mt-10">
        <EmptyState icon={CalendarRange} title="Publishing queue coming soon." description="Once integrations land, your scheduled content will appear here in a calm queue — never as a to-do list." />
      </div>
    </div>
  );
}
