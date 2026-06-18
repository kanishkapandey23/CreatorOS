'use client';

import Link from 'next/link';
import { useMemo, useState } from 'react';
import { useQuery } from '@tanstack/react-query';
import { motion } from 'framer-motion';
import { Search, Filter, BookOpen, Plus } from 'lucide-react';
import { storyService } from '@/services/story.service';
import { Input } from '@/components/ui/input';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { EmptyState } from '@/components/layout/empty-state';

const STATUSES = ['all', 'idea', 'draft', 'published'];

export default function StoryBankPage() {
  const { data: stories = [] } = useQuery({ queryKey: ['stories'], queryFn: () => storyService.list() });
  const [q, setQ] = useState('');
  const [status, setStatus] = useState('all');
  const [sort, setSort] = useState('recent');

  const filtered = useMemo(() => {
    let list = stories;
    if (q) list = list.filter((s) => (s.title + s.summary + s.category + s.emotion).toLowerCase().includes(q.toLowerCase()));
    if (status !== 'all') list = list.filter((s) => s.status === status);
    if (sort === 'recent') list = [...list].sort((a, b) => (a.createdAt < b.createdAt ? 1 : -1));
    if (sort === 'potential') list = [...list].sort((a, b) => b.potential - a.potential);
    return list;
  }, [stories, q, status, sort]);

  return (
    <div className="mx-auto w-full max-w-6xl px-5 py-10 md:px-8 md:py-12">
      <div className="flex flex-wrap items-end justify-between gap-4">
        <div>
          <p className="text-[12px] font-medium uppercase tracking-[0.18em] text-ink-subtle">Library</p>
          <h1 className="mt-1.5 font-display text-[30px] font-semibold tracking-tight text-ink md:text-[36px]">Story Bank</h1>
          <p className="mt-1.5 max-w-xl text-[13.5px] text-ink-muted">All the moments you've noticed, in one quiet place.</p>
        </div>
        <Button className="h-10 rounded-xl bg-ink px-4 text-[13px] text-white hover:bg-ink/90">
          <Plus className="mr-1.5 h-4 w-4" /> New story
        </Button>
      </div>

      <div className="mt-7 flex flex-wrap items-center gap-2">
        <div className="flex flex-1 min-w-[240px] items-center gap-2 rounded-xl border border-line bg-card px-3 py-2 shadow-soft">
          <Search className="h-4 w-4 text-ink-subtle" />
          <input className="w-full bg-transparent text-[13.5px] placeholder:text-ink-subtle focus:outline-none" placeholder="Search stories…" value={q} onChange={(e) => setQ(e.target.value)} />
        </div>
        <Select value={status} onValueChange={setStatus}>
          <SelectTrigger className="h-10 w-[140px] rounded-xl border-line bg-card text-[13px]">
            <SelectValue />
          </SelectTrigger>
          <SelectContent>
            {STATUSES.map((s) => <SelectItem key={s} value={s} className="capitalize">{s}</SelectItem>)}
          </SelectContent>
        </Select>
        <Select value={sort} onValueChange={setSort}>
          <SelectTrigger className="h-10 w-[160px] rounded-xl border-line bg-card text-[13px]">
            <SelectValue />
          </SelectTrigger>
          <SelectContent>
            <SelectItem value="recent">Most recent</SelectItem>
            <SelectItem value="potential">Highest potential</SelectItem>
          </SelectContent>
        </Select>
      </div>

      {filtered.length === 0 ? (
        <div className="mt-10"><EmptyState icon={BookOpen} title="No stories match." description="Try clearing filters, or start a reflection to surface new ones." /></div>
      ) : (
        <motion.div initial={{ opacity: 0, y: 8 }} animate={{ opacity: 1, y: 0 }} transition={{ duration: 0.3 }} className="mt-7 grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
          {filtered.map((s, i) => (
            <motion.div key={s.id} initial={{ opacity: 0, y: 6 }} animate={{ opacity: 1, y: 0 }} transition={{ duration: 0.25, delay: i * 0.03 }}>
              <Link href={`/stories/${s.id}`} className="card-elev group block p-5 transition-shadow hover:shadow-pop">
                <div className="flex items-center justify-between">
                  <Badge variant="outline" className="rounded-full border-line bg-canvas text-[11px] font-normal text-ink-muted">{s.category}</Badge>
                  <span className="text-[11px] text-ink-subtle">{s.potential}% potential</span>
                </div>
                <h3 className="mt-3 font-display text-[17px] font-semibold leading-snug text-ink">{s.title}</h3>
                <p className="mt-1.5 line-clamp-2 text-[13px] text-ink-muted">{s.summary}</p>
                <div className="mt-4 flex items-center justify-between text-[11.5px] text-ink-subtle">
                  <span className="inline-flex items-center gap-1.5"><span className="h-1.5 w-1.5 rounded-full bg-brand" />{s.emotion}</span>
                  <span className="capitalize">{s.status} · {new Date(s.createdAt).toLocaleDateString(undefined, { month: 'short', day: 'numeric' })}</span>
                </div>
              </Link>
            </motion.div>
          ))}
        </motion.div>
      )}
    </div>
  );
}