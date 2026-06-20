'use client';

import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { useParams, useRouter } from 'next/navigation';
import Link from 'next/link';
import { ArrowLeft, ArrowUpRight, Plus } from 'lucide-react';
import { storyService } from '@/services/story.service';
import { draftService, DRAFT_FORMATS } from '@/services/draft.service';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { ChipSelect } from '@/components/ui/chip-select';
import { DraftCard } from '@/components/content/story-card';
import { toast } from 'sonner';
import { useState } from 'react';

export default function StoryDetailPage() {
  const params = useParams();
  const router = useRouter();
  const queryClient = useQueryClient();
  const storyId = params.id;
  const [showFormatPicker, setShowFormatPicker] = useState(false);
  const [selectedFormat, setSelectedFormat] = useState('linkedin_post');

  const { data: story, isLoading } = useQuery({
    queryKey: ['story', storyId],
    queryFn: () => storyService.get(storyId),
  });
  const { data: drafts = [] } = useQuery({
    queryKey: ['story', storyId, 'drafts'],
    queryFn: () => draftService.listByStory(storyId),
  });

  const createDraftMutation = useMutation({
    mutationFn: (format) => draftService.create(storyId, format),
    onSuccess: (draft) => {
      queryClient.invalidateQueries({ queryKey: ['story', storyId, 'drafts'] });
      queryClient.invalidateQueries({ queryKey: ['stories'] });
      queryClient.invalidateQueries({ queryKey: ['story', storyId] });
      toast.success(`${draft.formatLabel} draft created`);
      router.push(`/stories/${storyId}/studio/${draft.id}`);
    },
    onError: () => toast.error('Failed to create draft'),
  });

  if (isLoading) return <div className="flex h-[60vh] items-center justify-center text-[13px] text-ink-muted">Loading story…</div>;
  if (!story) return <div className="flex h-[60vh] items-center justify-center text-[13px] text-ink-muted">Story not found.</div>;

  return (
    <div className="mx-auto w-full max-w-5xl px-5 py-8 md:px-8 md:py-12">
      <button onClick={() => router.push('/stories')} className="mb-6 inline-flex items-center gap-1.5 text-[12.5px] text-ink-muted hover:text-ink">
        <ArrowLeft className="h-3.5 w-3.5" /> Story Bank
      </button>

      <div className="flex flex-wrap items-center gap-2">
        <Badge variant="outline" className="rounded-full border-line bg-card text-[11px] font-normal text-ink-muted">{story.category}</Badge>
        <Badge variant="outline" className="rounded-full border-line bg-card text-[11px] font-normal capitalize text-ink-muted">{story.status}</Badge>
        <span className="text-[11px] text-ink-subtle">{story.emotion}</span>
      </div>

      <h1 className="mt-4 font-display text-[34px] font-semibold leading-[1.1] tracking-tight text-ink md:text-[44px]">{story.title}</h1>
      <p className="mt-4 max-w-2xl text-[16px] leading-relaxed text-ink-muted">{story.summary}</p>

      <div className="mt-8 grid gap-4 sm:grid-cols-2">
        <div className="card-elev p-5">
          <p className="text-[11px] font-medium uppercase tracking-[0.18em] text-ink-subtle">Lesson</p>
          <p className="mt-2 text-[14px] leading-relaxed text-ink">{story.lesson}</p>
        </div>
        <div className="card-elev p-5">
          <p className="text-[11px] font-medium uppercase tracking-[0.18em] text-ink-subtle">Tags</p>
          <div className="mt-2 flex flex-wrap gap-2">
            {(story.tags || []).map((t) => (
              <Badge key={t} variant="outline" className="rounded-full border-line bg-card text-[11.5px] font-normal text-ink-muted">#{t}</Badge>
            ))}
          </div>
        </div>
      </div>

      <section className="mt-10">
        <div className="flex items-center justify-between gap-4">
          <div>
            <p className="text-[11px] font-medium uppercase tracking-[0.18em] text-ink-subtle">Content drafts</p>
            <p className="mt-1 text-[13px] text-ink-muted">One story can become many pieces of content.</p>
          </div>
          <Button
            onClick={() => setShowFormatPicker((v) => !v)}
            className="h-9 rounded-xl bg-ink px-4 text-[12.5px] text-white hover:bg-ink/90"
          >
            <Plus className="mr-1.5 h-3.5 w-3.5" /> New draft
          </Button>
        </div>

        {showFormatPicker && (
          <div className="mt-4 card-elev p-5">
            <p className="text-[13px] font-medium text-ink">What would you like to create?</p>
            <ChipSelect
              className="mt-3"
              options={DRAFT_FORMATS}
              value={selectedFormat}
              onChange={setSelectedFormat}
            />
            <div className="mt-4 flex gap-2">
              <Button
                onClick={() => createDraftMutation.mutate(selectedFormat)}
                disabled={createDraftMutation.isPending}
                className="h-9 rounded-xl bg-ink text-[12.5px] text-white hover:bg-ink/90"
              >
                {createDraftMutation.isPending ? 'Creating…' : 'Create draft'}
              </Button>
              <Button variant="outline" onClick={() => setShowFormatPicker(false)} className="h-9 rounded-xl border-line text-[12.5px]">
                Cancel
              </Button>
            </div>
          </div>
        )}

        <div className="mt-4 space-y-2">
          {drafts.length === 0 ? (
            <div className="rounded-2xl border border-dashed border-line bg-canvas/40 px-5 py-8 text-center text-[13px] text-ink-muted">
              No drafts yet. Create a LinkedIn post, reel, carousel, or thread from this story.
            </div>
          ) : (
            drafts.map((d) => <DraftCard key={d.id} draft={d} storyId={storyId} />)
          )}
        </div>
      </section>

      <div className="mt-10">
        <Button asChild className="h-10 rounded-xl bg-ink px-4 text-[13px] text-white hover:bg-ink/90">
          <Link href={drafts[0] ? `/stories/${storyId}/studio/${drafts[0].id}` : `/stories/${storyId}/studio`}>
            Open in Studio <ArrowUpRight className="ml-1.5 h-4 w-4" />
          </Link>
        </Button>
      </div>
    </div>
  );
}
