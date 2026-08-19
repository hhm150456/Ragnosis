import { ShieldAlert } from 'lucide-react';

export type BadgeVariant = 'supported' | 'refused' | 'out_of_scope' | 'error' | 'neutral';

interface StatusBadgeProps {
  variant: BadgeVariant;
  label?: string;
}

const VARIANT_STYLES: Record<BadgeVariant, string> = {
  supported: 'bg-emerald-500/10 text-emerald-300 border-emerald-500/30',
  refused: 'bg-red-500/10 text-red-300 border-red-500/30',
  out_of_scope: 'bg-sky-500/10 text-sky-300 border-sky-500/30',
  error: 'bg-amber-500/10 text-amber-300 border-amber-500/30',
  neutral: 'bg-slate-500/10 text-slate-300 border-slate-500/30',
};

const DEFAULT_LABELS: Record<BadgeVariant, string> = {
  supported: 'Supported by Available Evidence',
  refused: 'Answer Generation Blocked',
  out_of_scope: 'Outside Current Corpus',
  error: 'Error',
  neutral: 'Neutral',
};

export function StatusBadge({ variant, label }: StatusBadgeProps) {
  return (
    <span
      className={`inline-flex items-center gap-2 rounded-full border px-3 py-1 text-xs font-medium ${VARIANT_STYLES[variant]}`}
    >
      {variant === 'refused' && <ShieldAlert className="h-3.5 w-3.5" />}
      {label ?? DEFAULT_LABELS[variant]}
    </span>
  );
}
