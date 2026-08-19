import { Check, X } from 'lucide-react';
import type { EvidenceCoverage } from '@/types/clinical';

interface EvidenceCoverageProps {
  coverage: EvidenceCoverage;
  variant?: 'default' | 'refusal';
}

export function EvidenceCoverage({ coverage, variant = 'default' }: EvidenceCoverageProps) {
  const isRefusal = variant === 'refusal';
  const barColor = isRefusal
    ? coverage.percentage >= 50
      ? 'bg-amber-500'
      : 'bg-red-500'
    : 'bg-sky-500';

  return (
    <div className="rounded-xl border border-slate-700/60 bg-slate-800/40 p-5">
      <h3 className="text-sm font-semibold text-white">Evidence Coverage</h3>

      <div className="mt-4 flex items-center gap-4">
        <div className="relative flex h-16 w-16 shrink-0 items-center justify-center">
          <svg className="h-16 w-16 -rotate-90" viewBox="0 0 36 36">
            <circle
              cx="18"
              cy="18"
              r="15"
              fill="none"
              stroke="currentColor"
              strokeWidth="3"
              className="text-slate-700"
            />
            <circle
              cx="18"
              cy="18"
              r="15"
              fill="none"
              stroke="currentColor"
              strokeWidth="3"
              strokeDasharray={`${(coverage.percentage / 100) * 94.2} 94.2`}
              strokeLinecap="round"
              className={isRefusal ? 'text-amber-400' : 'text-sky-400'}
            />
          </svg>
          <span className="absolute text-sm font-semibold text-white">
            {coverage.percentage}%
          </span>
        </div>

        <div className="flex-1 space-y-2">
          {coverage.items.map((item) => (
            <div key={item.label} className="flex items-start gap-2 text-sm">
              {item.found ? (
                <Check className="mt-0.5 h-4 w-4 shrink-0 text-emerald-400" />
              ) : (
                <X className="mt-0.5 h-4 w-4 shrink-0 text-red-400" />
              )}
              <span className={item.found ? 'text-slate-200' : 'text-slate-400'}>
                {item.label}
                {item.note && (
                  <span className="ml-1 text-xs text-slate-500">— {item.note}</span>
                )}
              </span>
            </div>
          ))}
        </div>
      </div>

      <div className="mt-4 h-1.5 w-full overflow-hidden rounded-full bg-slate-700">
        <div
          className={`h-full rounded-full transition-all duration-700 ${barColor}`}
          style={{ width: `${coverage.percentage}%` }}
        />
      </div>

      <p className="mt-3 text-xs leading-relaxed text-slate-500">{coverage.explanation}</p>
    </div>
  );
}
