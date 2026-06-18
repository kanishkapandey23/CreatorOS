'use client';

import { useAuth } from '@/providers/auth-provider';
import { useRouter } from 'next/navigation';
import { useEffect } from 'react';
import { Loader2 } from 'lucide-react';

export function RouteGuard({ children }) {
  const { status } = useAuth();
  const router = useRouter();

  useEffect(() => {
    if (status === 'unauthenticated') {
      router.replace('/login');
    }
  }, [status, router]);

  if (status === 'loading') {
    return (
      <div className="flex h-screen w-full items-center justify-center bg-canvas">
        <div className="flex items-center gap-3 text-ink-muted">
          <Loader2 className="h-4 w-4 animate-spin" />
          <span className="text-[13px]">Opening your workspace…</span>
        </div>
      </div>
    );
  }

  if (status === 'unauthenticated') return null;
  return children;
}