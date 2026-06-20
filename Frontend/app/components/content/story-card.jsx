'use client';

import Link from 'next/link';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import {
  NotebookPen,
  ChevronRight,
} from 'lucide-react';

export function StoryCard({ story, showActions = true }) {
  return (
    <div className="card-elev group flex h-full flex-col p-5 transition-shadow hover:shadow-pop">
      <Link href={`/stories/${story.id}`} className="min-w-0 flex-1">
        <div className="flex items-center justify-between gap-2">
          <Badge variant="outline" className="rounded-full border-line bg-canvas text-[11px] font-normal text-ink-muted">
            {story.category}
          </Badge>
          <span className="text-[11px] text-ink-subtle">
            {story.draftCount ?? 0} draft{(story.draftCount ?? 0) === 1 ? '' : 's'}
          </span>
        </div>
        <h3 className="mt-3 font-display text-[17px] font-semibold leading-snug text-ink">{story.title}</h3>
        <p className="mt-1.5 line-clamp-2 text-[13px] text-ink-muted">{story.summary}</p>
        <div className="mt-3 flex flex-wrap gap-1.5">
          {(story.tags || []).slice(0, 3).map((t) => (
            <Badge key={t} variant="outline" className="rounded-full border-line bg-canvas text-[10.5px] font-normal text-ink-muted">
              #{t}
            </Badge>
          ))}
        </div>
        <div className="mt-4 flex items-center justify-between text-[11.5px] text-ink-subtle">
          <span className="inline-flex items-center gap-1.5">
            <span className="h-1.5 w-1.5 rounded-full bg-brand" />
            {story.emotion}
          </span>
          <span className="capitalize">{story.status}</span>
        </div>
      </Link>

      {showActions && (
        <div className="mt-4 border-t border-line/60 pt-4">
          <Button asChild className="h-8 w-full rounded-lg bg-ink text-[11.5px] text-white hover:bg-ink/90">
            <Link href={`/stories/${story.id}/studio`}>
              <NotebookPen className="mr-1 h-3 w-3" /> Open in Studio
            </Link>
          </Button>
        </div>
      )}
    </div>
  );
}

export function DraftCard({ draft, storyId, onDelete }) {
  return (
    <div className="card-elev group flex flex-col sm:flex-row sm:items-center sm:justify-between p-5 transition-shadow hover:shadow-pop gap-4">
      <div>
        <div className="flex items-center gap-2">
          <p className="font-display text-[15.5px] font-semibold text-ink">{draft.formatLabel}</p>
          <Badge variant="secondary" className="rounded-full px-2 py-0.5 text-[10px] uppercase font-normal tracking-wider bg-secondary text-ink-muted">
            {draft.status}
          </Badge>
        </div>
        <p className="mt-1 text-[12px] text-ink-subtle">
          Last updated: {draft.updatedAt ? new Date(draft.updatedAt).toLocaleDateString(undefined, { month: 'short', day: 'numeric', hour: '2-digit', minute: '2-digit' }) : 'Never'}
        </p>
      </div>
      <div className="flex flex-wrap items-center gap-2">
        <Button asChild variant="outline" size="sm" className="h-8.5 rounded-lg border-line text-[12px] px-3.5">
          <Link href={`/stories/${storyId}/studio/${draft.id}`}>
            Open Preview
          </Link>
        </Button>
        <Button asChild variant="outline" size="sm" className="h-8.5 rounded-lg border-line text-[12px] px-3.5">
          <Link href={`/stories/${storyId}/studio/${draft.id}?edit=true`}>
            Edit
          </Link>
        </Button>
        {onDelete && (
          <Button
            onClick={() => {
              if (confirm('Are you sure you want to delete this draft?')) {
                onDelete(draft.id);
              }
            }}
            variant="ghost"
            size="sm"
            className="h-8.5 rounded-lg text-[12px] text-danger hover:bg-danger/10 hover:text-danger px-3"
          >
            Delete
          </Button>
        )}
      </div>
    </div>
  );
}
