'use client';

import { useCallback, useEffect, useState } from 'react';
import { useParams, useRouter, useSearchParams } from 'next/navigation';
import { useQuery, useQueryClient } from '@tanstack/react-query';
import { ArrowLeft, Save, Lightbulb, PenLine, Eye, Trash2, Copy, Check, Calendar, CalendarClock, Globe } from 'lucide-react';
import { draftService } from '@/services/draft.service';
import { storyService } from '@/services/story.service';
import { workspaceService } from '@/services/workspace.service';
import { plannerService } from '@/services/planner.service';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { MarkdownContent } from '@/components/content/markdown-content';
import { emptySections, normalizeSections } from '@/lib/draft-sections';
import { saveLastStudio } from '@/lib/studio-persistence';
import { toast } from 'sonner';

const SECTIONS = [
  { id: 'hook', label: 'Hook', hint: 'A single line that stops the scroll.' },
  { id: 'experience', label: 'Experience', hint: 'What happened, in your voice.' },
  { id: 'conflict', label: 'Conflict', hint: 'The friction or tension that mattered.' },
  { id: 'lesson', label: 'Lesson', hint: 'What you took away — quietly.' },
  { id: 'cta', label: 'Call to action', hint: 'A small invitation, not a sales line.' },
  { id: 'caption', label: 'Caption', hint: 'Secondary copy, context, or notes.' },
  { id: 'hashtags', label: 'Hashtags', hint: 'Relevant topic tags separated by spaces.' },
];

function formatSavedAt(iso) {
  if (!iso) return null;
  const diff = Date.now() - new Date(iso).getTime();
  if (diff < 60_000) return 'Saved just now';
  return `Saved ${new Date(iso).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}`;
}

