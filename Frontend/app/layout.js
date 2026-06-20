import './globals.css';
import 'highlight.js/styles/github.min.css';
import { Inter, Sora } from 'next/font/google';
import { AppProviders } from '@/providers/app-providers';

const inter = Inter({
  subsets: ['latin'],
  variable: '--font-inter',
  display: 'swap',
});

const sora = Sora({
  subsets: ['latin'],
  variable: '--font-sora',
  display: 'swap',
});

export const metadata = {
  title: 'CreatorOS — A creative operating system for storytellers',
  description:
    'CreatorOS helps creators discover, organize and manage stories without losing their voice.',
};

export default function RootLayout({ children }) {
  return (
    <html lang="en" className={`${inter.variable} ${sora.variable}`}>
      <body>
        <AppProviders>{children}</AppProviders>
      </body>
    </html>
  );
}
