import { LayoutGrid, Sparkles, BookOpen, CalendarRange, Settings } from 'lucide-react';

export const PRIMARY_NAV = [
  { id: 'workspace', label: 'Workspace', href: '/workspace', icon: LayoutGrid },
  { id: 'reflection', label: 'Reflection', href: '/reflection', icon: Sparkles },
  { id: 'stories', label: 'Story Bank', href: '/stories', icon: BookOpen },
  { id: 'planner', label: 'Planner', href: '/planner', icon: CalendarRange },
  { id: 'settings', label: 'Settings', href: '/settings', icon: Settings },
];
