'use client';

import { useCallback, useEffect, useState } from 'react';
import { useParams, useRouter } from 'next/navigation';
import { useQuery, useQueryClient } from '@tanstack/react-query';
import { ArrowLeft, Save, Lightbulb } from 'lucide-react';
import { draftService } from '@/services/draft.service';
import { storyService } from '@/services/story.service';
import { workspaceService } from '@/services/workspace.service';
import { Button } from '@/components/ui/button';
import { MarkdownContent } from '@/components/content/markdown-content';
import { emptySections, normalizeSections } from '@/lib/draft-sections';
import { saveLastStudio } from '@/lib/studio-persistence';

const SECTIONS = [
  { id: 'hook', label: 'Hook', hint: 'A single line that stops the scroll.' },
  { id: 'experience', label: 'Experience', hint: 'What happened, in your voice.' },
  { id: 'conflict', label: 'Conflict', hint: 'The friction or tension that mattered.' },
  { id: 'lesson', label: 'Lesson', hint: 'What you took away — quietly.' },
  { id: 'cta', label: 'Call to action', hint: 'A small invitation, not a sales line.' },
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
  const queryClient = useQueryClient();
  const storyId = params.id;
  const draftId = params.draftId;

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

  const updateSection = useCallback((id, value) => {
    setSections((prev) => ({ ...prev, [id]: value }));
    setIsDirty(true);
  }, []);

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

  return (
    <div className="min-h-[calc(100vh-3.5rem)]">
      <div className="sticky top-14 z-10 border-b border-line bg-canvas/85 px-5 py-3 backdrop-blur-md md:px-8">
        <div className="mx-auto flex max-w-3xl items-center justify-between">
          <button
            onClick={() => router.push(`/stories/${storyId}`)}
            className="inline-flex items-center gap-1.5 text-[12.5px] text-ink-muted hover:text-ink"
          >
            <ArrowLeft className="h-3.5 w-3.5" /> Back to story
          </button>
          <div className="flex items-center gap-2 text-[11.5px] text-ink-subtle">
            <Save className="h-3.5 w-3.5" />
            {formatSavedAt(savedAt) || (hydrated ? 'Autosaving…' : 'Loading…')}
          </div>
        </div>
      </div>

      <div className="mx-auto max-w-3xl px-5 py-10 md:px-8 md:py-12">
        <p className="text-[12px] font-medium uppercase tracking-[0.18em] text-ink-subtle">Studio</p>
        <h1 className="mt-1.5 font-display text-[32px] font-semibold leading-tight tracking-tight text-ink md:text-[40px]">
          {story?.title || 'Untitled story'}
        </h1>
        <p className="mt-2 text-[14px] text-ink-muted">
          {draft?.formatLabel} · Develop your draft section by section.
        </p>

        <div className="mt-10 space-y-12">
          {SECTIONS.map((sec) => (
            <section key={sec.id}>
              <div className="flex items-baseline justify-between">
                <h2 className="font-display text-[18px] font-semibold text-ink">{sec.label}</h2>
                <span className="text-[11.5px] text-ink-subtle">{sec.hint}</span>
              </div>
              <textarea
                value={sections[sec.id]}
                onChange={(e) => updateSection(sec.id, e.target.value)}
                placeholder="Start writing…"
                className="mt-2 min-h-[120px] w-full resize-y rounded-2xl border border-line bg-card px-5 py-4 text-[15px] leading-relaxed text-ink shadow-soft placeholder:text-ink-subtle focus:outline-none focus:ring-2 focus:ring-brand/30"
              />
            </section>
          ))}
        </div>

        {(suggestions.length > 0 || loadingSuggestions) && (
          <section className="mt-14 rounded-2xl border border-line bg-card/50 p-5">
            <div className="flex items-center gap-2 text-[11.5px] font-medium uppercase tracking-wider text-ink-subtle">
              <Lightbulb className="h-3.5 w-3.5 text-brand" />
              Optional suggestions
              {loadingSuggestions && <span className="h-2 w-2 rounded-full bg-brand animate-pulse" />}
            </div>
            <p className="mt-1.5 text-[12px] text-ink-muted">Editable ideas — take what helps, ignore the rest.</p>
            <div className="mt-4 space-y-2">
              {suggestions.map((s, idx) => (
                <div key={idx} className="rounded-xl border border-line bg-canvas px-3 py-2.5">
                  <MarkdownContent className="text-[12.5px] text-ink-muted">{s}</MarkdownContent>
                </div>
              ))}
            </div>
          </section>
        )}

        <div className="mt-12 flex items-center justify-between">
          <p className="text-[12px] text-ink-subtle">Your draft is private. Leave anytime — progress is saved.</p>
          <Button
            onClick={() => router.push(`/planner?draft=${draftId}`)}
            variant="outline"
            className="h-10 rounded-xl border-line text-[13px]"
          >
            Add to Planner
          </Button>
        </div>
      </div>
    </div>
  );
}
