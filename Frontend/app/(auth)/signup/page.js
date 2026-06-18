'use client';

import Link from 'next/link';
import { useState } from 'react';
import { useRouter } from 'next/navigation';
import { motion } from 'framer-motion';
import { Loader2 } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { useAuth } from '@/providers/auth-provider';
import { toast } from 'sonner';

export default function SignupPage() {
  const router = useRouter();
  const { signUp, signInWith } = useAuth();
  const [loading, setLoading] = useState(null);
  const [form, setForm] = useState({ name: '', email: '', password: '' });

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (!form.email || !form.name) return toast.error('Tell us your name and email');
    setLoading('email');
    try {
      await signUp(form);
      toast.success('Workspace ready');
      router.push('/workspace');
    } finally { setLoading(null); }
  };

  const handleOAuth = async (p) => {
    setLoading(p);
    try { await signInWith(p); router.push('/workspace'); } finally { setLoading(null); }
  };

  return (
    <motion.div initial={{ opacity: 0, y: 8 }} animate={{ opacity: 1, y: 0 }} transition={{ duration: 0.35 }} className="card-elev p-8">
      <h1 className="font-display text-[26px] font-semibold tracking-tight text-ink">Create your workspace</h1>
      <p className="mt-1.5 text-[13.5px] text-ink-muted">A quiet place for your stories. Free during beta.</p>

      <div className="mt-6 space-y-2">
        <Button onClick={() => handleOAuth('google')} disabled={loading} variant="outline" className="h-11 w-full justify-center rounded-xl border-line bg-card text-[13.5px] font-medium hover:bg-secondary">
          {loading === 'google' ? <Loader2 className="h-4 w-4 animate-spin" /> : 'Continue with Google'}
        </Button>
        <Button onClick={() => handleOAuth('github')} disabled={loading} variant="outline" className="h-11 w-full justify-center rounded-xl border-line bg-card text-[13.5px] font-medium hover:bg-secondary">
          {loading === 'github' ? <Loader2 className="h-4 w-4 animate-spin" /> : 'Continue with GitHub'}
        </Button>
      </div>

      <div className="my-6 flex items-center gap-3 text-[11.5px] uppercase tracking-wider text-ink-subtle">
        <span className="h-px flex-1 bg-line" /> or with email <span className="h-px flex-1 bg-line" />
      </div>

      <form onSubmit={handleSubmit} className="space-y-3.5">
        <div className="space-y-1.5">
          <Label className="text-[12.5px] font-medium text-ink">Your name</Label>
          <Input value={form.name} onChange={(e) => setForm({ ...form, name: e.target.value })} placeholder="Maya Chen" className="h-11 rounded-xl border-line" />
        </div>
        <div className="space-y-1.5">
          <Label className="text-[12.5px] font-medium text-ink">Email</Label>
          <Input value={form.email} onChange={(e) => setForm({ ...form, email: e.target.value })} type="email" placeholder="you@studio.com" className="h-11 rounded-xl border-line" />
        </div>
        <div className="space-y-1.5">
          <Label className="text-[12.5px] font-medium text-ink">Password</Label>
          <Input value={form.password} onChange={(e) => setForm({ ...form, password: e.target.value })} type="password" placeholder="At least 8 characters" className="h-11 rounded-xl border-line" />
        </div>
        <Button type="submit" disabled={loading} className="h-11 w-full rounded-xl bg-ink text-[13.5px] font-medium text-white hover:bg-ink/90">
          {loading === 'email' ? <Loader2 className="h-4 w-4 animate-spin" /> : 'Create my workspace'}
        </Button>
      </form>

      <p className="mt-6 text-center text-[12.5px] text-ink-muted">
        Already have an account? <Link href="/login" className="font-medium text-ink hover:text-brand">Sign in</Link>
      </p>
    </motion.div>
  );
}