'use client';

import { useMemo, useState } from 'react';
import { useQuery } from '@tanstack/react-query';
import { motion } from 'framer-motion';
import { Search, BookOpen } from 'lucide-react';
import { storyService } from '@/services/story.service';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { EmptyState } from '@/components/layout/empty-state';
import { PageHeader } from '@/components/layout/page-header';
import { StoryCard } from '@/components/content/story-card';

const STATUSES = ['all', 'idea', 'draft', 'planned', 'published'];

export default function StoryBankPage() {
  const { data: stories = [] } = useQuery({ queryKey: ['stories'], queryFn: () => storyService.list() });
  const [q, setQ] = useState('');
  const [status, setStatus] = useState('all');
  const [category, setCategory] = useState('all');
  const [sort, setSort] = useState('recent');

  const categories = useMemo(() => {
    const set = new Set(stories.map((s) => s.category).filter(Boolean));
    return ['all', ...Array.from(set)];
  }, [stories]);

  const filtered = useMemo(() => {
    let list = stories;
    if (q) {
      const lower = q.toLowerCase();
      list = list.filter((s) =>
        (s.title + s.summary + s.category + s.emotion + (s.tags || []).join(' ')).toLowerCase().includes(lower)
      );
    }
    if (status !== 'all') list = list.filter((s) => s.status === status);
    if (category !== 'all') list = list.filter((s) => s.category === category);
    if (sort === 'recent') list = [...list].sort((a, b) => (a.createdAt < b.createdAt ? 1 : -1));
    if (sort === 'drafts') list = [...list].sort((a, b) => (b.draftCount || 0) - (a.draftCount || 0));
    return list;
  }, [stories, q, status, category, sort]);

  return (
    <div className="mx-auto w-full max-w-6xl px-5 py-10 md:px-8 md:py-12">
      <PageHeader
        eyebrow="Library"
        title="Story Bank"
        description="Your personal memory vault. What stories do you already have?"
      />

      <div className="mt-7 flex flex-wrap items-center gap-2">
        <div className="flex min-w-[240px] flex-1 items-center gap-2 rounded-xl border border-line bg-card px-3 py-2 shadow-soft">
          <Search className="h-4 w-4 text-ink-subtle" />
          <input
            className="w-full bg-transparent text-[13.5px] placeholder:text-ink-subtle focus:outline-none"
            placeholder="Search stories…"
            value={q}
            onChange={(e) => setQ(e.target.value)}
          />
        </div>
        <Select value={status} onValueChange={setStatus}>
          <SelectTrigger className="h-10 w-[130px] rounded-xl border-line bg-card text-[13px]">
            <SelectValue />
          </SelectTrigger>
          <SelectContent>
            {STATUSES.map((s) => (
              <SelectItem key={s} value={s} className="capitalize">{s}</SelectItem>
            ))}
          </SelectContent>
        </Select>
        <Select value={category} onValueChange={setCategory}>
          <SelectTrigger className="h-10 w-[150px] rounded-xl border-line bg-card text-[13px]">
            <SelectValue placeholder="Category" />
          </SelectTrigger>
          <SelectContent>
            {categories.map((c) => (
              <SelectItem key={c} value={c} className="capitalize">{c === 'all' ? 'All categories' : c}</SelectItem>
            ))}
          </SelectContent>
        </Select>
        <Select value={sort} onValueChange={setSort}>
          <SelectTrigger className="h-10 w-[150px] rounded-xl border-line bg-card text-[13px]">
            <SelectValue />
          </SelectTrigger>
          <SelectContent>
            <SelectItem value="recent">Most recent</SelectItem>
            <SelectItem value="drafts">Most drafts</SelectItem>
          </SelectContent>
        </Select>
      </div>

      {filtered.length === 0 ? (
        <div className="mt-10">
          <EmptyState
            icon={BookOpen}
            title="No stories match."
            description="Start a reflection to capture new experiences, or clear your filters."
          />
        </div>
      ) : (
        <motion.div
          initial={{ opacity: 0, y: 8 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.3 }}
          className="mt-7 grid gap-4 sm:grid-cols-2 lg:grid-cols-3"
        >
          {filtered.map((s, i) => (
            <motion.div
              key={s.id}
              initial={{ opacity: 0, y: 6 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ duration: 0.25, delay: i * 0.03 }}
            >
              <StoryCard story={s} />
            </motion.div>
          ))}
        </motion.div>
      )}
    </div>
  );
}
