import { Sidebar } from '@/components/layout/sidebar';
import { TopNav } from '@/components/layout/topnav';
import { RouteGuard } from '@/components/layout/route-guard';

export default function AppLayout({ children }) {
  return (
    <RouteGuard>
      <div className="flex min-h-screen bg-canvas">
        <Sidebar />
        <div className="flex min-w-0 flex-1 flex-col">
          <TopNav />
          <div className="flex-1">{children}</div>
        </div>
      </div>
    </RouteGuard>
  );
}