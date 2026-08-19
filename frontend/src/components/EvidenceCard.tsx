import { ChevronDown } from 'lucide-react';
import { useState } from 'react';
import type { EvidenceChunk } from '@/types/clinical';

interface EvidenceCardProps {
  chunk: EvidenceChunk;
}

const STATUS_STYLES = {
  relevant: 'text-emerald-300 bg-emerald-500/10 border-emerald-500/20',
  partial: 'text-amber-300 bg-amber-500/10 border-amber-500/20',
  not_relevant: 'text-slate-400 bg-slate-500/10 border-slate-500/20',
} as const;

const STATUS_LABELS = {
  relevant: 'Relevant',
  partial: 'Partial',
  not_relevant: 'Not Relevant',
} as const;

export function EvidenceCard({ chunk }: EvidenceCardProps) {
  const [expanded, setExpanded] = useState(false);

  return (
    <div className="rounded-xl border border-slate-700/60 bg-slate-800/40 p-4 transition-colors hover:border-slate-600">
      <div className="flex flex-wrap items-start justify-between gap-3">
        <div className="min-w-0">
          <div className="text-xs font-medium text-sky-400">
            {chunk.organization}
          </div>
          <div className="mt-0.5 text-sm font-semibold text-white">
            {chunk.sourceTitle}
          </div>
        </div>
        <span
          className={`inline-flex items-center gap-1.5 rounded-full border px-2.5 py-0.5 text-[10px] font-medium ${
            STATUS_STYLES[chunk.status]
          }`}
        >
          {chunk.status === 'relevant' ? '✓' : chunk.status === 'partial' ? '≈' : '✗'}
          {STATUS_LABELS[chunk.status]}
        </span>
      </div>

      <div className="mt-3 grid grid-cols-2 gap-x-4 gap-y-2 text-xs sm:grid-cols-4">
        <Meta label="Source type" value={chunk.sourceType} />
        <Meta label="Section" value={chunk.section} />
        {chunk.page != null && <Meta label="Page" value={String(chunk.page)} />}
        {chunk.evidenceGrade && <Meta label="Evidence grade" value={chunk.evidenceGrade} />}
        <Meta
          label="Retrieval score"
          value={chunk.retrievalScore.toFixed(2)}
          mono
        />
      </div>

      <button
        onClick={() => setExpanded((v) => !v)}
        className="mt-3 inline-flex items-center gap-1.5 text-xs font-medium text-sky-400 hover:text-sky-300"
      >
        <ChevronDown
          className={`h-3.5 w-3.5 transition-transform ${expanded ? 'rotate-180' : ''}`}
        />
        {expanded ? 'Hide Evidence' : 'View Evidence'}
      </button>

      {expanded && (
        <div className="mt-3 animate-fadeIn rounded-lg border border-slate-700/50 bg-slate-900/60 p-3">
          <div className="text-[10px] font-semibold uppercase tracking-wider text-slate-500">
            Source Excerpt
          </div>
          <p className="mt-2 text-sm leading-relaxed text-slate-300">
            {chunk.excerpt}
          </p>
          {chunk.excerptIsMock && (
            <p className="mt-2 text-[10px] italic text-slate-500">
              Mock source excerpt for prototype demonstration.
            </p>
          )}
        </div>
      )}
    </div>
  );
}

function Meta({ label, value, mono }: { label: string; value: string; mono?: boolean }) {
  return (
    <div>
      <div className="text-[10px] uppercase tracking-wider text-slate-500">{label}</div>
      <div className={`text-slate-200 ${mono ? 'font-mono' : ''}`}>{value}</div>
    </div>
  );
}
