'use client';

import Link from 'next/link';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import {
  ArrowUpRight,
  Calendar,
  CalendarPlus,
  Clock,
  Music2,
  Sparkles,
  TrendingUp,
} from 'lucide-react';

export function RecommendationCard({ recommendation, onAction, onAddToPlanner, loading, plannerLoading }) {
  const {
    storyTitle,
    formatLabel,
    reason,
    priority,
    bestPostingDay,
    bestPostingTime,
    trendingFormat,
    trendingAudio,
    suggestedHookStyle,
    action,
    publishConfidence,
    publishWindowNote,
  } = recommendation;

  return (
    <div className="card-elev relative overflow-hidden p-5">
      <div className="pointer-events-none absolute -right-12 -top-12 h-28 w-28 rounded-full bg-brand-soft blur-2xl" />
      <div className="relative">
        <div className="flex flex-wrap items-start justify-between gap-3">
          <div>
            <div className="flex items-center gap-2">
              <Sparkles className="h-4 w-4 text-brand" />
              <span className="text-[11px] font-medium uppercase tracking-wider text-brand">
                {priority}% match
              </span>
            </div>
            <h3 className="mt-2 font-display text-[18px] font-semibold leading-snug text-ink">
              {storyTitle}
            </h3>
            <Badge variant="outline" className="mt-2 rounded-full border-line bg-canvas text-[11px] font-normal text-ink-muted">
              {formatLabel}
            </Badge>
          </div>
        </div>

        <p className="mt-4 text-[13.5px] leading-relaxed text-ink-muted">{reason}</p>

        <div className="mt-4 rounded-xl border border-line/60 bg-canvas/50 px-3 py-2.5">
          <p className="text-[10.5px] font-semibold uppercase tracking-wider text-ink-subtle">Suggested window</p>
          <p className="mt-1 text-[12.5px] text-ink">{publishWindowNote || 'Weekday evenings work well for this format in India.'}</p>
          <div className="mt-2 flex flex-wrap items-center gap-3 text-[12px] text-ink-muted">
            <span className="inline-flex items-center gap-1"><Calendar className="h-3.5 w-3.5" />{bestPostingDay}</span>
            <span className="inline-flex items-center gap-1"><Clock className="h-3.5 w-3.5" />{bestPostingTime}</span>
            {publishConfidence && (
              <Badge variant="outline" className="rounded-full border-line text-[10px] capitalize">{publishConfidence} confidence</Badge>
            )}
          </div>
        </div>

        <div className="mt-3 grid gap-2 sm:grid-cols-2">
          <div className="rounded-xl border border-line/60 bg-canvas/50 px-3 py-2.5">
            <p className="flex items-center gap-1.5 text-[10.5px] font-semibold uppercase tracking-wider text-ink-subtle">
              <TrendingUp className="h-3 w-3" /> Trending format
            </p>
            <p className="mt-1 text-[12.5px] text-ink">{trendingFormat}</p>
          </div>
          <div className="rounded-xl border border-line/60 bg-canvas/50 px-3 py-2.5">
            <p className="flex items-center gap-1.5 text-[10.5px] font-semibold uppercase tracking-wider text-ink-subtle">
              <Music2 className="h-3 w-3" /> Audio / vibe
            </p>
            <p className="mt-1 text-[12.5px] text-ink">{trendingAudio}</p>
          </div>
        </div>

        <div className="mt-3 rounded-xl border border-line/60 bg-canvas/50 px-3 py-2.5">
          <p className="text-[10.5px] font-semibold uppercase tracking-wider text-ink-subtle">Hook style</p>
          <p className="mt-1 text-[12.5px] text-ink">{suggestedHookStyle}</p>
        </div>

        <div className="mt-5 flex flex-wrap gap-2">
          {onAddToPlanner && (
            <Button
              onClick={() => onAddToPlanner(recommendation)}
              disabled={plannerLoading}
              variant="outline"
              className="h-9 rounded-xl border-line text-[12.5px]"
            >
              <CalendarPlus className="mr-1 h-3.5 w-3.5" />
              Add to Planner
            </Button>
          )}
          <Button
            onClick={() => onAction(recommendation)}
            disabled={loading}
            className="h-9 rounded-xl bg-ink text-[12.5px] text-white hover:bg-ink/90"
          >
            {action === 'continue_draft' ? 'Continue draft' : 'Start in Studio'}
            <ArrowUpRight className="ml-1 h-3.5 w-3.5" />
          </Button>
          <Button asChild variant="outline" className="h-9 rounded-xl border-line text-[12.5px]">
            <Link href={`/stories/${recommendation.storyId}`}>View story</Link>
          </Button>
        </div>
      </div>
    </div>
  );
}
