import { ShieldAlert } from 'lucide-react';

export function Disclaimer() {
  return (
    <div className="flex items-start gap-3 rounded-lg border border-slate-700/60 bg-slate-800/30 px-4 py-3 text-xs text-slate-400">
      <ShieldAlert className="mt-0.5 h-4 w-4 shrink-0 text-slate-500" />
      <p>
        ClinGuard is a research demonstration. It does not provide medical advice,
        diagnosis, or individualized treatment recommendations.
      </p>
    </div>
  );
}