export default function StudioDraftPage() {
  const params = useParams();
  const router = useRouter();
  const searchParams = useSearchParams();
  const queryClient = useQueryClient();
  
  const storyId = params.id;
  const draftId = params.draftId;
  const initialEdit = searchParams.get('edit') === 'true';

  const { data: story } = useQuery({ queryKey: ['story', storyId], queryFn: () => storyService.get(storyId) });
  const { data: draft, isSuccess: draftLoaded } = useQuery({
    queryKey: ['draft', draftId],
    queryFn: () => draftService.get(draftId),
  });

  const [sections, setSections] = useState(emptySections);
  const [hydrated, setHydrated] = useState(false);
  const [isDirty, setIsDirty] = useState(false);
  const [savedAt, setSavedAt] = useState(null);
  const [suggestions, setSuggestions] = useState([]);
  const [loadingSuggestions, setLoadingSuggestions] = useState(false);

  // Edit / Preview toggle state
  const [isEditing, setIsEditing] = useState(initialEdit);
  const [copied, setCopied] = useState(false);

  // Scheduling states
  const [showScheduleModal, setShowScheduleModal] = useState(false);
  const [scheduleDate, setScheduleDate] = useState('');
  const [scheduleTime, setScheduleTime] = useState('19:30');

  useEffect(() => {
    if (storyId && draftId) saveLastStudio(storyId, draftId);
  }, [storyId, draftId]);

  useEffect(() => {
    if (!draftLoaded || !draft) return;
    setSections(normalizeSections(draft.sections));
    setSavedAt(draft.updatedAt || null);
    setHydrated(true);
    setIsDirty(false);
  }, [draftLoaded, draft]);

  // Set default scheduling values
  useEffect(() => {
    if (draft?.scheduledAt) {
      const dt = new Date(draft.scheduledAt);
      const yr = dt.getFullYear();
      const mo = String(dt.getMonth() + 1).padStart(2, '0');
      const dy = String(dt.getDate()).padStart(2, '0');
      setScheduleDate(`${yr}-${mo}-${dy}`);
      const hr = String(dt.getHours()).padStart(2, '0');
      const mn = String(dt.getMinutes()).padStart(2, '0');
      setScheduleTime(`${hr}:${mn}`);
    } else {
      const today = new Date();
      const yr = today.getFullYear();
      const mo = String(today.getMonth() + 1).padStart(2, '0');
      const dy = String(today.getDate()).padStart(2, '0');
      setScheduleDate(`${yr}-${mo}-${dy}`);
    }
  }, [draft]);

  const updateSection = useCallback((id, value) => {
    setSections((prev) => ({ ...prev, [id]: value }));
    setIsDirty(true);
  }, []);

  // Autosave
  useEffect(() => {
    if (!hydrated || !isDirty) return undefined;

    const timer = setTimeout(async () => {
      try {
        const res = await draftService.save(draftId, sections);
        setSavedAt(res.savedAt);
        setIsDirty(false);
        queryClient.setQueryData(['draft', draftId], (prev) =>
          prev ? { ...prev, sections, updatedAt: res.savedAt } : prev
        );

        setLoadingSuggestions(true);
        const sugRes = await workspaceService.getSuggestions(storyId);
        if (sugRes.suggestions?.length > 0) {
          setSuggestions(sugRes.suggestions);
        }
      } catch (err) {
        console.error('Studio autosave error:', err);
      } finally {
        setLoadingSuggestions(false);
      }
    }, 800);

    return () => clearTimeout(timer);
  }, [sections, draftId, storyId, hydrated, isDirty, queryClient]);

  // Assemble full text content for copy/preview
  const getAssembledContent = () => {
    const parts = [];
    if (sections.hook) parts.push(sections.hook);
    if (sections.experience) parts.push(sections.experience);
    if (sections.conflict) parts.push(sections.conflict);
    if (sections.lesson) parts.push(sections.lesson);
    if (sections.cta) parts.push(sections.cta);
    if (sections.caption) parts.push(sections.caption);
    if (sections.hashtags) parts.push(sections.hashtags);
    return parts.join('\n\n');
  };

  const copyToClipboard = () => {
    navigator.clipboard.writeText(getAssembledContent());
    setCopied(true);
    toast.success('Copied content to clipboard');
    setTimeout(() => setCopied(false), 2000);
  };

  // Actions
  const handleDuplicate = async () => {
    try {
      const dup = await draftService.duplicate(draftId);
      toast.success('Draft duplicated successfully');
      queryClient.invalidateQueries({ queryKey: ['story', storyId, 'drafts'] });
      router.push(`/stories/${storyId}/studio/${dup.id}`);
    } catch {
      toast.error('Failed to duplicate draft');
    }
  };

  const handleDelete = async () => {
    if (confirm('Are you sure you want to delete this draft?')) {
      try {
        await draftService.remove(draftId);
        toast.success('Draft deleted');
        queryClient.invalidateQueries({ queryKey: ['story', storyId, 'drafts'] });
        queryClient.invalidateQueries({ queryKey: ['planner'] });
        router.push(`/stories/${storyId}`);
      } catch {
        toast.error('Failed to delete draft');
      }
    }
  };

  const handleMarkPublished = async () => {
    try {
      await draftService.update(draftId, { status: 'published' });
      toast.success('Draft marked as Published');
      queryClient.invalidateQueries({ queryKey: ['draft', draftId] });
      queryClient.invalidateQueries({ queryKey: ['story', storyId, 'drafts'] });
      queryClient.invalidateQueries({ queryKey: ['planner'] });
    } catch {
      toast.error('Failed to update status');
    }
  };

  const handleSchedule = async () => {
    if (!scheduleDate || !scheduleTime) {
      toast.error('Please choose a valid date and time');
      return;
    }
    try {
      const isoStr = new Date(`${scheduleDate}T${scheduleTime}`).toISOString();
      await plannerService.scheduleDraft(draftId, {
        scheduledAt: isoStr,
        reminderEnabled: true,
      });
      toast.success('Draft scheduled successfully');
      setShowScheduleModal(false);
      queryClient.invalidateQueries({ queryKey: ['draft', draftId] });
      queryClient.invalidateQueries({ queryKey: ['story', storyId, 'drafts'] });
      queryClient.invalidateQueries({ queryKey: ['planner'] });
    } catch {
      toast.error('Failed to schedule draft');
    }
  };

  const handleUnschedule = async () => {
    try {
      await plannerService.scheduleDraft(draftId, { scheduledAt: null });
      toast.success('Removed schedule');
      queryClient.invalidateQueries({ queryKey: ['draft', draftId] });
      queryClient.invalidateQueries({ queryKey: ['story', storyId, 'drafts'] });
      queryClient.invalidateQueries({ queryKey: ['planner'] });
    } catch {
      toast.error('Failed to unschedule');
    }
  };

  return (
    <div className="min-h-[calc(100vh-3.5rem)] bg-canvas pb-20">
      {/* Dynamic Sub-header */}
      <div className="sticky top-14 z-10 border-b border-line bg-canvas/85 px-5 py-3 backdrop-blur-md md:px-8">
        <div className="mx-auto flex max-w-3xl items-center justify-between">
          <button
            onClick={() => router.push(`/stories/${storyId}`)}
            className="inline-flex items-center gap-1.5 text-[12.5px] text-ink-muted hover:text-ink"
          >
            <ArrowLeft className="h-3.5 w-3.5" /> Back to story
          </button>

          <div className="flex items-center gap-3">
            {isEditing ? (
              <Button
                onClick={() => setIsEditing(false)}
                className="h-8.5 rounded-lg bg-ink px-4 text-[12px] text-white hover:bg-ink/90 inline-flex items-center gap-1.5"
              >
                <Eye className="h-3.5 w-3.5" /> Preview Draft
              </Button>
            ) : (
              <Button
                onClick={() => setIsEditing(true)}
                variant="outline"
                className="h-8.5 rounded-lg border-line text-[12px] px-4 inline-flex items-center gap-1.5"
              >
                <PenLine className="h-3.5 w-3.5" /> Edit Draft
              </Button>
            )}
            <div className="hidden sm:flex items-center gap-2 text-[11.5px] text-ink-subtle border-l border-line pl-3">
              <Save className="h-3.5 w-3.5" />
              {formatSavedAt(savedAt) || (hydrated ? 'Saved' : 'Loading…')}
            </div>
          </div>
        </div>
      </div>

      <div className="mx-auto max-w-3xl px-5 py-8 md:px-8">
        <div>
          <Badge variant="outline" className="rounded-full border-line bg-card text-[10.5px] font-normal text-ink-muted">
            {draft?.formatLabel || 'LinkedIn Post'}
          </Badge>
          {draft?.scheduledAt && (
            <Badge variant="outline" className="ml-2 rounded-full border-brand bg-brand-soft text-[10.5px] font-normal text-brand">
              <CalendarClock className="mr-1 h-3.5 w-3.5 inline" /> Scheduled
            </Badge>
          )}
          {draft?.status === 'published' && (
            <Badge variant="outline" className="ml-2 rounded-full border-success bg-success-soft text-[10.5px] font-normal text-success">
              <Globe className="mr-1 h-3.5 w-3.5 inline" /> Published
            </Badge>
          )}
          <h1 className="mt-2.5 font-display text-[28px] font-semibold leading-tight tracking-tight text-ink md:text-[36px]">
            {story?.title || 'Untitled story'}
          </h1>
          <p className="mt-1 text-[13.5px] text-ink-muted">
            Develop your post draft from raw thoughts to a polished social media piece.
          </p>
        </div>

        {/* --- INLINE SCHEDULER POP-UP --- */}
        {showScheduleModal && (
          <div className="mt-6 card-elev border border-line bg-card p-5 rounded-2xl">
            <h3 className="font-display text-[15px] font-semibold text-ink">Schedule Draft</h3>
            <p className="text-[12.5px] text-ink-muted mt-0.5">Select a release time on your calendar.</p>
            <div className="mt-4 grid gap-3 sm:grid-cols-2">
              <div>
                <label className="text-[11px] font-semibold text-ink-muted">Date</label>
                <input
                  type="date"
                  value={scheduleDate}
                  onChange={(e) => setScheduleDate(e.target.value)}
                  className="mt-1 w-full rounded-xl border border-line bg-canvas px-3 py-2 text-[13.5px] text-ink focus:outline-none"
                />
              </div>
              <div>
                <label className="text-[11px] font-semibold text-ink-muted">Time (IST)</label>
                <input
                  type="time"
                  value={scheduleTime}
                  onChange={(e) => setScheduleTime(e.target.value)}
                  className="mt-1 w-full rounded-xl border border-line bg-canvas px-3 py-2 text-[13.5px] text-ink focus:outline-none"
                />
              </div>
            </div>
            <div className="mt-5 flex gap-2 justify-end">
              <Button onClick={() => setShowScheduleModal(false)} variant="ghost" className="h-8.5 rounded-lg text-[12px]">
                Cancel
              </Button>
              <Button onClick={handleSchedule} className="h-8.5 rounded-lg bg-ink text-white text-[12px] px-4">
                Schedule Now
              </Button>
            </div>
          </div>
        )}

        {/* --- DEFAULT PREVIEW MODE --- */}
        {!isEditing && (
          <div className="mt-8 space-y-6">
            <div className="card-elev border border-line bg-card p-6 md:p-8 rounded-2xl shadow-soft">
              {/* Mock Social Header */}
              <div className="flex items-center gap-3 border-b border-line/45 pb-4 mb-5">
                <div className="h-10 w-10 rounded-full bg-brand-soft text-brand font-semibold flex items-center justify-center text-[15px]">
                  C
                </div>
                <div>
                  <p className="text-[13.5px] font-semibold text-ink">Creator</p>
                  <p className="text-[11px] text-ink-subtle">
                    {draft?.scheduledAt ? `Scheduled for ${new Date(draft.scheduledAt).toLocaleDateString(undefined, { weekday: 'short', month: 'short', day: 'numeric', hour: '2-digit', minute: '2-digit' })}` : 'Draft Copy'}
                  </p>
                </div>
              </div>

              {/* Assembled Content */}
              <div className="space-y-4 text-[14.5px] leading-relaxed text-ink whitespace-pre-wrap">
                {sections.hook && <p className="font-semibold text-ink text-[15.5px]">{sections.hook}</p>}
                {sections.experience && <p>{sections.experience}</p>}
                {sections.conflict && <p className="border-l-2 border-brand/20 pl-3 italic text-ink-muted">{sections.conflict}</p>}
                {sections.lesson && <p className="font-medium">{sections.lesson}</p>}
                {sections.cta && <p className="font-semibold text-brand">{sections.cta}</p>}
                {sections.caption && (
                  <div className="pt-3 border-t border-line/40 text-[13px] text-ink-muted">
                    {sections.caption}
                  </div>
                )}
                {sections.hashtags && <p className="text-[13px] text-brand">{sections.hashtags}</p>}

                {!sections.hook && !sections.experience && !sections.lesson && (
                  <p className="text-center text-ink-subtle py-8 text-[13px]">Your draft content is empty. Click "Edit Draft" to start writing.</p>
                )}
              </div>

              <div className="mt-8 border-t border-line/45 pt-4 flex items-center justify-between">
                <p className="text-[11.5px] text-ink-subtle">This preview mimics the final published structure.</p>
                <Button
                  onClick={copyToClipboard}
                  variant="ghost"
                  className="h-8 text-[12px] text-ink-muted hover:text-ink inline-flex items-center gap-1.5 px-3"
                >
                  {copied ? <Check className="h-3.5 w-3.5 text-brand" /> : <Copy className="h-3.5 w-3.5" />}
                  Copy Post
                </Button>
              </div>
            </div>

            {/* Quick Actions Panel */}
            <div className="flex flex-wrap items-center justify-between border-t border-line/65 pt-6 gap-3">
              <div className="flex flex-wrap gap-2">
                <Button
                  onClick={() => setIsEditing(true)}
                  className="h-9.5 rounded-xl bg-ink px-4.5 text-[13px] text-white hover:bg-ink/90 inline-flex items-center gap-1.5"
                >
                  <PenLine className="h-4 w-4" /> Edit Copy
                </Button>

                {draft?.scheduledAt ? (
                  <>
                    <Button
                      onClick={() => setShowScheduleModal(true)}
                      variant="outline"
                      className="h-9.5 rounded-xl border-line text-[13px] px-4.5 inline-flex items-center gap-1.5"
                    >
                      <Calendar className="h-4 w-4" /> Reschedule
                    </Button>
                    <Button
                      onClick={handleUnschedule}
                      variant="outline"
                      className="h-9.5 rounded-xl border-line text-[13px] px-4.5 text-ink-muted hover:text-ink"
                    >
                      Remove Schedule
                    </Button>
                  </>
                ) : (
                  <Button
                    onClick={() => setShowScheduleModal(true)}
                    variant="outline"
                    className="h-9.5 rounded-xl border-line text-[13px] px-4.5 inline-flex items-center gap-1.5"
                  >
                    <Calendar className="h-4 w-4" /> Add to Planner
                  </Button>
                )}

                {draft?.status !== 'published' && (
                  <Button
                    onClick={handleMarkPublished}
                    variant="outline"
                    className="h-9.5 rounded-xl border-line text-[13px] px-4.5"
                  >
                    Mark Published
                  </Button>
                )}

                <Button
                  onClick={handleDuplicate}
                  variant="outline"
                  className="h-9.5 rounded-xl border-line text-[13px] px-4.5"
                >
                  Duplicate
                </Button>
              </div>

              <Button
                onClick={handleDelete}
                variant="ghost"
                className="h-9.5 rounded-xl text-[13px] text-danger hover:bg-danger/10 px-4"
              >
                <Trash2 className="h-4 w-4 inline mr-1" /> Delete Draft
              </Button>
            </div>
          </div>
        )}

        {/* --- EDIT MODE --- */}
        {isEditing && (
          <div className="mt-8 space-y-8">
            <div className="space-y-6">
              {SECTIONS.map((sec) => (
                <section key={sec.id}>
                  <div className="flex items-baseline justify-between">
                    <h2 className="font-display text-[16.5px] font-semibold text-ink">{sec.label}</h2>
                    <span className="text-[11.5px] text-ink-subtle">{sec.hint}</span>
                  </div>
                  <textarea
                    value={sections[sec.id] || ''}
                    onChange={(e) => updateSection(sec.id, e.target.value)}
                    placeholder={`Start typing your ${sec.label.toLowerCase()}…`}
                    className="mt-2 min-h-[100px] w-full resize-y rounded-xl border border-line bg-card px-4 py-3 text-[14.5px] leading-relaxed text-ink shadow-soft focus:outline-none focus:ring-2 focus:ring-brand/35"
                  />
                </section>
              ))}
            </div>

            <div className="flex items-center justify-between border-t border-line/65 pt-6">
              <p className="text-[11.5px] text-ink-subtle">Autosave is enabled. Exit or preview when you're done.</p>
              <Button
                onClick={() => setIsEditing(false)}
                className="h-10 rounded-xl bg-ink px-5 text-[13px] text-white hover:bg-ink/90 inline-flex items-center gap-1.5"
              >
                <Eye className="h-4 w-4" /> Save & Preview
              </Button>
            </div>
          </div>
        )}

        {/* Optional AI Suggestions */}
        {suggestions.length > 0 && (
          <section className="mt-14 rounded-2xl border border-line bg-card/40 p-5">
            <div className="flex items-center gap-2 text-[11.5px] font-medium uppercase tracking-wider text-ink-subtle">
              <Lightbulb className="h-3.5 w-3.5 text-brand" />
              Creative Suggestions
            </div>
            <p className="mt-1.5 text-[12px] text-ink-muted">Optional AI angles and improvements — copy whatever helps.</p>
            <div className="mt-4 space-y-2">
              {suggestions.map((s, idx) => (
                <div key={idx} className="rounded-xl border border-line bg-card/65 px-4 py-3 text-[12.5px] text-ink-muted leading-relaxed">
                  <MarkdownContent>{s}</MarkdownContent>
                </div>
              ))}
            </div>
          </section>
        )}
      </div>
    </div>
  );
}
