'use client';

import { useState } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { useQuery } from '@tanstack/react-query';
import { useRouter } from 'next/navigation';
import { ArrowLeft, ArrowRight, Check, Sparkles, X } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { reflectionService } from '@/services/reflection.service';
import { toast } from 'sonner';

export default function ReflectionPage() {
  const router = useRouter();
  const { data } = useQuery({ queryKey: ['reflection', 'session'], queryFn: () => reflectionService.getActiveSession() });
  const prompts = data?.prompts || [];
  const [idx, setIdx] = useState(0);
  const [answers, setAnswers] = useState({});
  const [submitting, setSubmitting] = useState(false);

  const current = prompts[idx];
  const value = current ? (answers[current.id] || '') : '';
  const progress = prompts.length ? ((idx + 1) / prompts.length) * 100 : 0;

  const setValue = (v) => setAnswers((a) => ({ ...a, [current.id]: v }));

  const next = async () => {
    if (!current) return;
    await reflectionService.saveAnswer({ promptId: current.id, promptTitle: current.title, value });
    if (idx < prompts.length - 1) setIdx(idx + 1);
    else {
      setSubmitting(true);
      const res = await reflectionService.complete(data?.id);
      toast.success(`${res.storiesDiscovered} stories surfaced from your reflection`);
      router.push('/stories');
    }
  };

  const prev = () => idx > 0 && setIdx(idx - 1);

  if (!current) {
    return <div className="flex h-[70vh] items-center justify-center text-[13px] text-ink-muted">Preparing your reflection…</div>;
  }

  return (
    <div className="relative min-h-[calc(100vh-3.5rem)]">
      {/* Top exit bar */}
      <div className="sticky top-0 z-10 flex items-center justify-between border-b border-line bg-canvas/80 px-5 py-3 backdrop-blur-md md:px-8">
        <div className="flex items-center gap-2 text-[12.5px] text-ink-muted">
          <Sparkles className="h-3.5 w-3.5 text-brand" /> {data?.title || 'Reflection'}
        </div>
        <div className="flex items-center gap-4">
          <div className="flex items-center gap-2 text-[11.5px] text-ink-muted">
            <div className="h-1.5 w-40 overflow-hidden rounded-full bg-secondary">
              <motion.div className="h-full bg-brand" animate={{ width: `${progress}%` }} transition={{ duration: 0.4 }} />
            </div>
            {idx + 1} / {prompts.length}
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
            <p className="text-[11.5px] font-medium uppercase tracking-[0.18em] text-ink-subtle">Prompt {idx + 1}</p>
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

      {/* Bottom action bar */}
      <div className="fixed inset-x-0 bottom-0 z-20 border-t border-line bg-canvas/90 px-5 py-3 backdrop-blur-md md:px-8">
        <div className="mx-auto flex max-w-2xl items-center justify-between">
          <Button onClick={prev} disabled={idx === 0} variant="ghost" className="h-10 rounded-xl text-[13px] text-ink-muted hover:text-ink disabled:opacity-40">
            <ArrowLeft className="mr-1.5 h-4 w-4" /> Previous
          </Button>
          <p className="hidden text-[11.5px] text-ink-subtle md:block">Tip: a single honest sentence is enough.</p>
          <Button onClick={next} disabled={submitting} className="h-10 rounded-xl bg-ink px-4 text-[13px] text-white hover:bg-ink/90">
            {idx === prompts.length - 1 ? (<><Check className="mr-1.5 h-4 w-4" /> Finish</>) : (<>Continue <ArrowRight className="ml-1.5 h-4 w-4" /></>)}
          </Button>
        </div>
      </div>
    </div>
  );
}