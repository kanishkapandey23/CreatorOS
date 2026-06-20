'use client';

import { useEffect } from 'react';
import { useParams, useRouter } from 'next/navigation';
import Link from 'next/link';
import { useQuery } from '@tanstack/react-query';
import { draftService } from '@/services/draft.service';

export default function StudioEntryPage() {
  const params = useParams();
  const router = useRouter();
  const storyId = params.id;

  const { data: drafts = [], isLoading } = useQuery({
    queryKey: ['story', storyId, 'drafts'],
    queryFn: () => draftService.listByStory(storyId),
  });

  useEffect(() => {
    if (isLoading) return;
    if (drafts.length === 1) {
      router.replace(`/stories/${storyId}/studio/${drafts[0].id}`);
    }
  }, [drafts, isLoading, router, storyId]);

  if (isLoading) {
    return <div className="flex h-[60vh] items-center justify-center text-[13px] text-ink-muted">Opening Studio…</div>;
  }

  if (drafts.length > 1) {
    router.replace(`/stories/${storyId}`);
    return null;
  }

  return (
    <div className="mx-auto max-w-2xl px-5 py-16 text-center">
      <p className="text-[12px] font-medium uppercase tracking-[0.18em] text-ink-subtle">Studio</p>
      <h1 className="mt-3 font-display text-[28px] font-semibold text-ink">What would you like to create?</h1>
      <p className="mt-2 text-[14px] text-ink-muted">Choose a format to start your first draft.</p>
      <div className="mt-8 grid gap-3 sm:grid-cols-2">
        {[
          { id: 'linkedin_post', label: 'LinkedIn Post' },
          { id: 'instagram_reel', label: 'Instagram Reel' },
          { id: 'carousel', label: 'Carousel' },
          { id: 'twitter_thread', label: 'Twitter Thread' },
        ].map((f) => (
          <button
            key={f.id}
            onClick={async () => {
              const draft = await draftService.create(storyId, f.id);
              router.push(`/stories/${storyId}/studio/${draft.id}`);
            }}
            className="card-elev rounded-2xl p-5 text-left text-[15px] font-medium text-ink transition-shadow hover:shadow-pop"
          >
            {f.label}
          </button>
        ))}
      </div>
      <Link href={`/stories/${storyId}`} className="mt-8 inline-block text-[13px] text-ink-muted hover:text-ink">
        Back to story
      </Link>
    </div>
  );
}
