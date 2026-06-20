'use client';

import { NotificationBell } from '@/components/layout/notification-panel';
import { Search, SunMedium } from 'lucide-react';
import { useAuth } from '@/providers/auth-provider';
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuLabel,
  DropdownMenuSeparator,
  DropdownMenuTrigger,
} from '@/components/ui/dropdown-menu';
import { Avatar, AvatarFallback } from '@/components/ui/avatar';
import Link from 'next/link';
import { useRouter } from 'next/navigation';

function initials(name) {
  if (!name) return 'CO';
  return name.split(' ').map((p) => p[0]).slice(0, 2).join('').toUpperCase();
}

export function TopNav() {
  const { user, signOut } = useAuth();
  const router = useRouter();

  const handleSignOut = async () => {
    await signOut();
    router.push('/login');
  };

  return (
    <header className="sticky top-0 z-30 flex h-14 items-center gap-3 border-b border-line bg-canvas/80 px-4 backdrop-blur-md md:px-6">
      <div className="flex w-full max-w-xl items-center gap-2 rounded-xl border border-line bg-card px-3 py-1.5 shadow-soft">
        <Search className="h-4 w-4 text-ink-subtle" />
        <input
          className="w-full bg-transparent text-[13.5px] text-ink placeholder:text-ink-subtle focus:outline-none"
          placeholder="Search stories, reflections, drafts…"
        />
        <kbd className="hidden rounded-md border border-line bg-secondary px-1.5 py-0.5 text-[10.5px] text-ink-muted md:inline">
          ⌘K
        </kbd>
      </div>

      <div className="ml-auto flex items-center gap-1">
        <button className="rounded-lg p-2 text-ink-muted hover:bg-secondary hover:text-ink focus-ring" aria-label="Theme">
          <SunMedium className="h-[18px] w-[18px]" />
        </button>
        <NotificationBell />

        <DropdownMenu>
          <DropdownMenuTrigger className="ml-1 inline-flex items-center gap-2 rounded-xl px-1.5 py-1 hover:bg-secondary focus-ring">
            <Avatar className="h-7 w-7">
              <AvatarFallback className="bg-ink text-[11px] font-medium text-white">
                {initials(user?.name || 'CO')}
              </AvatarFallback>
            </Avatar>
            <span className="hidden text-[13px] font-medium text-ink md:inline">
              {user?.name?.split(' ')[0] || 'Sign in'}
            </span>
          </DropdownMenuTrigger>
          <DropdownMenuContent align="end" className="w-56">
            {user ? (
              <>
                <DropdownMenuLabel className="text-ink">
                  <div className="font-medium">{user.name}</div>
                  <div className="text-[11.5px] font-normal text-ink-muted">{user.email}</div>
                </DropdownMenuLabel>
                <DropdownMenuSeparator />
                <DropdownMenuItem asChild><Link href="/settings">Profile & settings</Link></DropdownMenuItem>
                <DropdownMenuItem asChild><Link href="/workspace">Home</Link></DropdownMenuItem>
                <DropdownMenuSeparator />
                <DropdownMenuItem onClick={handleSignOut} className="text-danger focus:text-danger">Sign out</DropdownMenuItem>
              </>
            ) : (
              <>
                <DropdownMenuItem asChild><Link href="/login">Sign in</Link></DropdownMenuItem>
                <DropdownMenuItem asChild><Link href="/signup">Create account</Link></DropdownMenuItem>
              </>
            )}
          </DropdownMenuContent>
        </DropdownMenu>
      </div>
    </header>
  );
}
