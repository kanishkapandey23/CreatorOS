'use client';

import { useState } from 'react';
import { useAuth } from '@/providers/auth-provider';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Button } from '@/components/ui/button';
import { Switch } from '@/components/ui/switch';
import { Badge } from '@/components/ui/badge';

export default function SettingsPage() {
  const { user } = useAuth();
  const [name, setName] = useState(user?.name || '');
  const [email, setEmail] = useState(user?.email || '');

  return (
    <div className="mx-auto w-full max-w-4xl px-5 py-10 md:px-8 md:py-12">
      <p className="text-[12px] font-medium uppercase tracking-[0.18em] text-ink-subtle">Settings</p>
      <h1 className="mt-1.5 font-display text-[30px] font-semibold tracking-tight text-ink md:text-[36px]">Make CreatorOS yours</h1>
      <p className="mt-1.5 text-[13.5px] text-ink-muted">Tune the small things. Big things stay simple.</p>

      <Tabs defaultValue="profile" className="mt-8">
        <TabsList className="h-10 rounded-xl border border-line bg-card p-1">
          {['profile', 'account', 'preferences', 'connected', 'ai', 'theme', 'notifications'].map((t) => (
            <TabsTrigger key={t} value={t} className="rounded-lg px-3 text-[12.5px] capitalize data-[state=active]:bg-secondary data-[state=active]:text-ink">
              {t === 'connected' ? 'Connected' : t === 'ai' ? 'AI' : t}
            </TabsTrigger>
          ))}
        </TabsList>

        <TabsContent value="profile" className="mt-6">
          <div className="card-elev p-6">
            <h2 className="font-display text-[18px] font-semibold text-ink">Profile</h2>
            <div className="mt-5 grid gap-5 md:grid-cols-2">
              <div className="space-y-1.5">
                <Label className="text-[12.5px]">Name</Label>
                <Input value={name} onChange={(e) => setName(e.target.value)} className="h-10 rounded-xl border-line" />
              </div>
              <div className="space-y-1.5">
                <Label className="text-[12.5px]">Email</Label>
                <Input value={email} onChange={(e) => setEmail(e.target.value)} className="h-10 rounded-xl border-line" />
              </div>
            </div>
            <Button className="mt-5 h-10 rounded-xl bg-ink px-4 text-[13px] text-white hover:bg-ink/90">Save changes</Button>
          </div>
        </TabsContent>

        <TabsContent value="account" className="mt-6">
          <div className="card-elev p-6">
            <h2 className="font-display text-[18px] font-semibold text-ink">Account</h2>
            <p className="mt-1 text-[13px] text-ink-muted">Manage password, sessions and account deletion.</p>
            <div className="mt-5 space-y-3">
              <Button variant="outline" className="h-10 rounded-xl border-line">Change password</Button>
              <Button variant="outline" className="h-10 rounded-xl border-line">Sign out all devices</Button>
              <Button variant="outline" className="h-10 rounded-xl border-line text-danger hover:bg-danger-soft">Delete account</Button>
            </div>
          </div>
        </TabsContent>

        <TabsContent value="preferences" className="mt-6">
          <div className="card-elev space-y-4 p-6">
            {[
              { l: 'Show daily reflection nudge', d: 'A gentle reminder, never a pop-up.' },
              { l: 'Weekly story digest by email', d: 'A short letter every Sunday.' },
              { l: 'Enable keyboard-first navigation', d: 'For when typing feels better.' },
            ].map((p) => (
              <div key={p.l} className="flex items-center justify-between rounded-xl border border-line p-4">
                <div><p className="text-[13.5px] font-medium text-ink">{p.l}</p><p className="text-[12px] text-ink-muted">{p.d}</p></div>
                <Switch defaultChecked />
              </div>
            ))}
          </div>
        </TabsContent>

        <TabsContent value="connected" className="mt-6">
          <div className="card-elev p-6">
            <h2 className="font-display text-[18px] font-semibold text-ink">Connected platforms</h2>
            <p className="mt-1 text-[13px] text-ink-muted">Publish in your voice, to the places you already are.</p>
            <div className="mt-5 grid gap-3 sm:grid-cols-2">
              {['LinkedIn', 'Instagram', 'X (Twitter)', 'Substack'].map((p) => (
                <div key={p} className="flex items-center justify-between rounded-xl border border-line bg-canvas p-4">
                  <div><p className="text-[13.5px] font-medium text-ink">{p}</p><p className="text-[12px] text-ink-muted">Not connected</p></div>
                  <Badge variant="outline" className="rounded-full border-line text-[11px] text-ink-muted">Coming soon</Badge>
                </div>
              ))}
            </div>
          </div>
        </TabsContent>

        <TabsContent value="ai" className="mt-6">
          <div className="card-elev space-y-4 p-6">
            <h2 className="font-display text-[18px] font-semibold text-ink">AI preferences</h2>
            <p className="text-[13px] text-ink-muted">Tune how much (or how little) CreatorOS suggests.</p>
            {[
              { l: 'Suggest hooks while I write', d: 'Quiet inline ideas, dismissible.' },
              { l: 'Voice mimicry', d: 'Off by default — we never write as you.' },
              { l: 'Surface story potential', d: 'Show a soft potential score on cards.' },
            ].map((p) => (
              <div key={p.l} className="flex items-center justify-between rounded-xl border border-line p-4">
                <div><p className="text-[13.5px] font-medium text-ink">{p.l}</p><p className="text-[12px] text-ink-muted">{p.d}</p></div>
                <Switch defaultChecked={p.l !== 'Voice mimicry'} />
              </div>
            ))}
          </div>
        </TabsContent>

        <TabsContent value="theme" className="mt-6">
          <div className="card-elev p-6">
            <h2 className="font-display text-[18px] font-semibold text-ink">Theme</h2>
            <p className="mt-1 text-[13px] text-ink-muted">Choose a mood for your workspace.</p>
            <div className="mt-5 grid gap-3 sm:grid-cols-3">
              {[{ n: 'Paper', c: '#FAFAF8' }, { n: 'Ivory', c: '#F8F6EF' }, { n: 'Slate', c: '#0F0F12' }].map((t) => (
                <button key={t.n} className="flex items-center gap-3 rounded-xl border border-line bg-card p-4 text-left hover:border-ink-subtle">
                  <span className="h-8 w-8 rounded-lg border border-line" style={{ background: t.c }} />
                  <div><p className="text-[13.5px] font-medium text-ink">{t.n}</p><p className="text-[11.5px] text-ink-subtle">Coming soon</p></div>
                </button>
              ))}
            </div>
          </div>
        </TabsContent>

        <TabsContent value="notifications" className="mt-6">
          <div className="card-elev space-y-4 p-6">
            {[
              { l: 'Reflection reminders', d: 'A nudge twice a week.' },
              { l: 'Story milestones', d: 'When a story crosses a potential threshold.' },
              { l: 'Weekly newsletter', d: 'A small wrap-up, every Sunday.' },
            ].map((p) => (
              <div key={p.l} className="flex items-center justify-between rounded-xl border border-line p-4">
                <div><p className="text-[13.5px] font-medium text-ink">{p.l}</p><p className="text-[12px] text-ink-muted">{p.d}</p></div>
                <Switch defaultChecked />
              </div>
            ))}
          </div>
        </TabsContent>
      </Tabs>
    </div>
  );
}