'use client';

import { useEffect, useRef } from 'react';
import { usePathname, useRouter } from 'next/navigation';
import { getLastWorkspace } from '@/lib/workspace-persistence';

export function WorkspaceRestore() {
  const router = useRouter();
  const pathname = usePathname();
  const restored = useRef(false);

  useEffect(() => {
    if (restored.current) return;
    if (pathname !== '/workspace') return;

    const last = getLastWorkspace();
    if (last?.path) {
      restored.current = true;
      router.replace(last.path);
    }
  }, [pathname, router]);

  return null;
}
