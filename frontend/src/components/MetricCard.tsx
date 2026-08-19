import { TrendingUp } from 'lucide-react';

interface MetricCardProps {
  label: string;
  value: string;
  description?: string;
}

export function MetricCard({ label, value, description }: MetricCardProps) {
  return (
    <div className="rounded-xl border border-slate-700/60 bg-slate-800/40 p-5 transition-colors hover:border-slate-600">
      <div className="flex items-center justify-between">
        <span className="text-xs font-medium uppercase tracking-wider text-slate-400">
          {label}
        </span>
        <TrendingUp className="h-4 w-4 text-sky-500/70" />
      </div>
      <div className="mt-3 text-3xl font-semibold text-white">{value}</div>
      {description && (
        <p className="mt-2 text-xs text-slate-500">{description}</p>
      )}
    </div>
  );
}
