export function Marquee() {
  const items = ['Workspace', 'Reflection', 'Story Bank', 'Planner', 'Voice', 'Originality'];
  return (
    <div className="overflow-hidden">
      <div className="flex animate-[marquee_30s_linear_infinite] gap-12 whitespace-nowrap py-4 text-[12.5px] uppercase tracking-[0.18em] text-ink-subtle">
        {[...items, ...items, ...items].map((it, i) => (
          <span key={i} className="inline-flex items-center gap-3">
            <span className="h-1.5 w-1.5 rounded-full bg-ink-subtle" />
            {it}
          </span>
        ))}
      </div>
      <style>{`@keyframes marquee { from { transform: translateX(0) } to { transform: translateX(-33.3333%) } }`}</style>
    </div>
  );
}