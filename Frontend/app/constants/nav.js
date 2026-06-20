import { LayoutGrid, Sparkles, BookOpen, CalendarRange, Compass, Settings } from 'lucide-react';

export const PRIMARY_NAV = [
  { id: 'home', label: 'Home', href: '/workspace', icon: LayoutGrid },
  { id: 'reflection', label: 'Reflection', href: '/reflection', icon: Sparkles },
  { id: 'stories', label: 'Story Bank', href: '/stories', icon: BookOpen },
  { id: 'strategy', label: 'Strategist', href: '/strategy', icon: Compass },
  { id: 'planner', label: 'Planner', href: '/planner', icon: CalendarRange },
  { id: 'settings', label: 'Settings', href: '/settings', icon: Settings },
];
