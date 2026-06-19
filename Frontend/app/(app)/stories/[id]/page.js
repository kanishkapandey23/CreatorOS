'use client';

import { useQuery } from '@tanstack/react-query';
import { useParams, useRouter } from 'next/navigation';
import Link from 'next/link';
import { ArrowLeft, ArrowUpRight, Sparkles, Copy } from 'lucide-react';
import { storyService } from '@/services/story.service';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { toast } from 'sonner';

export default function StoryDetailPage() {
  const params = useParams();
  const router = useRouter();
  const { data: story, isLoading } = useQuery({ queryKey: ['story', params.id], queryFn: () => storyService.get(params.id) });

  if (isLoading) return <div className="flex h-[60vh] items-center justify-center text-[13px] text-ink-muted">Loading story…</div>;
  if (!story) return <div className="flex h-[60vh] items-center justify-center text-[13px] text-ink-muted">Story not found.</div>;

  return (
    <div className="mx-auto w-full max-w-5xl px-5 py-8 md:px-8 md:py-12">
      <button onClick={() => router.back()} className="mb-6 inline-flex items-center gap-1.5 text-[12.5px] text-ink-muted hover:text-ink">
        <ArrowLeft className="h-3.5 w-3.5" /> Back
      </button>

      <div className="grid gap-10 md:grid-cols-12">
        <article className="md:col-span-8">
          <div className="flex items-center gap-2">
            <Badge variant="outline" className="rounded-full border-line bg-card text-[11px] font-normal text-ink-muted">{story.category}</Badge>
            <Badge variant="outline" className="rounded-full border-line bg-card text-[11px] font-normal capitalize text-ink-muted">{story.status}</Badge>
            <span className="text-[11px] text-ink-subtle">{story.potential}% potential</span>
          </div>
          <h1 className="mt-4 font-display text-[34px] font-semibold leading-[1.1] tracking-tight text-ink md:text-[44px]">{story.title}</h1>
          <p className="mt-4 max-w-2xl text-[16px] leading-relaxed text-ink-muted">{story.summary}</p>

          <div className="mt-9 grid gap-4 sm:grid-cols-2">
            <div className="card-elev p-5">
              <p className="text-[11px] font-medium uppercase tracking-[0.18em] text-ink-subtle">Emotion</p>
              <p className="mt-2 font-display text-[18px] font-semibold text-ink">{story.emotion}</p>
            </div>
            <div className="card-elev p-5">
              <p className="text-[11px] font-medium uppercase tracking-[0.18em] text-ink-subtle">Lesson</p>
              <p className="mt-2 text-[14px] leading-relaxed text-ink">{story.lesson}</p>
            </div>
          </div>

          <section className="mt-9">
            <p className="text-[11px] font-medium uppercase tracking-[0.18em] text-ink-subtle">Tags</p>
            <div className="mt-2 flex flex-wrap gap-2">
              {story.tags?.map((t) => (
                <Badge key={t} variant="outline" className="rounded-full border-line bg-card text-[11.5px] font-normal text-ink-muted">#{t}</Badge>
              ))}
            </div>
          </section>

          <section className="mt-9">
            <p className="text-[11px] font-medium uppercase tracking-[0.18em] text-ink-subtle">Suggested formats</p>
            <div className="mt-2 grid gap-2 sm:grid-cols-3">
              {story.suggestedFormats?.map((f) => (
                <div key={f} className="rounded-xl border border-line bg-card px-4 py-3 text-[13px] text-ink">{f}</div>
              ))}
            </div>
          </section>

          <div className="mt-10">
            <Button asChild className="h-11 rounded-xl bg-ink px-5 text-[13.5px] text-white hover:bg-ink/90">
              <Link href={`/stories/${story.id}/workspace`}>Open workspace <ArrowUpRight className="ml-2 h-4 w-4" /></Link>
            </Button>
          </div>
        </article>

        <aside className="md:col-span-4">
          <div className="card-elev sticky top-20 p-5">
            <div className="flex items-center gap-2 text-[11.5px] font-medium uppercase tracking-wider text-ink-subtle">
              <Sparkles className="h-3.5 w-3.5 text-brand" /> Scroll-Stopper Hooks
            </div>
            <p className="mt-2 text-[13px] leading-relaxed text-ink-muted">
              Surfaced from your memory. Select a hook to copy or start writing in the workspace.
            </p>
            <div className="mt-4 space-y-2">
              {story.hooks && story.hooks.length > 0 ? (
                story.hooks.map((h, i) => (
                  <div key={i} className="group relative rounded-xl border border-line bg-canvas px-3 py-2.5 text-[12.5px] text-ink leading-relaxed">
                    <p className="pr-6">{h}</p>
                    <button
                      onClick={() => {
                        navigator.clipboard.writeText(h);
                        toast.success('Hook copied!');
                      }}
                      className="absolute right-2 top-2 text-ink-subtle hover:text-ink opacity-0 group-hover:opacity-100 transition-opacity"
                    >
                      <Copy className="h-3.5 w-3.5" />
                    </button>
                  </div>
                ))
              ) : (
                <div className="rounded-xl border border-dashed border-line bg-canvas px-3 py-2.5 text-[12.5px] text-ink-subtle italic">
                  No hook recommendations generated yet.
                </div>
              )}
            </div>
            <p className="mt-4 text-[11px] text-ink-subtle">Recommendations will personalize as you write more.</p>
          </div>
        </aside>
      </div>
    </div>
  );
}
