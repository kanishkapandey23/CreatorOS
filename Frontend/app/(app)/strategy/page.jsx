'use client';

import { useState } from 'react';
import { useRouter } from 'next/navigation';
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import { motion } from 'framer-motion';
import {
  Compass,
  RefreshCw,
  BookOpen,
  TrendingUp,
  PenLine,
} from 'lucide-react';
import { toast } from 'sonner';
import { PageHeader } from '@/components/layout/page-header';
import { ChipSelect } from '@/components/ui/chip-select';
import { Button } from '@/components/ui/button';
import { RecommendationCard } from '@/components/content/recommendation-card';
import { strategyService } from '@/services/strategy.service';
import { reflectionService } from '@/services/reflection.service';
import { draftService } from '@/services/draft.service';
import { plannerService } from '@/services/planner.service';

const MOODS = [
  { id: 'reflective', label: 'Reflective' },
  { id: 'happy', label: 'Happy' },
  { id: 'funny', label: 'Funny' },
  { id: 'emotional', label: 'Emotional' },
  { id: 'motivated', label: 'Motivated' },
  { id: 'nostalgic', label: 'Nostalgic' },
];

const MOOD_GOALS = {
  reflective: 'express_myself',
  happy: 'build_connection',
  funny: 'build_connection',
  emotional: 'express_myself',
  motivated: 'increase_reach',
  nostalgic: 'express_myself',
};

