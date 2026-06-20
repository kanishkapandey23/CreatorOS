'use client';

import { useEffect } from 'react';
import { useParams, useRouter } from 'next/navigation';

/** Legacy route — redirects to Studio. */
export default function LegacyWorkspacePage() {
  const params = useParams();
  const router = useRouter();

  useEffect(() => {
    router.replace(`/stories/${params.id}/studio`);
  }, [params.id, router]);

  return (
    <div className="flex h-[60vh] items-center justify-center text-[13px] text-ink-muted">
      Redirecting to Studio…
    </div>
  );
}
