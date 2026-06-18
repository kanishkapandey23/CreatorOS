import Link from 'next/link';
import { Logo } from '@/components/brand/logo';

export default function AuthLayout({ children }) {
  return (
    <main className="min-h-screen bg-canvas">
      <header className="container flex h-16 items-center justify-between">
        <Logo />
        <Link href="/" className="text-[13px] text-ink-muted hover:text-ink">Back to home</Link>
      </header>
      <div className="container flex min-h-[calc(100vh-4rem)] items-center justify-center pb-16">
        <div className="w-full max-w-[420px]">{children}</div>
      </div>
    </main>
  );
}
