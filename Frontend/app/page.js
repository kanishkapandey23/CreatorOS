import Link from 'next/link';
import { ArrowRight, BookOpen, CalendarRange, Sparkles, LayoutGrid, ChevronRight } from 'lucide-react';
import { Logo } from '@/components/brand/logo';
import { Button } from '@/components/ui/button';
import { Marquee } from '@/components/landing/marquee';

export default function LandingPage() {
  return (
    <main className="min-h-screen bg-canvas">
      {/* Nav */}
      <header className="sticky top-0 z-30 border-b border-line/70 bg-canvas/80 backdrop-blur-md">
        <div className="flex h-16 items-center justify-between px-4 md:px-6 lg:px-8 max-w-7xl mx-auto">
          <Logo />
          <nav className="hidden items-center gap-7 text-[13.5px] text-ink-muted md:flex">
            <Link href="#features" className="hover:text-ink">Features</Link>
            <Link href="#philosophy" className="hover:text-ink">Philosophy</Link>
            <Link href="#workflow" className="hover:text-ink">Workflow</Link>
            <Link href="/workspace" className="hover:text-ink">Workspace</Link>
          </nav>
          <div className="flex items-center gap-2">
            <Button asChild variant="ghost" className="h-9 rounded-xl text-[13px] font-medium text-ink">
              <Link href="/login">Sign in</Link>
            </Button>
            <Button asChild className="h-9 rounded-xl bg-ink text-[13px] font-medium text-white hover:bg-ink/90">
              <Link href="/signup">Start free<ArrowRight className="ml-1.5 h-3.5 w-3.5" /></Link>
            </Button>
          </div>
        </div>
      </header>

      {/* Hero */}
      <section className="relative overflow-hidden">
        <div className="pointer-events-none absolute inset-0 grain opacity-60" />
        <div className="relative px-4 md:px-6 lg:px-8 py-16 md:py-24 lg:py-32 max-w-7xl mx-auto">
          <div className="mx-auto max-w-3xl text-center">
            <div className="inline-flex items-center gap-2 rounded-full border border-line bg-card px-3 py-1 text-[11.5px] text-ink-muted shadow-soft">
              <span className="h-1.5 w-1.5 rounded-full bg-brand" />
              A creative OS for storytellers — now in private beta
            </div>
            <h1 className="mt-6 font-display text-[36px] md:text-[48px] lg:text-[64px] font-semibold leading-[1.05] tracking-tight text-ink">
              Every creator has<br />
              <span className="italic text-ink">stories</span> to tell.
            </h1>
            <p className="mx-auto mt-6 max-w-xl text-[14px] md:text-[15.5px] lg:text-[17px] leading-relaxed text-ink-muted">
              CreatorOS helps you discover, organize and manage them — without losing your voice.
            </p>
            <div className="mt-9 flex flex-col sm:flex-row items-center justify-center gap-3">
              <Button asChild size="lg" className="h-11 w-full sm:w-auto rounded-xl bg-ink px-5 text-[14px] font-medium text-white hover:bg-ink/90">
                <Link href="/signup">Start free<ArrowRight className="ml-2 h-4 w-4" /></Link>
              </Button>
              <Button asChild size="lg" variant="outline" className="h-11 w-full sm:w-auto rounded-xl border-line bg-card px-5 text-[14px] font-medium text-ink hover:bg-secondary">
                <Link href="/workspace">Explore workspace</Link>
              </Button>
            </div>
            <p className="mt-4 text-[12px] text-ink-subtle">No credit card. No noise. Just a quiet place to think.</p>
          </div>

          {/* Hero illustration — abstract notebook */}
          <div className="relative mx-auto mt-12 md:mt-16 max-w-5xl">
            <div className="absolute -inset-x-10 -top-6 -bottom-6 rounded-[36px] bg-gradient-to-b from-white to-transparent opacity-60 blur-2xl" />
            <div className="card-elev relative overflow-hidden p-2 shadow-pop">
              <div className="flex items-center gap-1.5 px-3 py-2.5">
                <span className="h-2.5 w-2.5 rounded-full bg-line" />
                <span className="h-2.5 w-2.5 rounded-full bg-line" />
                <span className="h-2.5 w-2.5 rounded-full bg-line" />
                <span className="ml-3 text-[11.5px] text-ink-subtle">workspace · maya</span>
              </div>
              <div className="grid grid-cols-12 gap-3 rounded-2xl bg-canvas p-3 md:gap-4 md:p-4">
                <div className="col-span-3 hidden flex-col gap-1.5 rounded-xl border border-line bg-card p-3 text-[12.5px] md:flex">
                  {['Workspace', 'Reflection', 'Story Bank', 'Planner', 'Settings'].map((s, i) => (
                    <div key={s} className={`flex items-center gap-2 rounded-lg px-2 py-1.5 ${i===0 ? 'bg-secondary text-ink' : 'text-ink-muted'}`}>
                      <span className="h-1.5 w-1.5 rounded-full bg-ink-subtle" /> {s}
                    </div>
                  ))}
                </div>
                <div className="col-span-12 grid grid-cols-2 gap-3 md:col-span-9 md:gap-4">
                  <div className="col-span-2 rounded-xl border border-line bg-card p-5">
                    <p className="text-[11.5px] uppercase tracking-wider text-ink-subtle">Continue reflection</p>
                    <p className="mt-2 font-display text-[20px] font-semibold text-ink">What did you change your mind about this week?</p>
                    <div className="mt-4 flex items-center gap-2 text-[12px] text-ink-muted"><span className="h-1 w-24 overflow-hidden rounded-full bg-secondary"><span className="block h-full w-1/2 bg-brand" /></span> 3 of 6</div>
                  </div>
                  {[
                    { t: 'The Tuesday I almost gave up', e: 'Vulnerability' },
                    { t: 'A walk that changed the roadmap', e: 'Clarity' },
                  ].map((s) => (
                    <div key={s.t} className="rounded-xl border border-line bg-card p-4">
                      <p className="text-[11px] uppercase tracking-wider text-ink-subtle">{s.e}</p>
                      <p className="mt-1.5 font-display text-[15px] font-semibold text-ink">{s.t}</p>
                      <p className="mt-1 text-[12.5px] text-ink-muted">Draft · 92 potential</p>
                    </div>
                  ))}
                </div>
              </div>
            </div>
          </div>
        </div>
      </section>

      <Marquee />

      {/* Philosophy */}
      <section id="philosophy" className="px-4 md:px-6 lg:px-8 py-16 md:py-24 lg:py-32">
        <div className="max-w-7xl mx-auto">
          <div className="grid items-start gap-12 md:grid-cols-12">
            <div className="md:col-span-5">
              <p className="text-[11.5px] font-medium uppercase tracking-[0.18em] text-brand">Philosophy</p>
              <h2 className="mt-3 font-display text-[28px] md:text-[34px] lg:text-[40px] font-semibold leading-tight text-ink">
                AI manages content.<br /> You keep your creativity.
              </h2>
            </div>
            <div className="space-y-5 text-[14px] md:text-[15px] lg:text-[15px] leading-relaxed text-ink-muted md:col-span-7">
              <p>CreatorOS is not another AI writer. It will not finish your sentences or impersonate your tone.</p>
              <p>Instead, it sits quietly beside you — helping you notice what's worth saying, organize the stories you already carry, and ship them in your own voice.</p>
              <p>Opening CreatorOS should feel like opening a personal notebook. Not a chat window.</p>
            </div>
          </div>
        </div>
      </section>

      {/* Features */}
      <section id="features" className="border-y border-line bg-card">
        <div className="px-4 md:px-6 lg:px-8 py-16 md:py-24 lg:py-32">
          <div className="max-w-7xl mx-auto">
            <div className="mx-auto max-w-2xl text-center">
              <p className="text-[11.5px] font-medium uppercase tracking-[0.18em] text-brand">A complete OS</p>
              <h2 className="mt-3 font-display text-[28px] md:text-[34px] lg:text-[40px] font-semibold leading-tight text-ink">
                Built around how creators actually think.
              </h2>
            </div>
            <div className="mt-14 grid gap-6 md:grid-cols-2 lg:grid-cols-4">
              {[
                { icon: LayoutGrid, t: 'Workspace', d: 'Your calm home. Continue where you left off — no dashboards, no noise.' },
                { icon: Sparkles, t: 'Reflection', d: 'Guided journaling sessions that quietly surface the stories already in your week.' },
                { icon: BookOpen, t: 'Story Bank', d: 'A library of your moments — sortable, searchable, never lost.' },
                { icon: CalendarRange, t: 'Planner', d: 'A weekly rhythm for shipping in your voice. Built for creators, not calendars.' },
              ].map((f) => (
                <div key={f.t} className="rounded-2xl border border-line bg-canvas p-6 transition-colors hover:bg-card">
                  <div className="inline-flex h-9 w-9 items-center justify-center rounded-xl bg-secondary text-ink">
                    <f.icon className="h-[18px] w-[18px]" />
                  </div>
                  <h3 className="mt-4 font-display text-[18px] font-semibold text-ink">{f.t}</h3>
                  <p className="mt-1.5 text-[13.5px] leading-relaxed text-ink-muted">{f.d}</p>
                </div>
              ))}
            </div>
          </div>
        </div>
      </section>

      {/* CTA */}
      <section className="px-4 md:px-6 lg:px-8 py-16 md:py-24 lg:py-32">
        <div className="max-w-7xl mx-auto">
          <div className="card-elev relative overflow-hidden p-8 md:p-10 lg:p-14">
            <div className="pointer-events-none absolute -right-24 -top-24 h-72 w-72 rounded-full bg-brand-soft blur-3xl" />
            <div className="pointer-events-none absolute -bottom-24 -left-10 h-64 w-64 rounded-full bg-violet-soft blur-3xl" />
            <div className="relative max-w-2xl">
              <h2 className="font-display text-[28px] md:text-[36px] lg:text-[40px] font-semibold leading-tight text-ink">
                A calmer place to be a creator.
              </h2>
              <p className="mt-3 text-[14px] md:text-[15px] lg:text-[15px] leading-relaxed text-ink-muted">
                Stop chasing trends. Start telling the stories only you can tell.
              </p>
              <div className="mt-7 flex flex-col sm:flex-row items-start gap-3">
                <Button asChild size="lg" className="h-11 w-full sm:w-auto rounded-xl bg-ink px-5 text-[14px] text-white hover:bg-ink/90">
                  <Link href="/signup">Create your workspace<ArrowRight className="ml-2 h-4 w-4" /></Link>
                </Button>
                <Link href="/workspace" className="inline-flex items-center text-[13.5px] font-medium text-ink hover:text-brand">
                  Take a tour <ChevronRight className="h-4 w-4" />
                </Link>
              </div>
            </div>
          </div>
        </div>
      </section>

      <footer className="border-t border-line px-4 md:px-6 lg:px-8 py-8 md:py-10">
        <div className="max-w-7xl mx-auto flex flex-col items-center justify-between gap-4 text-[12.5px] text-ink-muted md:flex-row">
          <Logo />
          <p>© {new Date().getFullYear()} CreatorOS · Made for storytellers</p>
          <div className="flex items-center gap-5">
            <Link href="/login" className="hover:text-ink">Sign in</Link>
            <Link href="/signup" className="hover:text-ink">Get started</Link>
          </div>
        </div>
      </footer>
    </main>
  );
}