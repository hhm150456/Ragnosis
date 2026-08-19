import { ExternalLink, FileCheck, Calendar, Tag, BookOpen } from 'lucide-react';
import { useState } from 'react';
import type { EvidenceSource } from '@/types/clinical';

interface SourceCardProps {
  source: EvidenceSource;
}

export function SourceCard({ source }: SourceCardProps) {
  const [open, setOpen] = useState(false);

  return (
    <>
      <div className="rounded-xl border border-slate-700/60 bg-slate-800/40 p-5 transition-colors hover:border-slate-600">
        <div className="flex items-start justify-between gap-3">
          <div>
            <div className="text-xs font-medium text-sky-400">{source.organization}</div>
            <h3 className="mt-1 text-base font-semibold text-white">{source.title}</h3>
          </div>
          <span className="rounded-full border border-emerald-500/20 bg-emerald-500/10 px-2.5 py-0.5 text-[10px] font-medium text-emerald-300">
            ✓ Indexed
          </span>
        </div>

        <div className="mt-4 flex flex-wrap gap-2">
          <Pill icon={FileCheck} label={source.sourceType} />
          {source.publicationYear && <Pill icon={Calendar} label={`${source.publicationYear}`} />}
          {source.lastUpdated && <Pill icon={Tag} label={source.lastUpdated} />}
          {source.evidenceGrade && (
            <Pill label={`Grade ${source.evidenceGrade}`} accent />
          )}
        </div>

        {source.topics.length > 0 && (
          <div className="mt-3 flex flex-wrap gap-1.5">
            {source.topics.map((t) => (
              <span
                key={t}
                className="rounded bg-slate-700/40 px-2 py-0.5 text-[10px] text-slate-300"
              >
                {t}
              </span>
            ))}
          </div>
        )}

        <div className="mt-4 flex gap-2">
          <button
            onClick={() => setOpen(true)}
            className="inline-flex items-center gap-1.5 text-xs font-medium text-sky-400 hover:text-sky-300"
          >
            View Source <ExternalLink className="h-3 w-3" />
          </button>
        </div>
      </div>

      {open && <SourceModal source={source} onClose={() => setOpen(false)} />}
    </>
  );
}

function Pill({
  label,
  icon: Icon,
  accent,
}: {
  label: string;
  icon?: typeof FileCheck;
  accent?: boolean;
}) {
  return (
    <span
      className={`inline-flex items-center gap-1 rounded-md border px-2 py-0.5 text-[10px] font-medium ${
        accent
          ? 'border-sky-500/30 bg-sky-500/10 text-sky-300'
          : 'border-slate-700/50 bg-slate-900/40 text-slate-300'
      }`}
    >
      {Icon && <Icon className="h-3 w-3" />}
      {label}
    </span>
  );
}

function SourceModal({ source, onClose }: { source: EvidenceSource; onClose: () => void }) {
  return (
    <div
      className="fixed inset-0 z-50 flex items-center justify-center bg-black/60 p-4 backdrop-blur-sm"
      onClick={onClose}
    >
      <div
        className="max-h-[85vh] w-full max-w-lg overflow-y-auto rounded-2xl border border-slate-700 bg-slate-900 p-6 shadow-2xl"
        onClick={(e) => e.stopPropagation()}
      >
        <div className="flex items-start justify-between">
          <div>
            <div className="text-xs font-medium text-sky-400">{source.organization}</div>
            <h3 className="mt-1 text-lg font-semibold text-white">{source.title}</h3>
          </div>
          <button
            onClick={onClose}
            className="rounded-lg p-1 text-slate-400 hover:bg-slate-800 hover:text-white"
            aria-label="Close"
          >
            ✕
          </button>
        </div>

        <div className="mt-4 grid grid-cols-2 gap-3 text-sm">
          <Detail label="Document" value={source.title} />
          <Detail label="Organization" value={source.organization} />
          <Detail label="Source type" value={source.sourceType} />
          <Detail
            label="Publication date"
            value={source.publicationYear ? String(source.publicationYear) : '—'}
          />
          <Detail label="Last updated" value={source.lastUpdated ?? '—'} />
          <Detail label="Version" value={source.version ?? '—'} />
          {source.evidenceGrade && (
            <Detail label="Evidence grade" value={source.evidenceGrade} />
          )}
          <Detail label="Indexed status" value={source.indexed ? 'Indexed' : 'Not indexed'} />
        </div>

        {source.indexedSections && source.indexedSections.length > 0 && (
          <div className="mt-4">
            <div className="text-[10px] font-semibold uppercase tracking-wider text-slate-500">
              Indexed sections
            </div>
            <ul className="mt-2 space-y-1">
              {source.indexedSections.map((s) => (
                <li key={s} className="flex items-center gap-2 text-sm text-slate-300">
                  <BookOpen className="h-3.5 w-3.5 text-slate-500" /> {s}
                </li>
              ))}
            </ul>
          </div>
        )}

        {source.topics.length > 0 && (
          <div className="mt-4">
            <div className="text-[10px] font-semibold uppercase tracking-wider text-slate-500">
              Topics
            </div>
            <div className="mt-2 flex flex-wrap gap-1.5">
              {source.topics.map((t) => (
                <span
                  key={t}
                  className="rounded bg-slate-700/40 px-2 py-0.5 text-[10px] text-slate-300"
                >
                  {t}
                </span>
              ))}
            </div>
          </div>
        )}

        <div className="mt-5 rounded-lg border border-slate-700/50 bg-slate-800/40 p-3">
          <div className="text-[10px] font-semibold uppercase tracking-wider text-slate-500">
            Provenance note
          </div>
          <p className="mt-1 text-xs text-slate-400">{source.provenanceNote}</p>
        </div>

        <button
          disabled
          className="mt-5 w-full rounded-lg border border-slate-700 bg-slate-800/60 px-4 py-2.5 text-sm text-slate-400"
        >
          {source.referenceNote}
        </button>
      </div>
    </div>
  );
}

function Detail({ label, value }: { label: string; value: string }) {
  return (
    <div className="rounded-lg border border-slate-700/40 bg-slate-800/40 p-3">
      <div className="text-[10px] uppercase tracking-wider text-slate-500">{label}</div>
      <div className="mt-0.5 text-slate-200">{value}</div>
    </div>
  );
}
