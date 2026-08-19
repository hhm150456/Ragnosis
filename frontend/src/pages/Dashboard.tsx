import { Search, FileCheck, ShieldAlert, ArrowRight, Check, X } from 'lucide-react';
import { useState } from 'react';
import { QueryInput } from '@/components/QueryInput';
import { ExampleQuery } from '@/components/ExampleQuery';
import { Workflow } from '@/components/Workflow';
import { Disclaimer } from '@/components/Disclaimer';
import { EXAMPLE_QUERIES } from '@/data/mockData';
import type { PageId } from '@/components/Sidebar';

const HERO_EXAMPLES = EXAMPLE_QUERIES.slice(0, 4);

export function Dashboard({ onNavigate }: { onNavigate: (page: PageId) => void }) {
  const [pendingQuery, setPendingQuery] = useState<string | undefined>();

  const handleSubmit = (query: string) => {
    setPendingQuery(query);
    onNavigate('evidence');
  };

  return (
    <div className="space-y-20">
      {/* Hero */}
      <section className="pt-4">
        <div className="text-center">
          <span className="text-xs font-semibold uppercase tracking-[0.2em] text-sky-400">
            Clinical Evidence • Safety • Traceability
          </span>
          <h1 className="mx-auto mt-4 max-w-3xl text-3xl font-bold leading-tight text-white sm:text-5xl">
            Clinical evidence, not clinical guesses.
          </h1>
          <p className="mx-auto mt-4 max-w-2xl text-base text-slate-400">
            ClinGuard retrieves evidence from a controlled clinical corpus, verifies whether
            the available evidence is sufficient, and blocks unsupported clinical claims.
          </p>
        </div>

        <div className="mx-auto mt-8 max-w-3xl">
          <QueryInput
            onSubmit={handleSubmit}
            placeholder="Enter a clinical question..."
          />
          <div className="mt-3 flex flex-col items-center justify-between gap-3 sm:flex-row">
            <p className="text-xs text-slate-500">
              Enter a clinical question → Check evidence → Get a grounded result
            </p>
            <button
              onClick={() => setPendingQuery(EXAMPLE_QUERIES[0].query)}
              className="text-xs font-medium text-sky-400 hover:text-sky-300"
            >
              Try an example →
            </button>
          </div>
        </div>

        {/* Example chips */}
        <div className="mx-auto mt-5 max-w-3xl">
          <ExampleQuery examples={HERO_EXAMPLES} onSelect={handleSubmit} />
        </div>
      </section>

      {/* Workflow */}
      <section>
        <Workflow />
      </section>

      {/* Controlled refusal showcase */}
      <section className="rounded-2xl border border-red-500/20 bg-slate-800/20 p-6 sm:p-10">
        <div className="text-center">
          <h2 className="text-2xl font-bold text-white sm:text-3xl">
            When the evidence isn't enough, ClinGuard stops.
          </h2>
          <p className="mx-auto mt-3 max-w-2xl text-sm text-slate-400">
            ClinGuard does not fill evidence gaps with unsupported medical knowledge. If the
            required evidence cannot be found in the controlled corpus, answer generation is blocked.
          </p>
        </div>

        <div className="mt-8 grid grid-cols-1 gap-4 lg:grid-cols-2">
          {/* User question */}
          <div className="rounded-xl border border-slate-700/60 bg-slate-900/40 p-5">
            <div className="text-[10px] font-semibold uppercase tracking-wider text-slate-500">
              User Question
            </div>
            <p className="mt-2 text-sm text-slate-200">
              "Does aspirin interact with clopidogrel?"
            </p>
          </div>

          {/* ClinGuard response */}
          <div className="rounded-xl border border-red-500/30 bg-red-500/5 p-5">
            <div className="flex items-center gap-2 text-[10px] font-semibold uppercase tracking-wider text-red-400">
              <ShieldAlert className="h-4 w-4" /> ClinGuard
            </div>
            <div className="mt-2 text-sm font-bold text-red-200">
              ⚠ INSUFFICIENT EVIDENCE
            </div>
            <div className="mt-1 text-xs font-semibold text-red-300">
              ANSWER GENERATION BLOCKED
            </div>
            <ul className="mt-4 space-y-1.5 text-xs">
              <li className="flex items-center gap-2 text-emerald-300">
                <Check className="h-3.5 w-3.5" /> Aspirin evidence found
              </li>
              <li className="flex items-center gap-2 text-red-300">
                <X className="h-3.5 w-3.5" /> Aspirin–clopidogrel interaction evidence not found
              </li>
            </ul>
            <p className="mt-3 text-xs text-slate-400">
              Unsupported clinical claim prevented.
            </p>
          </div>
        </div>

        <div className="mt-6 text-center">
          <button
            onClick={() => onNavigate('evidence')}
            className="inline-flex items-center gap-2 rounded-lg border border-red-500/30 bg-red-500/10 px-4 py-2.5 text-sm font-medium text-red-300 transition hover:bg-red-500/20"
          >
            See why this was blocked <ArrowRight className="h-4 w-4" />
          </button>
        </div>
      </section>

      {/* Core capabilities */}
      <section>
        <div className="grid grid-cols-1 gap-4 sm:grid-cols-3">
          <CapabilityCard
            icon={Search}
            title="Evidence Retrieval"
            desc="Find relevant clinical evidence using medication, intent, population, and source metadata."
          />
          <CapabilityCard
            icon={FileCheck}
            title="Source Verification"
            desc="Trace supported results to the document, section, page, and source type."
          />
          <CapabilityCard
            icon={ShieldAlert}
            title="Controlled Refusal"
            desc="Block unsupported clinical claims when required evidence is missing."
          />
        </div>
      </section>

      {/* Why ClinGuard */}
      <section>
        <h2 className="text-center text-xl font-semibold text-white sm:text-2xl">
          Built for evidence boundaries.
        </h2>
        <div className="mx-auto mt-6 max-w-3xl space-y-3">
          <CompareRow
            general="May rely on broader model knowledge."
            clinguard="Uses a controlled evidence corpus."
          />
          <CompareRow
            general="Evidence paths may not always be explicit."
            clinguard="Shows source, section, page, and retrieval trace."
          />
          <CompareRow
            general="May attempt to answer uncertain questions."
            clinguard="Uses controlled refusal when evidence is insufficient."
          />
        </div>
      </section>

      {/* Brand message */}
      <section className="text-center">
        <h2 className="mx-auto max-w-3xl text-2xl font-bold text-white sm:text-3xl">
          ClinGuard doesn't just answer. It checks whether the evidence is sufficient to answer.
        </h2>
      </section>

      {/* Final CTA */}
      <section className="rounded-2xl border border-sky-500/20 bg-sky-500/5 p-8 text-center sm:p-12">
        <h2 className="text-2xl font-bold text-white sm:text-3xl">
          Ready to check the evidence?
        </h2>
        <p className="mt-2 text-sm text-slate-400">
          Controlled corpus • Source traceability • Safety-first refusal
        </p>
        <button
          onClick={() => onNavigate('evidence')}
          className="mt-5 inline-flex items-center gap-2 rounded-xl bg-sky-500 px-6 py-3 text-sm font-semibold text-white transition hover:bg-sky-400"
        >
          Open Evidence Checker <ArrowRight className="h-4 w-4" />
        </button>
      </section>

      {/* Footer */}
      <footer className="pb-4">
        <p className="text-center text-xs text-slate-500">
          ClinGuard is a research demonstration and does not replace professional medical judgment.
        </p>
      </footer>
    </div>
  );
}

