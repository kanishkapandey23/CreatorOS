'use client';

import Link from 'next/link';
import { useState } from 'react';
import { useRouter } from 'next/navigation';
import { motion } from 'framer-motion';
import { Mail, Loader2 } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Checkbox } from '@/components/ui/checkbox';
import { useAuth } from '@/providers/auth-provider';
import { toast } from 'sonner';

function GoogleIcon() {
  return (
    <svg viewBox="0 0 24 24" className="h-4 w-4"><path fill="#EA4335" d="M12 10.2v3.9h5.5c-.24 1.4-1.7 4.1-5.5 4.1-3.3 0-6-2.7-6-6.2s2.7-6.2 6-6.2c1.9 0 3.2.8 3.9 1.5l2.7-2.6C16.9 3.1 14.7 2 12 2 6.9 2 2.8 6.1 2.8 11.2c0 5 4.1 9.2 9.2 9.2 5.3 0 8.8-3.7 8.8-9 0-.6-.1-1.1-.2-1.7H12z"/></svg>
  );
}
function GitHubIcon() {
  return (
    <svg viewBox="0 0 24 24" className="h-4 w-4" fill="currentColor"><path d="M12 .5a12 12 0 0 0-3.8 23.4c.6.1.8-.3.8-.6v-2.1c-3.3.7-4-1.6-4-1.6-.5-1.3-1.3-1.7-1.3-1.7-1.1-.7.1-.7.1-.7 1.2.1 1.8 1.2 1.8 1.2 1.1 1.8 2.8 1.3 3.5 1 .1-.8.4-1.3.8-1.6-2.7-.3-5.5-1.3-5.5-6 0-1.3.5-2.4 1.2-3.2-.1-.3-.5-1.5.1-3.2 0 0 1-.3 3.3 1.2a11.5 11.5 0 0 1 6 0c2.3-1.5 3.3-1.2 3.3-1.2.6 1.7.2 2.9.1 3.2.8.8 1.2 1.9 1.2 3.2 0 4.7-2.8 5.7-5.5 6 .4.4.8 1.1.8 2.3v3.4c0 .3.2.7.8.6A12 12 0 0 0 12 .5z"/></svg>
  );
}

export default function LoginPage() {
  const router = useRouter();
  const { signIn, signInWith } = useAuth();
  const [loading, setLoading] = useState(null);
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');

  const handleEmail = async (e) => {
    e.preventDefault();
    if (!email) return toast.error('Enter your email to continue');
    setLoading('email');
    try {
      await signIn({ email, password });
      toast.success('Welcome back');
      router.push('/workspace');
    } finally {
      setLoading(null);
    }
  };

  const handleOAuth = async (provider) => {
    setLoading(provider);
    try {
      await signInWith(provider);
      router.push('/workspace');
    } finally {
      setLoading(null);
    }
  };

  return (
    <motion.div
      initial={{ opacity: 0, y: 8 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.35 }}
      className="card-elev p-8"
    >
      <h1 className="font-display text-[26px] font-semibold tracking-tight text-ink">Welcome back</h1>
      <p className="mt-1.5 text-[13.5px] text-ink-muted">Sign in to your CreatorOS workspace.</p>

      <div className="mt-6 space-y-2">
        <Button onClick={() => handleOAuth('google')} disabled={loading} variant="outline" className="h-11 w-full justify-center gap-2.5 rounded-xl border-line bg-card text-[13.5px] font-medium hover:bg-secondary">
          {loading === 'google' ? <Loader2 className="h-4 w-4 animate-spin" /> : <GoogleIcon />} Continue with Google
        </Button>
        <Button onClick={() => handleOAuth('github')} disabled={loading} variant="outline" className="h-11 w-full justify-center gap-2.5 rounded-xl border-line bg-card text-[13.5px] font-medium hover:bg-secondary">
          {loading === 'github' ? <Loader2 className="h-4 w-4 animate-spin" /> : <GitHubIcon />} Continue with GitHub
        </Button>
      </div>

      <div className="my-6 flex items-center gap-3 text-[11.5px] uppercase tracking-wider text-ink-subtle">
        <span className="h-px flex-1 bg-line" /> or with email <span className="h-px flex-1 bg-line" />
      </div>

      <form onSubmit={handleEmail} className="space-y-3.5">
        <div className="space-y-1.5">
          <Label className="text-[12.5px] font-medium text-ink">Email</Label>
          <Input value={email} onChange={(e) => setEmail(e.target.value)} type="email" placeholder="you@studio.com" className="h-11 rounded-xl border-line" />
        </div>
        <div className="space-y-1.5">
          <div className="flex items-center justify-between">
            <Label className="text-[12.5px] font-medium text-ink">Password</Label>
            <Link href="/forgot-password" className="text-[12px] text-ink-muted hover:text-ink">Forgot password?</Link>
          </div>
          <Input value={password} onChange={(e) => setPassword(e.target.value)} type="password" placeholder="••••••••" className="h-11 rounded-xl border-line" />
        </div>
        <label className="flex cursor-pointer items-center gap-2 pt-1 text-[12.5px] text-ink-muted">
          <Checkbox className="data-[state=checked]:bg-ink data-[state=checked]:border-ink" /> Remember me on this device
        </label>
        <Button type="submit" disabled={loading} className="h-11 w-full rounded-xl bg-ink text-[13.5px] font-medium text-white hover:bg-ink/90">
          {loading === 'email' ? <Loader2 className="h-4 w-4 animate-spin" /> : <><Mail className="mr-2 h-4 w-4" /> Continue with email</>}
        </Button>
      </form>

      <p className="mt-6 text-center text-[12.5px] text-ink-muted">
        New to CreatorOS? <Link href="/signup" className="font-medium text-ink hover:text-brand">Create an account</Link>
      </p>
    </motion.div>
  );
}