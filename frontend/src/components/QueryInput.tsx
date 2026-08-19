import { Search, Loader2, X } from 'lucide-react';
import { useState } from 'react';

interface QueryInputProps {
  onSubmit: (query: string) => void;
  onReset?: () => void;
  loading?: boolean;
  hasResult?: boolean;
  placeholder?: string;
  defaultValue?: string;
}

export function QueryInput({
  onSubmit,
  onReset,
  loading = false,
  hasResult = false,
  placeholder = 'Ask a clinical evidence question...',
  defaultValue = '',
}: QueryInputProps) {
  const [value, setValue] = useState(defaultValue);

  const submit = () => {
    if (!value.trim() || loading) return;
    onSubmit(value.trim());
  };

  const reset = () => {
    setValue('');
    onReset?.();
  };

  return (
    <div className="rounded-2xl border border-slate-700/60 bg-slate-800/40 p-2 shadow-xl">
      <div className="flex flex-col gap-2 sm:flex-row sm:items-center">
        <div className="relative flex-1">
          <Search className="pointer-events-none absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-slate-500" />
          <input
            type="text"
            value={value}
            onChange={(e) => setValue(e.target.value)}
            onKeyDown={(e) => e.key === 'Enter' && submit()}
            placeholder={placeholder}
            className="w-full rounded-xl bg-slate-900/60 py-3.5 pl-10 pr-4 text-sm text-white placeholder-slate-500 outline-none transition focus:ring-2 focus:ring-sky-500/40"
          />
        </div>
        <button
          onClick={submit}
          disabled={loading || !value.trim()}
          className="inline-flex items-center justify-center gap-2 rounded-xl bg-sky-500 px-5 py-3.5 text-sm font-semibold text-white transition hover:bg-sky-400 disabled:cursor-not-allowed disabled:opacity-50"
        >
          {loading ? (
            <>
              <Loader2 className="h-4 w-4 animate-spin" /> Checking...
            </>
          ) : (
            <>Check Evidence →</>
          )}
        </button>
      </div>

      {hasResult && (
        <div className="mt-2 flex justify-end px-2 pb-1">
          <button
            onClick={reset}
            className="inline-flex items-center gap-1.5 text-xs font-medium text-slate-400 hover:text-white"
          >
            <X className="h-3.5 w-3.5" /> New Question
          </button>
        </div>
      )}
    </div>
  );
}