function CapabilityCard({
  icon: Icon,
  title,
  desc,
}: {
  icon: typeof Search;
  title: string;
  desc: string;
}) {
  return (
    <div className="rounded-xl border border-slate-700/60 bg-slate-800/40 p-5 transition-colors hover:border-slate-600">
      <div className="flex h-10 w-10 items-center justify-center rounded-lg bg-sky-500/10 border border-sky-500/20">
        <Icon className="h-5 w-5 text-sky-400" />
      </div>
      <h3 className="mt-3 text-sm font-semibold text-white">{title}</h3>
      <p className="mt-1.5 text-xs leading-relaxed text-slate-400">{desc}</p>
    </div>
  );
}

function CompareRow({ general, clinguard }: { general: string; clinguard: string }) {
  return (
    <div className="grid grid-cols-1 gap-3 sm:grid-cols-2">
      <div className="rounded-lg border border-slate-700/40 bg-slate-800/30 p-4">
        <div className="text-[10px] font-semibold uppercase tracking-wider text-slate-500">
          General AI
        </div>
        <p className="mt-1 text-sm text-slate-400">{general}</p>
      </div>
      <div className="rounded-lg border border-sky-500/20 bg-sky-500/5 p-4">
        <div className="text-[10px] font-semibold uppercase tracking-wider text-sky-400">
          ClinGuard
        </div>
        <p className="mt-1 text-sm text-slate-200">{clinguard}</p>
      </div>
    </div>
  );
}
