'use client';

import { useEffect } from 'react';
import { useRouter, useSearchParams } from 'next/navigation';
import { Loader2 } from 'lucide-react';
import { toast } from 'sonner';

const ERROR_MESSAGES = {
  oauth_not_configured:
    'OAuth is not configured on the server. Add Google/GitHub credentials to backend/.env, or sign in with email.',
  oauth_missing_params: 'OAuth sign-in was interrupted. Please try again.',
  oauth_failed: 'OAuth sign-in failed. Please try again or use email sign-in.',
};

export default function AuthCallbackPage() {
  const router = useRouter();
  const searchParams = useSearchParams();

  useEffect(() => {
    const token = searchParams.get('token');
    const error = searchParams.get('error');

    if (error) {
      toast.error(ERROR_MESSAGES[error] || ERROR_MESSAGES.oauth_failed);
      router.replace('/login');
      return;
    }

    if (token) {
      localStorage.setItem('creatoros:token', token);
      window.location.replace('/workspace');
      return;
    }

    router.replace('/login');
  }, [router, searchParams]);

  return (
    <div className="flex min-h-[40vh] items-center justify-center">
      <div className="flex items-center gap-3 text-ink-muted">
        <Loader2 className="h-4 w-4 animate-spin" />
        <span className="text-[13px]">Completing sign-in…</span>
      </div>
    </div>
  );
}
