import { ChevronDown } from 'lucide-react';
import { useState } from 'react';
import type { RetrievalTrace } from '@/types/clinical';

export function RetrievalTrace({ trace }: { trace: RetrievalTrace }) {
  const [open, setOpen] = useState(false);

  return (
    <div className="rounded-xl border border-slate-700/60 bg-slate-800/40">
      <button
        onClick={() => setOpen((v) => !v)}
        className="flex w-full items-center justify-between px-5 py-4"
      >
        <span className="text-sm font-semibold text-white">Retrieval Trace</span>
        <ChevronDown
          className={`h-4 w-4 text-slate-400 transition-transform ${open ? 'rotate-180' : ''}`}
        />
      </button>

      {open && (
        <div className="animate-fadeIn border-t border-slate-700/50 px-5 py-4">
          <div className="text-[10px] font-semibold uppercase tracking-wider text-slate-500">
            Query decomposition
          </div>
          <div className="mt-2 grid grid-cols-1 gap-2 sm:grid-cols-3">
            {trace.decomposition.medication && (
              <Field label="Medication" value={trace.decomposition.medication} />
            )}
            {trace.decomposition.intent && (
              <Field label="Intent" value={trace.decomposition.intent} />
            )}
            {trace.decomposition.population && (
              <Field label="Population" value={trace.decomposition.population} />
            )}
            {trace.decomposition.interaction && (
              <Field label="Interaction" value={trace.decomposition.interaction} />
            )}
          </div>

          <div className="mt-4 text-[10px] font-semibold uppercase tracking-wider text-slate-500">
            Retrieved chunks
          </div>
          <ol className="mt-2 space-y-2">
            {trace.retrievedChunks.map((chunk, i) => (
              <li
                key={chunk.id}
                className="flex items-center justify-between rounded-lg border border-slate-700/40 bg-slate-900/40 px-3 py-2 text-xs"
              >
                <div className="flex items-center gap-2">
                  <span className="flex h-5 w-5 items-center justify-center rounded bg-slate-700 text-[10px] text-slate-300">
                    {i + 1}
                  </span>
                  <span className="text-slate-200">{chunk.sourceTitle}</span>
                  <span className="text-slate-500">· {chunk.section}</span>
                </div>
                <span className="font-mono text-sky-400">
                  Score: {chunk.score.toFixed(2)}
                </span>
              </li>
            ))}
          </ol>

          <p className="mt-3 text-xs text-slate-500">{trace.note}</p>
        </div>
      )}
    </div>
  );
}

function Field({ label, value }: { label: string; value: string }) {
  return (
    <div className="rounded-lg border border-slate-700/40 bg-slate-900/40 px-3 py-2">
      <div className="text-[10px] uppercase tracking-wider text-slate-500">{label}</div>
      <div className="text-sm text-slate-200">{value}</div>
    </div>
  );
}
