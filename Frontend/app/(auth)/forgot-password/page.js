'use client';

import Link from 'next/link';
import { useState } from 'react';
import { motion } from 'framer-motion';
import { Loader2, MailCheck } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { authService } from '@/services/auth.service';
import { toast } from 'sonner';

export default function ForgotPasswordPage() {
  const [email, setEmail] = useState('');
  const [loading, setLoading] = useState(false);
  const [sent, setSent] = useState(false);

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (!email) return toast.error('Enter your email');
    setLoading(true);
    try {
      await authService.requestPasswordReset(email);
      setSent(true);
    } finally { setLoading(false); }
  };

  return (
    <motion.div initial={{ opacity: 0, y: 8 }} animate={{ opacity: 1, y: 0 }} transition={{ duration: 0.35 }} className="card-elev p-8">
      {sent ? (
        <div className="text-center">
          <div className="mx-auto inline-flex h-10 w-10 items-center justify-center rounded-xl bg-success-soft text-success">
            <MailCheck className="h-5 w-5" />
          </div>
          <h1 className="mt-4 font-display text-[24px] font-semibold text-ink">Check your inbox</h1>
          <p className="mt-2 text-[13.5px] text-ink-muted">If an account exists for {email}, we just sent a reset link.</p>
          <Link href="/login" className="mt-6 inline-block text-[13px] font-medium text-ink hover:text-brand">Back to sign in</Link>
        </div>
      ) : (
        <>
          <h1 className="font-display text-[26px] font-semibold tracking-tight text-ink">Reset your password</h1>
          <p className="mt-1.5 text-[13.5px] text-ink-muted">We'll send a quiet email with a one-time link.</p>
          <form onSubmit={handleSubmit} className="mt-6 space-y-3.5">
            <div className="space-y-1.5">
              <Label className="text-[12.5px] font-medium text-ink">Email</Label>
              <Input value={email} onChange={(e) => setEmail(e.target.value)} type="email" placeholder="you@studio.com" className="h-11 rounded-xl border-line" />
            </div>
            <Button type="submit" disabled={loading} className="h-11 w-full rounded-xl bg-ink text-[13.5px] font-medium text-white hover:bg-ink/90">
              {loading ? <Loader2 className="h-4 w-4 animate-spin" /> : 'Send reset link'}
            </Button>
          </form>
          <p className="mt-6 text-center text-[12.5px] text-ink-muted">
            Remembered it? <Link href="/login" className="font-medium text-ink hover:text-brand">Sign in</Link>
          </p>
        </>
      )}
    </motion.div>
  );
}