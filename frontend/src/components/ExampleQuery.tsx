import type { ExampleQueryItem } from '@/types/clinical';

interface ExampleQueryProps {
  examples: ExampleQueryItem[];
  onSelect: (query: string) => void;
  variant?: 'chip' | 'list';
}

export function ExampleQuery({ examples, onSelect, variant = 'chip' }: ExampleQueryProps) {
  if (variant === 'list') {
    return (
      <div className="space-y-2">
        {examples.map((ex, i) => (
          <button
            key={ex.id}
            onClick={() => onSelect(ex.query)}
            className="flex w-full items-start gap-3 rounded-lg border border-slate-700/50 bg-slate-800/40 p-3 text-left transition hover:border-sky-500/30 hover:bg-slate-800/70"
          >
            <span className="flex h-5 w-5 shrink-0 items-center justify-center rounded bg-slate-700 text-[10px] font-semibold text-slate-300">
              {i + 1}
            </span>
            <span className="text-sm text-slate-300">{ex.query}</span>
          </button>
        ))}
      </div>
    );
  }

  return (
    <div className="flex flex-wrap gap-2">
      {examples.map((ex) => (
        <button
          key={ex.id}
          onClick={() => onSelect(ex.query)}
          className="rounded-full border border-slate-700/60 bg-slate-800/40 px-3.5 py-1.5 text-xs font-medium text-slate-300 transition hover:border-sky-500/40 hover:bg-sky-500/10 hover:text-sky-300"
        >
          {ex.label}
        </button>
      ))}
    </div>
  );
}
