'use client';

import { useEffect, useState } from 'react';
import { useParams, useRouter } from 'next/navigation';
import { useQuery } from '@tanstack/react-query';
import { ArrowLeft, Save, Sparkles, History, Users } from 'lucide-react';
import { workspaceService } from '@/services/workspace.service';
import { storyService } from '@/services/story.service';
import { Button } from '@/components/ui/button';

const SECTIONS = [
  { id: 'hook', label: 'Hook', hint: 'A single line that stops the scroll.' },
  { id: 'experience', label: 'Experience', hint: 'What happened, in your voice.' },
  { id: 'conflict', label: 'Conflict', hint: 'The friction or tension that mattered.' },
  { id: 'lesson', label: 'Lesson', hint: 'What you took away — quietly.' },
  { id: 'cta', label: 'Call to action', hint: 'A small invitation, not a sales line.' },
];

export default function ContentWorkspacePage() {
  const params = useParams();
  const router = useRouter();
  const { data: story } = useQuery({ queryKey: ['story', params.id], queryFn: () => storyService.get(params.id) });
  const { data: draft } = useQuery({ queryKey: ['draft', params.id], queryFn: () => workspaceService.getDraft(params.id) });
  const [sections, setSections] = useState({ hook: '', experience: '', conflict: '', lesson: '', cta: '' });
  const [savedAt, setSavedAt] = useState(null);

  useEffect(() => {
    if (draft?.sections) setSections(draft.sections);
  }, [draft]);

  // Autosave-ready (debounced placeholder)
  useEffect(() => {
    const t = setTimeout(async () => {
      const res = await workspaceService.saveDraft({ storyId: params.id, sections });
      setSavedAt(res.savedAt);
    }, 800);
    return () => clearTimeout(t);
  }, [sections, params.id]);

  return (
    <div className="flex min-h-[calc(100vh-3.5rem)] flex-col xl:flex-row">
      <div className="min-w-0 flex-1">
        <div className="sticky top-14 z-10 border-b border-line bg-canvas/85 px-5 py-3 backdrop-blur-md md:px-8">
          <div className="mx-auto flex max-w-3xl items-center justify-between">
            <button onClick={() => router.back()} className="inline-flex items-center gap-1.5 text-[12.5px] text-ink-muted hover:text-ink"><ArrowLeft className="h-3.5 w-3.5" /> Back to story</button>
            <div className="flex items-center gap-3 text-[11.5px] text-ink-subtle">
              <Save className="h-3.5 w-3.5" />{savedAt ? `Saved ${new Date(savedAt).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}` : 'Autosaving…'}
            </div>
          </div>
        </div>

        <div className="mx-auto max-w-3xl px-5 py-10 md:px-8 md:py-12">
          <p className="text-[12px] font-medium uppercase tracking-[0.18em] text-ink-subtle">Workspace</p>
          <h1 className="mt-1.5 font-display text-[32px] font-semibold leading-tight tracking-tight text-ink md:text-[40px]">{story?.title || 'Untitled story'}</h1>
          <p className="mt-2 text-[14px] text-ink-muted">Write the piece, section by section. Nothing here is final.</p>

          <div className="mt-10 space-y-8">
            {SECTIONS.map((sec) => (
              <section key={sec.id}>
                <div className="flex items-baseline justify-between">
                  <h2 className="font-display text-[18px] font-semibold text-ink">{sec.label}</h2>
                  <span className="text-[11.5px] text-ink-subtle">{sec.hint}</span>
                </div>
                <textarea
                  value={sections[sec.id]}
                  onChange={(e) => setSections({ ...sections, [sec.id]: e.target.value })}
                  placeholder="Start writing…"
                  className="mt-2 min-h-[120px] w-full resize-y rounded-2xl border border-line bg-card px-5 py-4 text-[15px] leading-relaxed text-ink shadow-soft placeholder:text-ink-subtle focus:outline-none focus:ring-2 focus:ring-brand/30"
                />
              </section>
            ))}
          </div>

          <div className="mt-12 flex items-center justify-between border-t border-line pt-6">
            <p className="text-[12px] text-ink-subtle">Your draft is private. Only you can see it.</p>
            <Button className="h-10 rounded-xl bg-ink px-4 text-[13px] text-white hover:bg-ink/90">Preview</Button>
          </div>
        </div>
      </div>

      <aside className="hidden w-[320px] shrink-0 border-l border-line bg-card xl:block">
        <div className="sticky top-14 space-y-5 p-5">
          <div>
            <div className="flex items-center gap-2 text-[11.5px] font-medium uppercase tracking-wider text-ink-subtle"><Sparkles className="h-3.5 w-3.5 text-brand" /> AI suggestions</div>
            <div className="mt-2 space-y-2">
              {['Soften the hook by 4 words', 'Move lesson before conflict', 'Add a sensory detail'].map((s) => (
                <div key={s} className="rounded-xl border border-dashed border-line bg-canvas px-3 py-2.5 text-[12.5px] text-ink-muted">{s}</div>
              ))}
            </div>
            <p className="mt-2 text-[11px] text-ink-subtle">Suggestions will arrive here. Take what helps. Ignore the rest.</p>
          </div>
          <div className="soft-divider" />
          <div>
            <div className="flex items-center gap-2 text-[11.5px] font-medium uppercase tracking-wider text-ink-subtle"><History className="h-3.5 w-3.5" /> Version history</div>
            <p className="mt-2 text-[12.5px] text-ink-muted">Every save creates a quiet checkpoint.</p>
            <div className="mt-2 rounded-xl border border-dashed border-line bg-canvas px-3 py-3 text-[12px] text-ink-subtle">Versioning coming soon.</div>
          </div>
          <div className="soft-divider" />
          <div>
            <div className="flex items-center gap-2 text-[11.5px] font-medium uppercase tracking-wider text-ink-subtle"><Users className="h-3.5 w-3.5" /> Collaboration</div>
            <div className="mt-2 rounded-xl border border-dashed border-line bg-canvas px-3 py-3 text-[12px] text-ink-subtle">Invite editors — coming soon.</div>
          </div>
        </div>
      </aside>
    </div>
  );
}
