'use client';

import { useState } from 'react';
import { useQuery, useQueryClient } from '@tanstack/react-query';
import Link from 'next/link';
import { motion } from 'framer-motion';
import { CalendarRange, Bell, Clock } from 'lucide-react';
import { plannerService } from '@/services/planner.service';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { ChipSelect } from '@/components/ui/chip-select';
import { toast } from 'sonner';

const typeColor = {
  LinkedIn: 'bg-brand-soft text-brand',
  Reel: 'bg-secondary text-ink',
  Carousel: 'bg-violet-soft text-violet',
  Thread: 'bg-success-soft text-success',
};

const REMINDER_OPTIONS = [
  { id: '1d', label: '1 day before' },
  { id: '6h', label: '6 hours before' },
  { id: '1h', label: '1 hour before' },
  { id: '15m', label: '15 min before' },
  { id: 'until_complete', label: 'Until completed' },
];

export default function PlannerPage() {
  const queryClient = useQueryClient();
  const [scheduling, setScheduling] = useState(null);
  const [reminderDraft, setReminderDraft] = useState(null);
  const [offsets, setOffsets] = useState(['1d', '1h']);
  const [emailOn, setEmailOn] = useState(true);

  const { data, isLoading } = useQuery({
    queryKey: ['planner'],
    queryFn: () => plannerService.getWeek(),
  });

  const week = data?.week || [];
  const unscheduled = data?.unscheduled || [];

  const handleSchedule = async (draftId, dayIso, dayLabel) => {
    setScheduling(draftId);
    try {
      await plannerService.scheduleDraft(draftId, {
        dayIso,
        reminderEnabled: true,
        reminderOffsets: offsets,
        reminderChannels: emailOn ? ['in_app', 'email'] : ['in_app'],
      });
      toast.success(`Scheduled for ${dayLabel} · reminders on`);
      queryClient.invalidateQueries({ queryKey: ['planner'] });
      queryClient.invalidateQueries({ queryKey: ['notifications'] });
    } catch {
      toast.error('Could not schedule');
    } finally {
      setScheduling(null);
    }
  };

  const handleUpdateReminders = async (draftId) => {
    try {
      await plannerService.updateReminders(draftId, {
        reminderEnabled: true,
        reminderOffsets: offsets,
        reminderChannels: emailOn ? ['in_app', 'email'] : ['in_app'],
      });
      toast.success('Reminders updated');
      setReminderDraft(null);
      queryClient.invalidateQueries({ queryKey: ['planner'] });
    } catch {
      toast.error('Could not update reminders');
    }
  };

  return (
    <div className="mx-auto w-full max-w-[1200px] px-5 py-10 md:px-8 md:py-12">
      <div>
        <p className="text-[12px] font-medium uppercase tracking-[0.18em] text-ink-subtle">Planner</p>
        <h1 className="mt-1.5 font-display text-[30px] font-semibold tracking-tight text-ink md:text-[36px]">This week</h1>
        <p className="mt-1.5 max-w-xl text-[13.5px] text-ink-muted">
          Schedule drafts and set gentle reminders — in-app and email (when SMTP is configured).
        </p>
      </div>

      {reminderDraft && (
        <div className="mt-6 card-elev p-5">
          <p className="text-[14px] font-medium text-ink">Reminder settings</p>
          <ChipSelect className="mt-3" options={REMINDER_OPTIONS} value={offsets[0]} onChange={(v) => setOffsets([v])} />
          <label className="mt-4 flex items-center gap-2 text-[13px] text-ink-muted">
            <input type="checkbox" checked={emailOn} onChange={(e) => setEmailOn(e.target.checked)} />
            Email reminders too
          </label>
          <p className="mt-2 text-[11.5px] text-ink-subtle">WhatsApp, Discord, Slack — coming soon</p>
          <div className="mt-4 flex gap-2">
            <Button onClick={() => handleUpdateReminders(reminderDraft)} className="rounded-xl bg-ink text-white">Save</Button>
            <Button variant="outline" onClick={() => setReminderDraft(null)} className="rounded-xl border-line">Cancel</Button>
          </div>
        </div>
      )}

      {isLoading ? (
        <p className="mt-8 text-[13px] text-ink-muted">Loading your week…</p>
      ) : (
        <>
          <motion.div initial={{ opacity: 0, y: 8 }} animate={{ opacity: 1, y: 0 }} className="mt-8 grid gap-3 md:grid-cols-7">
            {week.map((d) => (
              <div key={d.iso} className="card-elev flex min-h-[200px] flex-col p-4">
                <div className="flex items-center justify-between">
                  <p className="font-display text-[14px] font-semibold text-ink">{d.day}</p>
                  <span className="text-[11px] text-ink-subtle">{d.date}</span>
                </div>
                <div className="mt-3 flex flex-1 flex-col gap-2">
                  {d.items.length === 0 ? (
                    <p className="flex flex-1 items-center justify-center text-[11px] text-ink-subtle">Open</p>
                  ) : (
                    d.items.map((it) => (
                      <Link
                        key={it.id}
                        href={`/stories/${it.storyId}/studio/${it.id}`}
                        className="rounded-xl border border-line bg-canvas p-3 hover:shadow-soft"
                      >
                        <Badge className={`mb-1.5 rounded-full px-2 py-0.5 text-[10px] ${typeColor[it.type] || 'bg-secondary text-ink'}`}>
                          {it.type}
                        </Badge>
                        <p className="line-clamp-2 text-[12px] font-medium text-ink">{it.title}</p>
                        {it.reminderActive && (
                          <p className="mt-1.5 flex items-center gap-1 text-[10px] text-brand">
                            <Bell className="h-3 w-3" /> Reminder active
                          </p>
                        )}
                      </Link>
                    ))
                  )}
                </div>
              </div>
            ))}
          </motion.div>

          <section className="mt-10">
            <h2 className="font-display text-[18px] font-semibold text-ink">Ready to schedule</h2>
            {unscheduled.length === 0 ? (
              <div className="mt-4 rounded-2xl border border-dashed border-line bg-canvas/40 px-5 py-8 text-center">
                <CalendarRange className="mx-auto h-6 w-6 text-ink-subtle" />
                <p className="mt-2 text-[13px] text-ink-muted">No drafts yet. Strategist can recommend what to create.</p>
                <Button asChild className="mt-4 rounded-xl bg-ink text-white">
                  <Link href="/strategy">Open Strategist</Link>
                </Button>
              </div>
            ) : (
              <div className="mt-4 space-y-2">
                {unscheduled.map((it) => (
                  <div key={it.id} className="card-elev p-4">
                    <div className="flex flex-wrap items-start justify-between gap-3">
                      <div>
                        <Badge className={`rounded-full px-2 py-0.5 text-[10px] ${typeColor[it.type] || 'bg-secondary text-ink'}`}>{it.type}</Badge>
                        <p className="mt-1 font-medium text-ink">{it.title}</p>
                        {it.reminderActive && (
                          <p className="mt-1 flex items-center gap-1 text-[11px] text-brand">
                            <Clock className="h-3 w-3" /> Reminders on
                          </p>
                        )}
                      </div>
                      <Button size="sm" variant="ghost" onClick={() => { setReminderDraft(it.id); setOffsets(it.reminderOffsets || ['1d', '1h']); }} className="text-[11px] text-ink-muted">
                        Reminders
                      </Button>
                    </div>
                    <div className="mt-3 flex flex-wrap gap-2">
                      {week.map((d) => (
                        <Button
                          key={d.iso}
                          size="sm"
                          variant="outline"
                          disabled={scheduling === it.id}
                          onClick={() => handleSchedule(it.id, d.iso, d.day)}
                          className="h-8 rounded-lg border-line text-[11px]"
                        >
                          {d.day}
                        </Button>
                      ))}
                    </div>
                  </div>
                ))}
              </div>
            )}
          </section>
        </>
      )}
    </div>
  );
}
