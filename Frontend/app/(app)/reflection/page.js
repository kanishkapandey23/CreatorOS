'use client';

import { useState, useEffect } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { useQuery, useQueryClient } from '@tanstack/react-query';
import { useRouter } from 'next/navigation';
import { ArrowLeft, ArrowRight, Check, Sparkles, X } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { reflectionService } from '@/services/reflection.service';
import { toast } from 'sonner';

const MOOD_LABELS = {
  reflective: 'Reflective',
  happy: 'Happy',
  funny: 'Light-hearted',
  emotional: 'Emotional',
  motivated: 'Motivated',
  nostalgic: 'Nostalgic',
  uncertain: 'Uncertain',
};

export default function ReflectionPage() {
  const router = useRouter();
  const queryClient = useQueryClient();
  const { data, isLoading } = useQuery({
    queryKey: ['reflection', 'session'],
    queryFn: () => reflectionService.getActiveSession(),
    staleTime: 0,
  });

  const [current, setCurrent] = useState(null);
  const [questionIndex, setQuestionIndex] = useState(0);
  const [totalQuestions, setTotalQuestions] = useState(3);
  const [detectedMood, setDetectedMood] = useState(null);
  const [sessionId, setSessionId] = useState(null);
  const [answers, setAnswers] = useState({});
  const [submitting, setSubmitting] = useState(false);
  const [ready, setReady] = useState(false);

  useEffect(() => {
    if (!data) return;
    setSessionId(data.id);
    setCurrent(data.currentPrompt);
    setQuestionIndex(data.questionIndex ?? 0);
    setTotalQuestions(data.totalQuestions ?? 3);
    setDetectedMood(data.detectedMood);
    setReady(true);
  }, [data]);

  const value = current ? (answers[current.id] || '') : '';
  const progress = totalQuestions ? ((questionIndex + 1) / totalQuestions) * 100 : 0;
  const isLastQuestion = questionIndex >= totalQuestions - 1;

  const setValue = (v) => setAnswers((a) => ({ ...a, [current.id]: v }));

  const next = async () => {
    if (!current || !sessionId) return;
    setSubmitting(true);
    try {
      const res = await reflectionService.saveAnswer({
        promptId: current.id,
        promptTitle: current.title,
        value,
      });

      if (res.detectedMood) setDetectedMood(res.detectedMood);

      if (res.isComplete || isLastQuestion) {
        const completeRes = await reflectionService.complete(sessionId);
        toast.success(
          completeRes.storiesDiscovered
            ? `${completeRes.storiesDiscovered} ${completeRes.storiesDiscovered === 1 ? 'story' : 'stories'} captured`
            : 'Reflection saved — no new stories this time'
        );
        queryClient.invalidateQueries({ queryKey: ['stories'] });
        queryClient.invalidateQueries({ queryKey: ['workspace'] });
        router.push('/stories');
        return;
      }

      if (res.nextPrompt) {
        setCurrent(res.nextPrompt);
        setQuestionIndex(res.questionIndex ?? questionIndex + 1);
      }
    } catch {
      toast.error('Could not save your answer');
    } finally {
      setSubmitting(false);
    }
  };

  const prev = () => {
    if (questionIndex > 0) {
      toast.info('Previous answers are saved — continue forward when ready.');
    }
  };

  if (isLoading || !ready || !current) {
    return <div className="flex h-[70vh] items-center justify-center text-[13px] text-ink-muted">Preparing your reflection…</div>;
  }

  return (
    <div className="relative min-h-[calc(100vh-3.5rem)]">
      <div className="sticky top-0 z-10 flex items-center justify-between border-b border-line bg-canvas/80 px-5 py-3 backdrop-blur-md md:px-8">
        <div className="flex items-center gap-2 text-[12.5px] text-ink-muted">
          <Sparkles className="h-3.5 w-3.5 text-brand" /> {data?.title || 'Reflection'}
          {detectedMood && (
            <Badge variant="outline" className="ml-1 rounded-full border-line bg-card text-[10px] font-normal text-ink-muted">
              {MOOD_LABELS[detectedMood] || detectedMood}
            </Badge>
          )}
        </div>
        <div className="flex items-center gap-4">
          <div className="flex items-center gap-2 text-[11.5px] text-ink-muted">
            <div className="h-1.5 w-40 overflow-hidden rounded-full bg-secondary">
              <motion.div className="h-full bg-brand" animate={{ width: `${progress}%` }} transition={{ duration: 0.4 }} />
            </div>
            {questionIndex + 1} / {totalQuestions}
          </div>
          <button onClick={() => router.push('/workspace')} className="rounded-lg p-1.5 text-ink-muted hover:bg-secondary hover:text-ink" aria-label="Close">
            <X className="h-4 w-4" />
          </button>
        </div>
      </div>

      <div className="mx-auto flex max-w-2xl flex-col items-center px-5 pt-16 pb-32 text-center md:pt-24">
        <AnimatePresence mode="wait">
          <motion.div
            key={current.id}
            initial={{ opacity: 0, y: 16 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0, y: -8 }}
            transition={{ duration: 0.35, ease: [0.22, 1, 0.36, 1] }}
            className="w-full"
          >
            <p className="text-[11.5px] font-medium uppercase tracking-[0.18em] text-ink-subtle">
              {current.sectionTitle || 'Reflection'}
            </p>
            <h1 className="mt-4 font-display text-[28px] font-semibold leading-snug tracking-tight text-ink md:text-[36px]">
              {current.title}
            </h1>
            <p className="mt-3 text-[14px] leading-relaxed text-ink-muted">{current.hint}</p>

            <div className="mt-9">
              <textarea
                value={value}
                onChange={(e) => setValue(e.target.value)}
                placeholder="Write freely. No one will judge what you type here."
                className="min-h-[220px] w-full resize-none rounded-2xl border border-line bg-card px-5 py-4 text-left text-[15px] leading-relaxed text-ink shadow-soft placeholder:text-ink-subtle focus:outline-none focus:ring-2 focus:ring-brand/30"
                autoFocus
              />
              <div className="mt-2 text-right text-[11.5px] text-ink-subtle">{value.length} characters</div>
            </div>
          </motion.div>
        </AnimatePresence>
      </div>

      <div className="fixed inset-x-0 bottom-0 z-20 border-t border-line bg-canvas/90 px-5 py-3 backdrop-blur-md md:px-8">
        <div className="mx-auto flex max-w-2xl items-center justify-between">
          <Button onClick={prev} disabled={questionIndex === 0} variant="ghost" className="h-10 rounded-xl text-[13px] text-ink-muted hover:text-ink disabled:opacity-40">
            <ArrowLeft className="mr-1.5 h-4 w-4" /> Previous
          </Button>
          <p className="hidden text-[11.5px] text-ink-subtle md:block">
            {questionIndex === 0 ? 'Start anywhere — we will follow your thread.' : 'Each answer shapes your next question.'}
          </p>
          <Button onClick={next} disabled={submitting || !value.trim()} className="h-10 rounded-xl bg-ink px-4 text-[13px] text-white hover:bg-ink/90">
            {isLastQuestion ? (
              <><Check className="mr-1.5 h-4 w-4" /> Finish</>
            ) : (
              <>Continue <ArrowRight className="ml-1.5 h-4 w-4" /></>
            )}
          </Button>
        </div>
      </div>
    </div>
  );
}
