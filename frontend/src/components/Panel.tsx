export function Panel({
  title,
  subtitle,
  right,
  children,
}: {
  title: string;
  subtitle?: string;
  right?: React.ReactNode;
  children: React.ReactNode;
}) {
  return (
    <div className="rounded-[28px] border border-white/10 bg-white/5 backdrop-blur p-6 shadow-[0_20px_60px_-30px_rgba(0,0,0,0.8)]">
      <div className="flex items-start justify-between gap-4">
        <div>
          <div className="text-lg font-semibold text-white">{title}</div>
          {subtitle ? <div className="text-sm text-white/60 mt-1">{subtitle}</div> : null}
        </div>
        {right}
      </div>
      <div className="mt-5">{children}</div>
    </div>
  );
}
