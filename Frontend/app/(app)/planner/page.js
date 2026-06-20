'use client';

import { useState } from 'react';
import { useQuery, useQueryClient } from '@tanstack/react-query';
import Link from 'next/link';
import { motion, AnimatePresence } from 'framer-motion';
import { CalendarRange, Bell, Clock, Trash2, Edit, ExternalLink, Check, Plus, X } from 'lucide-react';
import { plannerService } from '@/services/planner.service';
import { draftService } from '@/services/draft.service';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { toast } from 'sonner';

const typeColor = {
  LinkedIn: 'bg-brand-soft text-brand border-brand/20',
  Reel: 'bg-secondary text-ink border-line',
  Carousel: 'bg-violet-soft text-violet border-violet/20',
  Thread: 'bg-success-soft text-success border-success/20',
};

export default function PlannerPage() {
  const queryClient = useQueryClient();
  const [scheduling, setScheduling] = useState(null);
  const [showScheduleModal, setShowScheduleModal] = useState(false);
  const [selectedDraft, setSelectedDraft] = useState(null);
  const [scheduleDate, setScheduleDate] = useState('');
  const [scheduleTime, setScheduleTime] = useState('19:30');

  // Inline reschedule states
  const [reschedulingId, setReschedulingId] = useState(null);
  const [newDate, setNewDate] = useState('');
  const [newTime, setNewTime] = useState('19:30');

  const { data, isLoading } = useQuery({
    queryKey: ['planner'],
    queryFn: () => plannerService.getWeek(),
  });

  const week = data?.week || [];
  const unscheduled = data?.unscheduled || [];

  // Determine if there are any scheduled items in the week
  const scheduledItems = week.reduce((acc, day) => [...acc, ...day.items], []);
  const hasScheduled = scheduledItems.length > 0;

  const handleSchedule = async () => {
    if (!selectedDraft || !scheduleDate || !scheduleTime) {
      toast.error('Please choose a draft, date and time');
      return;
    }
    setScheduling(selectedDraft.id);
    try {
      const isoStr = new Date(`${scheduleDate}T${scheduleTime}`).toISOString();
      await plannerService.scheduleDraft(selectedDraft.id, {
        scheduledAt: isoStr,
        reminderEnabled: true,
      });
      toast.success('Draft scheduled successfully');
      setShowScheduleModal(false);
      setSelectedDraft(null);
      queryClient.invalidateQueries({ queryKey: ['planner'] });
    } catch {
      toast.error('Could not schedule draft');
    } finally {
      setScheduling(null);
    }
  };

  const handleReschedule = async (draftId) => {
    if (!newDate || !newTime) {
      toast.error('Choose a valid date and time');
      return;
    }
    try {
      const isoStr = new Date(`${newDate}T${newTime}`).toISOString();
      await plannerService.scheduleDraft(draftId, {
        scheduledAt: isoStr,
        reminderEnabled: true,
      });
      toast.success('Rescheduled successfully');
      setReschedulingId(null);
      queryClient.invalidateQueries({ queryKey: ['planner'] });
    } catch {
      toast.error('Failed to reschedule');
    }
  };

  const handleRemoveSchedule = async (draftId) => {
    if (confirm('Remove this draft from the schedule?')) {
      try {
        await plannerService.scheduleDraft(draftId, { scheduledAt: null });
        toast.success('Removed from schedule');
        queryClient.invalidateQueries({ queryKey: ['planner'] });
      } catch {
        toast.error('Failed to remove from schedule');
      }
    }
  };

  const handleMarkPublished = async (draftId) => {
    try {
      await draftService.update(draftId, { status: 'published' });
      toast.success('Marked as published');
      queryClient.invalidateQueries({ queryKey: ['planner'] });
    } catch {
      toast.error('Failed to update status');
    }
  };

  const formatDate = (isoStr) => {
    return new Date(isoStr).toLocaleDateString(undefined, { weekday: 'long', month: 'short', day: 'numeric' });
  };

  const formatTime = (isoStr) => {
    return new Date(isoStr).toLocaleTimeString(undefined, { hour: '2-digit', minute: '2-digit' });
  };

  return (
    <div className="mx-auto w-full max-w-[1200px] px-5 py-10 md:px-8 md:py-12">
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
        <div>
          <p className="text-[12px] font-medium uppercase tracking-[0.18em] text-ink-subtle">Planner</p>
          <h1 className="mt-1.5 font-display text-[30px] font-semibold tracking-tight text-ink md:text-[36px]">Publishing Schedule</h1>
          <p className="mt-1.5 max-w-xl text-[13.5px] text-ink-muted">
            Map out your week, set publishing reminders, and oversee execution.
          </p>
        </div>
        <Button
          onClick={() => {
            const today = new Date();
            const yr = today.getFullYear();
            const mo = String(today.getMonth() + 1).padStart(2, '0');
            const dy = String(today.getDate()).padStart(2, '0');
            setScheduleDate(`${yr}-${mo}-${dy}`);
            setShowScheduleModal(true);
          }}
          className="h-10.5 rounded-xl bg-ink text-white hover:bg-ink/90 inline-flex items-center gap-1.5 self-start sm:self-center"
        >
          <Plus className="h-4 w-4" /> Schedule a Draft
        </Button>
      </div>

      {isLoading ? (
        <p className="mt-10 text-[13px] text-ink-muted">Loading schedule…</p>
      ) : !hasScheduled ? (
        /* --- EMPTY STATE --- */
        <div className="mt-12 rounded-2xl border border-dashed border-line bg-card px-5 py-12 text-center max-w-xl mx-auto">
          <CalendarRange className="mx-auto h-8 w-8 text-brand" />
          <h3 className="mt-4 font-display text-[17px] font-semibold text-ink">No drafts scheduled yet</h3>
          <p className="mt-2 text-[13.5px] text-ink-muted">
            Set up a calm publishing rhythm by adding draft entries to specific days and times this week.
          </p>
          <Button
            onClick={() => setShowScheduleModal(true)}
            className="mt-6 rounded-xl bg-ink text-white hover:bg-ink/90 inline-flex items-center gap-1.5"
          >
            <Plus className="h-4 w-4" /> Schedule a Draft
          </Button>
        </div>
      ) : (
        <>
          {/* Weekly Calendar Grid Overview */}
          <div className="mt-10">
            <h2 className="font-display text-[15px] font-semibold text-ink uppercase tracking-wider text-ink-subtle mb-4">Calendar Grid</h2>
            <motion.div initial={{ opacity: 0, y: 8 }} animate={{ opacity: 1, y: 0 }} className="grid gap-3 md:grid-cols-7">
              {week.map((d) => (
                <div key={d.iso} className="card-elev flex min-h-[140px] flex-col p-4 bg-card/50">
                  <div className="flex items-center justify-between border-b border-line/40 pb-2">
                    <p className="font-display text-[13px] font-semibold text-ink">{d.day}</p>
                    <span className="text-[10.5px] text-ink-subtle">{d.date}</span>
                  </div>
                  <div className="mt-3 flex flex-1 flex-col gap-1.5">
                    {d.items.length === 0 ? (
                      <p className="flex flex-1 items-center justify-center text-[10.5px] text-ink-subtle/40 italic">Open</p>
                    ) : (
                      d.items.map((it) => (
                        <div
                          key={it.id}
                          className="rounded-lg border border-line bg-canvas px-2.5 py-1.5 text-[11px] font-medium text-ink shadow-soft flex items-center justify-between"
                        >
                          <span className="truncate">{it.type} ({it.storyTitle})</span>
                          <span className="text-[9.5px] text-brand shrink-0 pl-1">{it.scheduledAt ? formatTime(it.scheduledAt) : ''}</span>
                        </div>
                      ))
                    )}
                  </div>
                </div>
              ))}
            </motion.div>
          </div>

          {/* Detailed Scheduled Cards List */}
          <div className="mt-12">
            <h2 className="font-display text-[15px] font-semibold text-ink uppercase tracking-wider text-ink-subtle mb-4">Scheduled Posts Queue</h2>
            <div className="space-y-4">
              {scheduledItems.map((it) => {
                const isInlineRescheduling = reschedulingId === it.id;
                return (
                  <div key={it.id} className="card-elev p-5 bg-card border border-line flex flex-col md:flex-row md:items-start justify-between gap-5">
                    <div className="space-y-2.5 max-w-2xl">
                      <div className="flex flex-wrap items-center gap-2">
                        <Badge className={`rounded-full border px-2 py-0.5 text-[10.5px] font-normal tracking-wide capitalize ${typeColor[it.type] || 'bg-secondary text-ink'}`}>
                          {it.type} Draft
                        </Badge>
                        <Badge variant="outline" className="rounded-full border-line bg-canvas text-[10.5px] font-normal text-ink-subtle uppercase tracking-wider">
                          {it.status === 'draft' ? 'Draft Ready' : it.status}
                        </Badge>
                        <span className="text-[11.5px] text-ink-subtle flex items-center gap-1">
                          <Clock className="h-3.5 w-3.5" /> {formatDate(it.scheduledAt)} at {formatTime(it.scheduledAt)}
                        </span>
                      </div>

                      <h3 className="font-display text-[17px] font-semibold text-ink">{it.storyTitle}</h3>
                      {it.snippet && (
                        <p className="text-[13px] text-ink-muted leading-relaxed italic border-l-2 border-line pl-3 font-serif">
                          "{it.snippet}"
                        </p>
                      )}

                      {it.reminderActive && (
                        <p className="flex items-center gap-1.5 text-[11px] text-brand">
                          <Bell className="h-3.5 w-3.5" /> Reminders configured
                        </p>
                      )}

                      {/* Reschedule inline drawer */}
                      {isInlineRescheduling && (
                        <div className="mt-4 p-4 rounded-xl border border-line bg-canvas max-w-md">
                          <p className="text-[12.5px] font-semibold text-ink">Choose Date & Time</p>
                          <div className="mt-3 grid gap-3 sm:grid-cols-2">
                            <input
                              type="date"
                              value={newDate}
                              onChange={(e) => setNewDate(e.target.value)}
                              className="rounded-lg border border-line bg-card px-2.5 py-1.5 text-[12.5px] text-ink"
                            />
                            <input
                              type="time"
                              value={newTime}
                              onChange={(e) => setNewTime(e.target.value)}
                              className="rounded-lg border border-line bg-card px-2.5 py-1.5 text-[12.5px] text-ink"
                            />
                          </div>
                          <div className="mt-4 flex gap-2 justify-end">
                            <Button onClick={() => setReschedulingId(null)} variant="ghost" className="h-8 rounded-lg text-[11px]">
                              Cancel
                            </Button>
                            <Button onClick={() => handleReschedule(it.id)} className="h-8 rounded-lg bg-ink text-white text-[11px] px-3.5">
                              Apply
                            </Button>
                          </div>
                        </div>
                      )}
                    </div>

                    {/* Actions Panel */}
                    <div className="flex flex-wrap items-center gap-2 self-end md:self-start">
                      <Button asChild variant="outline" size="sm" className="h-8.5 rounded-lg border-line text-[12px]">
                        <Link href={`/stories/${it.storyId}/studio/${it.id}`}>
                          <ExternalLink className="h-3.5 w-3.5 mr-1" /> Open Preview
                        </Link>
                      </Button>
                      <Button asChild variant="outline" size="sm" className="h-8.5 rounded-lg border-line text-[12px]">
                        <Link href={`/stories/${it.storyId}/studio/${it.id}?edit=true`}>
                          <Edit className="h-3.5 w-3.5 mr-1" /> Edit
                        </Link>
                      </Button>
                      <Button
                        onClick={() => {
                          const dt = new Date(it.scheduledAt);
                          const yr = dt.getFullYear();
                          const mo = String(dt.getMonth() + 1).padStart(2, '0');
                          const dy = String(dt.getDate()).padStart(2, '0');
                          setNewDate(`${yr}-${mo}-${dy}`);
                          const hr = String(dt.getHours()).padStart(2, '0');
                          const mn = String(dt.getMinutes()).padStart(2, '0');
                          setNewTime(`${hr}:${mn}`);
                          setReschedulingId(it.id);
                        }}
                        variant="outline"
                        size="sm"
                        className="h-8.5 rounded-lg border-line text-[12px]"
                      >
                        Reschedule
                      </Button>
                      {it.status !== 'published' && (
                        <Button
                          onClick={() => handleMarkPublished(it.id)}
                          variant="outline"
                          size="sm"
                          className="h-8.5 rounded-lg border-line text-[12px]"
                        >
                          Mark Published
                        </Button>
                      )}
                      <Button
                        onClick={() => handleRemoveSchedule(it.id)}
                        variant="ghost"
                        size="sm"
                        className="h-8.5 rounded-lg text-[12px] text-danger hover:bg-danger/10 px-3"
                      >
                        Remove
                      </Button>
                    </div>
                  </div>
                );
              })}
            </div>
          </div>
        </>
      )}

      {/* --- SELECT DRAFT TO SCHEDULE MODAL --- */}
      {showScheduleModal && (
        <div className="fixed inset-0 z-50 bg-ink/30 backdrop-blur-sm flex items-center justify-center p-5">
          <motion.div
            initial={{ scale: 0.95, opacity: 0 }}
            animate={{ scale: 1, opacity: 1 }}
            className="w-full max-w-xl bg-card border border-line rounded-2xl p-6 shadow-pop max-h-[85vh] overflow-y-auto"
          >
            <div className="flex items-center justify-between border-b border-line/45 pb-3">
              <h2 className="font-display text-[18px] font-semibold text-ink">Schedule a Draft</h2>
              <button
                onClick={() => {
                  setShowScheduleModal(false);
                  setSelectedDraft(null);
                }}
                className="p-1 rounded-lg hover:bg-secondary text-ink-subtle hover:text-ink"
              >
                <X className="h-5 w-5" />
              </button>
            </div>

            <div className="mt-4">
              {!selectedDraft ? (
                <>
                  <p className="text-[13px] text-ink-muted mb-3">Choose from available unscheduled drafts:</p>
                  <div className="space-y-2 max-h-[40vh] overflow-y-auto">
                    {unscheduled.length === 0 ? (
                      <div className="text-center py-8 text-[13px] text-ink-subtle">
                        No unscheduled drafts. Head to Story Bank to create a draft.
                      </div>
                    ) : (
                      unscheduled.map((d) => (
                        <div
                          key={d.id}
                          onClick={() => setSelectedDraft(d)}
                          className="card-elev border border-line/60 p-4 bg-canvas/45 hover:bg-canvas transition-colors cursor-pointer text-left"
                        >
                          <div className="flex items-center justify-between">
                            <Badge className="rounded-full px-2 py-0.5 text-[9.5px] font-normal tracking-wide capitalize bg-secondary text-ink-muted">
                              {d.type}
                            </Badge>
                            <span className="text-[10px] text-ink-subtle">Select Draft</span>
                          </div>
                          <h4 className="font-display text-[14.5px] font-semibold text-ink mt-1.5">{d.storyTitle || d.title}</h4>
                          {d.snippet && (
                            <p className="text-[12px] text-ink-muted truncate mt-1">"{d.snippet}"</p>
                          )}
                        </div>
                      ))
                    )}
                  </div>
                </>
              ) : (
                <div className="space-y-4">
                  <div className="p-4 rounded-xl bg-secondary/35 border border-line">
                    <p className="text-[11px] font-semibold uppercase tracking-wider text-ink-subtle">Selected Draft</p>
                    <h3 className="font-display text-[15.5px] font-semibold text-ink mt-1">{selectedDraft.storyTitle}</h3>
                    <Badge className="mt-1.5 rounded-full px-2 py-0.5 text-[9.5px] font-normal tracking-wide bg-secondary text-ink-muted">
                      {selectedDraft.type}
                    </Badge>
                  </div>

                  <div className="grid gap-3 sm:grid-cols-2">
                    <div>
                      <label className="text-[11.5px] font-semibold text-ink-muted">Scheduled Date</label>
                      <input
                        type="date"
                        value={scheduleDate}
                        onChange={(e) => setScheduleDate(e.target.value)}
                        className="mt-1 w-full rounded-xl border border-line bg-canvas px-3.5 py-2 text-[13px] text-ink focus:outline-none"
                      />
                    </div>
                    <div>
                      <label className="text-[11.5px] font-semibold text-ink-muted">Scheduled Time</label>
                      <input
                        type="time"
                        value={scheduleTime}
                        onChange={(e) => setScheduleTime(e.target.value)}
                        className="mt-1 w-full rounded-xl border border-line bg-canvas px-3.5 py-2 text-[13px] text-ink focus:outline-none"
                      />
                    </div>
                  </div>

                  <div className="pt-4 flex items-center justify-between border-t border-line/45 mt-4">
                    <Button
                      onClick={() => setSelectedDraft(null)}
                      variant="outline"
                      className="h-9.5 rounded-xl border-line text-[12.5px]"
                    >
                      Back to list
                    </Button>
                    <Button
                      onClick={handleSchedule}
                      disabled={scheduling === selectedDraft.id}
                      className="h-9.5 rounded-xl bg-ink text-white text-[12.5px] px-5"
                    >
                      Schedule Draft
                    </Button>
                  </div>
                </div>
              )}
            </div>
          </motion.div>
        </div>
      )}
    </div>
  );
}
