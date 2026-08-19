import { ShieldAlert, ChevronDown, Check, X } from 'lucide-react';
import { useState } from 'react';
import type { ClinicalResult } from '@/types/clinical';
import { EvidenceCoverage } from './EvidenceCoverage';

export function RefusalPanel({ result }: { result: ClinicalResult }) {
  const [traceOpen, setTraceOpen] = useState(false);
  const isOutOfScope = result.status === 'out_of_scope';

  return (
    <div
      className={`rounded-2xl border p-6 sm:p-8 ${
        isOutOfScope
          ? 'border-sky-500/30 bg-sky-500/5'
          : 'border-red-500/30 bg-red-500/5'
      }`}
    >
      <div className="flex flex-col items-start gap-4">
        <div
          className={`flex h-14 w-14 items-center justify-center rounded-2xl ${
            isOutOfScope ? 'bg-sky-500/10' : 'bg-red-500/10'
          }`}
        >
          <ShieldAlert
            className={`h-7 w-7 ${isOutOfScope ? 'text-sky-400' : 'text-red-400'}`}
          />
        </div>

        <div>
          <h2
            className={`text-2xl font-bold ${
              isOutOfScope ? 'text-sky-200' : 'text-red-200'
            }`}
          >
            {isOutOfScope ? 'Outside Current Corpus' : 'Insufficient Evidence'}
          </h2>
          <span
            className={`mt-2 inline-block rounded-full border px-3 py-1 text-xs font-semibold ${
              isOutOfScope
                ? 'border-sky-500/30 bg-sky-500/10 text-sky-300'
                : 'border-red-500/30 bg-red-500/10 text-red-300'
            }`}
          >
            ANSWER GENERATION BLOCKED
          </span>
        </div>

        <p className="text-sm leading-relaxed text-slate-300">
          {result.refusalReason}
        </p>
      </div>

      {/* Evidence check */}
      <div className="mt-6 rounded-xl border border-slate-700/50 bg-slate-900/50 p-4">
        <div className="text-xs font-semibold uppercase tracking-wider text-slate-400">
          Evidence Check
        </div>
        <ul className="mt-3 space-y-2">
          {result.foundEvidence?.map((e) => (
            <li key={e} className="flex items-center gap-2 text-sm text-emerald-300">
              <Check className="h-4 w-4" /> {e}
            </li>
          ))}
          {result.missingEvidence?.map((e) => (
            <li key={e} className="flex items-center gap-2 text-sm text-red-300">
              <X className="h-4 w-4" /> {e}
            </li>
          ))}
        </ul>
      </div>

      {/* Coverage visual */}
      {result.coverage && (
        <div className="mt-4">
          <EvidenceCoverage coverage={result.coverage} variant="refusal" />
        </div>
      )}

      {/* Why blocked */}
      <div className="mt-4 rounded-xl border border-slate-700/50 bg-slate-900/50 p-4">
        <div className="text-xs font-semibold uppercase tracking-wider text-slate-400">
          Why was this blocked?
        </div>
        <p className="mt-2 text-sm text-slate-300">{result.refusalReason}</p>
        {result.blockedExplanation && (
          <p className="mt-2 text-sm text-slate-400">{result.blockedExplanation}</p>
        )}
        <div className="mt-3">
          <span
            className={`inline-block rounded-md px-3 py-1 text-xs font-bold ${
              isOutOfScope
                ? 'bg-sky-500/15 text-sky-300'
                : 'bg-red-500/15 text-red-300'
            }`}
          >
            Safety decision: {result.refusalDecision ?? 'BLOCK'}
          </span>
        </div>
      </div>

      {/* Expandable refusal trace */}
      <div className="mt-4 rounded-xl border border-slate-700/60 bg-slate-800/40">
        <button
          onClick={() => setTraceOpen((v) => !v)}
          className="flex w-full items-center justify-between px-5 py-4"
        >
          <span className="text-sm font-semibold text-white">
            Why was this answer blocked?
          </span>
          <ChevronDown
            className={`h-4 w-4 text-slate-400 transition-transform ${
              traceOpen ? 'rotate-180' : ''
            }`}
          />
        </button>
        {traceOpen && (
          <div className="animate-fadeIn border-t border-slate-700/50 px-5 py-4 text-sm">
            <Row label="Query" value={result.query} />
            <div className="mt-3 text-[10px] font-semibold uppercase tracking-wider text-slate-500">
              Required evidence
            </div>
            <ul className="mt-2 space-y-1.5">
              {result.foundEvidence?.map((e) => (
                <li key={e} className="flex items-center gap-2 text-emerald-300">
                  <Check className="h-4 w-4" /> {e}
                </li>
              ))}
              {result.missingEvidence?.map((e) => (
                <li key={e} className="flex items-center gap-2 text-red-300">
                  <X className="h-4 w-4" /> {e}
                </li>
              ))}
            </ul>
            <div className="mt-3 grid grid-cols-2 gap-3">
              <Row label="Decision" value={result.refusalDecision ?? 'REFUSE'} />
              <Row label="Reason" value="Required evidence unavailable." />
            </div>
          </div>
        )}
      </div>
    </div>
  );
}

function Row({ label, value }: { label: string; value: string }) {
  return (
    <div>
      <div className="text-[10px] uppercase tracking-wider text-slate-500">{label}</div>
      <div className="text-slate-200">{value}</div>
    </div>
  );
}