export default function StrategyPage() {
  const router = useRouter();
  const queryClient = useQueryClient();
  const [mood, setMood] = useState('reflective');
  const [results, setResults] = useState(null);
  const [actingId, setActingId] = useState(null);
  const [plannerId, setPlannerId] = useState(null);

  const { data: trends } = useQuery({
    queryKey: ['strategyTrends', mood],
    queryFn: () => strategyService.getTrends(mood),
    staleTime: 5 * 60 * 1000,
  });

  const recommendMutation = useMutation({
    mutationFn: () => strategyService.getRecommendations({
      mood,
      contentPreference: 'personal_story',
      goal: MOOD_GOALS[mood] || 'build_connection',
      intent: 'recommend_from_bank',
    }),
    onSuccess: (data) => setResults(data),
    onError: () => toast.error('Could not get recommendations'),
  });

  const startReflection = async () => {
    try {
      await reflectionService.startWithVibe({
        mood,
        goal: MOOD_GOALS[mood] || 'express_myself',
      });
      queryClient.invalidateQueries({ queryKey: ['reflection', 'session'] });
      router.push('/reflection');
    } catch {
      toast.error('Could not start reflection');
    }
  };

  const handleAddToPlanner = async (rec) => {
    setPlannerId(rec.id);
    try {
      let draftId = rec.draftId;
      if (!draftId || rec.action !== 'continue_draft') {
        const draft = await draftService.create(rec.storyId, rec.format);
        draftId = draft.id;
      }
      await plannerService.scheduleDraft(draftId, {
        scheduledAt: rec.scheduledAt,
        reminderEnabled: true,
        reminderOffsets: ['1d', '1h'],
        reminderChannels: ['in_app', 'email'],
      });
      toast.success(`Added to Planner · ${rec.bestPostingDay} ${rec.bestPostingTime}`);
      queryClient.invalidateQueries({ queryKey: ['planner'] });
      queryClient.invalidateQueries({ queryKey: ['notifications'] });
      router.push('/planner');
    } catch {
      toast.error('Could not add to Planner');
    } finally {
      setPlannerId(null);
    }
  };

  const handleRecommendationAction = async (rec) => {
    setActingId(rec.id);
    try {
      if (rec.action === 'continue_draft' && rec.draftId) {
        router.push(`/stories/${rec.storyId}/studio/${rec.draftId}`);
        return;
      }
      const draft = await draftService.create(rec.storyId, rec.format);
      router.push(`/stories/${rec.storyId}/studio/${draft.id}`);
    } catch {
      toast.error('Could not open Studio');
    } finally {
      setActingId(null);
    }
  };

  return (
    <div className="mx-auto max-w-5xl px-4 py-8 md:px-6">
      <PageHeader
        eyebrow="Strategist"
        title="What should you create today?"
        description="Pick your mood. We will recommend from your Story Bank or help you capture something new — using India trends and IST posting times."
      >
        {results && (
          <Button
            variant="outline"
            onClick={() => setResults(null)}
            className="rounded-xl border-line text-[13px]"
          >
            <RefreshCw className="mr-1.5 h-3.5 w-3.5" /> Reset
          </Button>
        )}
      </PageHeader>

      <div className="mt-8 grid gap-6 lg:grid-cols-[1fr_260px]">
        <div className="space-y-4">
          <div className="card-elev p-6">
            <h2 className="font-display text-[18px] font-semibold text-ink">How are you feeling?</h2>
            <ChipSelect className="mt-4" options={MOODS} value={mood} onChange={setMood} />

            {!results && (
              <div className="mt-6 grid gap-3 sm:grid-cols-2">
                <Button
                  onClick={() => recommendMutation.mutate()}
                  disabled={recommendMutation.isPending}
                  className="h-11 rounded-xl bg-ink text-[13px] text-white hover:bg-ink/90"
                >
                  <BookOpen className="mr-2 h-4 w-4" />
                  {recommendMutation.isPending ? 'Looking…' : 'From my Story Bank'}
                </Button>
                <Button
                  onClick={startReflection}
                  variant="outline"
                  className="h-11 rounded-xl border-line text-[13px]"
                >
                  <PenLine className="mr-2 h-4 w-4" /> Capture something new
                </Button>
              </div>
            )}
          </div>

          {results && (
            <motion.div initial={{ opacity: 0 }} animate={{ opacity: 1 }} className="space-y-4">
              {results.suggestReflection ? (
                <div className="card-elev p-6 text-center">
                  <p className="text-[14px] text-ink-muted">Your Story Bank is empty. Start with a reflection — we will use your mood from this check-in.</p>
                  <Button onClick={startReflection} className="mt-4 rounded-xl bg-ink text-white hover:bg-ink/90">
                    Start reflection
                  </Button>
                </div>
              ) : (
                results.recommendations.map((rec) => (
                  <RecommendationCard
                    key={rec.id}
                    recommendation={rec}
                    onAction={handleRecommendationAction}
                    onAddToPlanner={handleAddToPlanner}
                    loading={actingId === rec.id}
                    plannerLoading={plannerId === rec.id}
                  />
                ))
              )}
              <Button onClick={startReflection} variant="outline" className="w-full rounded-xl border-line text-[13px]">
                <PenLine className="mr-2 h-4 w-4" /> Or capture a new story instead
              </Button>
            </motion.div>
          )}
        </div>

        <aside className="card-elev h-fit p-5">
          <div className="flex items-center gap-2 text-[11px] font-medium uppercase tracking-[0.18em] text-ink-subtle">
            <TrendingUp className="h-3.5 w-3.5 text-brand" />
            India trends (IST)
          </div>
          {trends ? (
            <div className="mt-4 space-y-3 text-[12.5px]">
              <p className="text-ink-muted">
                Best slot: <span className="text-ink">{trends.suggestedDay} · {trends.suggestedTime}</span>
              </p>
              {(trends.trendingFormats || []).slice(0, 3).map((fmt) => (
                <div key={fmt} className="rounded-xl border border-line/60 bg-canvas/50 px-3 py-2 text-ink">{fmt}</div>
              ))}
              {(trends.trendingHookPatterns || []).slice(0, 1).map((hook) => (
                <p key={hook} className="italic text-ink-muted">{hook}</p>
              ))}
            </div>
          ) : (
            <p className="mt-4 text-[12px] text-ink-subtle">Loading…</p>
          )}
        </aside>
      </div>
    </div>
  );
}
