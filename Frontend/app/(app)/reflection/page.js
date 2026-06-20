'use client';

import { useState, useEffect } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { useQuery, useQueryClient } from '@tanstack/react-query';
import { useRouter } from 'next/navigation';
import { ArrowLeft, ArrowRight, Check, Sparkles, X, Trash2, Save, Calendar } from 'lucide-react';
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

  // Review screen states
  const [reviewMode, setReviewMode] = useState(false);
  const [extractedStories, setExtractedStories] = useState([]);
  const [selectedStories, setSelectedStories] = useState([]); // Array of indexes
  const [savingStories, setSavingStories] = useState(false);

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
        toast.info('Extracting stories from your reflection...', { id: 'extraction' });
        try {
          const extractRes = await reflectionService.extractStories(sessionId);
          const stories = extractRes.stories || [];
          setExtractedStories(stories);
          setSelectedStories(stories.map((_, idx) => idx));
          setReviewMode(true);
          toast.dismiss('extraction');
          toast.success('Stories extracted! Review them below.');
        } catch (err) {
          toast.dismiss('extraction');
          toast.error('Failed to extract stories automatically');
          router.push('/stories');
        }
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

  const toggleStorySelection = (index) => {
    setSelectedStories((prev) =>
      prev.includes(index) ? prev.filter((i) => i !== index) : [...prev, index]
    );
  };

  const updateStoryField = (index, field, val) => {
    setExtractedStories((prev) =>
      prev.map((story, idx) => (idx === index ? { ...story, [field]: val } : story))
    );
  };

  const deleteStory = (index) => {
    setExtractedStories((prev) => prev.filter((_, idx) => idx !== index));
    setSelectedStories((prev) => prev.filter((i) => i !== index).map((i) => (i > index ? i - 1 : i)));
  };

  const handleSaveSelected = async () => {
    if (selectedStories.length === 0) {
      toast.error('Please select at least one story card to save');
      return;
    }
    setSavingStories(true);
    try {
      const storiesToSave = extractedStories.filter((_, idx) => selectedStories.includes(idx));
      await reflectionService.saveStories(sessionId, storiesToSave);
      toast.success(`${storiesToSave.length} ${storiesToSave.length === 1 ? 'story' : 'stories'} saved to Story Bank`);
      queryClient.invalidateQueries({ queryKey: ['stories'] });
      queryClient.invalidateQueries({ queryKey: ['workspace'] });
      router.push('/stories');
    } catch {
      toast.error('Failed to save selected stories');
    } finally {
      setSavingStories(false);
    }
  };

  if (isLoading || !ready || (!current && !reviewMode)) {
    return <div className="flex h-[70vh] items-center justify-center text-[13px] text-ink-muted">Preparing your reflection…</div>;
  }

  // --- REVIEW SCREEN VIEW ---
  if (reviewMode) {
    return (
      <div className="relative min-h-[calc(100vh-3.5rem)] bg-canvas pt-8 pb-32">
        <div className="mx-auto max-w-4xl px-5">
          <div className="text-center">
            <Badge variant="secondary" className="rounded-full bg-brand-soft text-brand text-[11px] font-normal mb-3">
              <Sparkles className="mr-1 h-3 w-3 inline" /> Memory Engine Active
            </Badge>
            <h1 className="font-display text-[32px] font-semibold tracking-tight text-ink md:text-[40px]">
              Review Discovered Stories
            </h1>
            <p className="mt-2 text-[14.5px] text-ink-muted max-w-2xl mx-auto">
              We parsed your journal reflection and generated these story entries. Customize their details or discard what you don't want.
            </p>
          </div>

          <div className="mt-10 space-y-6">
            {extractedStories.length === 0 ? (
              <div className="rounded-2xl border border-dashed border-line bg-card px-5 py-12 text-center">
                <p className="text-[14px] text-ink-muted">No story cards generated. You can head back to Story Bank.</p>
                <Button onClick={() => router.push('/stories')} className="mt-4 rounded-xl bg-ink text-white">
                  Go to Story Bank
                </Button>
              </div>
            ) : (
              extractedStories.map((story, idx) => {
                const isSelected = selectedStories.includes(idx);
                return (
                  <div
                    key={idx}
                    className={`card-elev border-2 transition-all p-6 ${
                      isSelected ? 'border-brand/40 bg-card shadow-soft' : 'border-line/60 bg-card/60 opacity-80'
                    }`}
                  >
                    <div className="flex items-start justify-between gap-4">
                      <div className="flex items-center gap-3">
                        <input
                          type="checkbox"
                          checked={isSelected}
                          onChange={() => toggleStorySelection(idx)}
                          className="h-4.5 w-4.5 rounded border-line text-brand focus:ring-brand/30"
                          id={`story-check-${idx}`}
                        />
                        <label htmlFor={`story-check-${idx}`} className="text-[13px] font-semibold text-ink-muted cursor-pointer">
                          Select Story Card
                        </label>
                      </div>
                      <button
                        onClick={() => deleteStory(idx)}
                        className="rounded-lg p-1.5 text-ink-subtle hover:bg-secondary hover:text-danger transition-colors"
                        title="Delete Card"
                      >
                        <Trash2 className="h-4 w-4" />
                      </button>
                    </div>

                    <div className="mt-4 space-y-4">
                      <div>
                        <label className="text-[11px] font-medium uppercase tracking-[0.1em] text-ink-subtle">Story Title</label>
                        <input
                          type="text"
                          value={story.title}
                          onChange={(e) => updateStoryField(idx, 'title', e.target.value)}
                          className="mt-1 w-full rounded-xl border border-line bg-canvas px-4 py-2.5 text-[14px] font-medium text-ink focus:outline-none focus:ring-2 focus:ring-brand/20"
                        />
                      </div>

                      <div className="grid gap-4 sm:grid-cols-2">
                        <div>
                          <label className="text-[11px] font-medium uppercase tracking-[0.1em] text-ink-subtle">Summary / Event</label>
                          <textarea
                            value={story.summary}
                            onChange={(e) => updateStoryField(idx, 'summary', e.target.value)}
                            rows={3}
                            className="mt-1 w-full resize-none rounded-xl border border-line bg-canvas px-4 py-2.5 text-[13.5px] leading-relaxed text-ink focus:outline-none focus:ring-2 focus:ring-brand/20"
                          />
                        </div>
                        <div>
                          <label className="text-[11px] font-medium uppercase tracking-[0.1em] text-ink-subtle">Lesson Takeaway</label>
                          <textarea
                            value={story.lesson}
                            onChange={(e) => updateStoryField(idx, 'lesson', e.target.value)}
                            rows={3}
                            className="mt-1 w-full resize-none rounded-xl border border-line bg-canvas px-4 py-2.5 text-[13.5px] leading-relaxed text-ink focus:outline-none focus:ring-2 focus:ring-brand/20"
                          />
                        </div>
                      </div>

                      <div className="flex flex-wrap gap-2 pt-2 border-t border-line/40 items-center justify-between">
                        <div className="flex gap-2">
                          <Badge variant="outline" className="rounded-full border-line bg-canvas text-[10.5px] font-normal text-ink-muted">
                            {story.category}
                          </Badge>
                          <Badge variant="outline" className="rounded-full border-line bg-canvas text-[10.5px] font-normal text-ink-muted capitalize">
                            {story.emotion}
                          </Badge>
                        </div>
                        <div className="flex gap-1.5">
                          {(story.tags || []).map((t) => (
                            <span key={t} className="text-[11.5px] text-ink-subtle">#{t}</span>
                          ))}
                        </div>
                      </div>
                    </div>
                  </div>
                );
              })
            )}
          </div>
        </div>

        <div className="fixed inset-x-0 bottom-0 z-20 border-t border-line bg-canvas/90 px-5 py-4 backdrop-blur-md md:px-8">
          <div className="mx-auto max-w-4xl flex items-center justify-between">
            <Button
              variant="ghost"
              onClick={() => {
                if (selectedStories.length === extractedStories.length) {
                  setSelectedStories([]);
                } else {
                  setSelectedStories(extractedStories.map((_, idx) => idx));
                }
              }}
              className="h-10 text-[13px] text-ink-muted rounded-xl"
            >
              {selectedStories.length === extractedStories.length ? 'Deselect All' : 'Select All'}
            </Button>
            <div className="flex gap-3">
              <Button
                variant="outline"
                onClick={() => router.push('/stories')}
                className="h-10 border-line text-[13px] rounded-xl"
              >
                Discard Journal
              </Button>
              <Button
                onClick={handleSaveSelected}
                disabled={savingStories || selectedStories.length === 0}
                className="h-10 rounded-xl bg-ink px-5 text-[13px] text-white hover:bg-ink/90 inline-flex items-center gap-1.5"
              >
                <Save className="h-4 w-4" />
                {savingStories ? 'Saving…' : `Save ${selectedStories.length} Selected`}
              </Button>
            </div>
          </div>
        </div>
      </div>
    );
  }

  // --- GUIDED QUESTIONS VIEW ---
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
