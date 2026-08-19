import { useState } from 'react';
import { FileCheck } from 'lucide-react';
import { QueryInput } from '@/components/QueryInput';
import { ExampleQuery } from '@/components/ExampleQuery';
import { EvidenceCard } from '@/components/EvidenceCard';
import { EvidenceCoverage } from '@/components/EvidenceCoverage';
import { RetrievalTrace } from '@/components/RetrievalTrace';
import { RefusalPanel } from '@/components/RefusalPanel';
import { StatusBadge } from '@/components/StatusBadge';
import { Disclaimer } from '@/components/Disclaimer';
import { EXAMPLE_QUERIES } from '@/data/mockData';
import { analyzeQueryAsync } from '@/services/clinicalService';
import type { ClinicalResult, QueryUnderstanding } from '@/types/clinical';

const LOADING_STEPS = [
  'Parse clinical question',
  'Retrieve evidence',
  'Verify sources',
  'Check evidence coverage',
  'Prepare result',
];

export function EvidenceChecker({
  initialQuery,
  onClearInitial,
}: {
  initialQuery?: string;
  onClearInitial?: () => void;
}) {
  const [result, setResult] = useState<ClinicalResult | null>(null);
  const [loading, setLoading] = useState(false);
  const [loadingStep, setLoadingStep] = useState(0);
  const [error, setError] = useState(false);

  const runQuery = async (query: string) => {
    setLoading(true);
    setError(false);
    setResult(null);
    onClearInitial?.();

    // Animate loading steps
    setLoadingStep(0);
    const stepTimer = setInterval(() => {
      setLoadingStep((s) => Math.min(s + 1, LOADING_STEPS.length - 1));
    }, 300);

    try {
      const res = await analyzeQueryAsync(query);
      setResult(res);
    } catch {
      setError(true);
    } finally {
      clearInterval(stepTimer);
      setLoading(false);
    }
  };

  const reset = () => {
    setResult(null);
    setError(false);
  };

  return (
    <div className="space-y-6">
      {/* Header */}
      <div>
        <h1 className="text-2xl font-bold text-white sm:text-3xl">Evidence Checker</h1>
        <p className="mt-1 text-sm text-slate-400">
          Ask a preventive medication question and inspect the evidence behind the result.
        </p>
      </div>

      <QueryInput
        onSubmit={runQuery}
        onReset={reset}
        loading={loading}
        hasResult={!!result || error}
        defaultValue={initialQuery}
      />

      {/* Examples */}
      {!result && !loading && !error && (
        <div>
          <div className="text-xs font-semibold uppercase tracking-wider text-slate-500">
            Try an example
          </div>
          <div className="mt-3">
            <ExampleQuery examples={EXAMPLE_QUERIES} onSelect={runQuery} variant="list" />
          </div>
        </div>
      )}

      {/* Loading */}
      {loading && <LoadingState step={loadingStep} />}

      {/* Error */}
      {error && !loading && (
        <div className="rounded-2xl border border-amber-500/30 bg-amber-500/5 p-6">
          <h2 className="text-lg font-semibold text-amber-200">Unable to analyze this question.</h2>
          <p className="mt-1 text-sm text-slate-300">
            Please try another question within the current evidence scope.
          </p>
          <button
            onClick={reset}
            className="mt-3 rounded-lg border border-slate-700 px-4 py-2 text-sm text-slate-300 hover:text-white"
          >
            Try again
          </button>
        </div>
      )}

      {/* Result */}
      {result && !loading && <ResultView result={result} />}
    </div>
  );
}

function LoadingState({ step }: { step: number }) {
  return (
    <div className="rounded-2xl border border-slate-700/60 bg-slate-800/40 p-6">
      <div className="text-xs font-semibold uppercase tracking-wider text-slate-500">
        Analyzing
      </div>
      <ul className="mt-4 space-y-3">
        {LOADING_STEPS.map((label, i) => {
          const done = i < step;
          const active = i === step;
          return (
            <li key={label} className="flex items-center gap-3 text-sm">
              <span
                className={`flex h-5 w-5 items-center justify-center rounded-full text-[10px] ${
                  done
                    ? 'bg-emerald-500/20 text-emerald-300'
                    : active
                    ? 'bg-sky-500/20 text-sky-300'
                    : 'bg-slate-700 text-slate-500'
                }`}
              >
                {done ? '✓' : active ? '•' : ''}
              </span>
              <span
                className={
                  done
                    ? 'text-slate-300'
                    : active
                    ? 'text-sky-300'
                    : 'text-slate-500'
                }
              >
                {label}
              </span>
              {active && (
                <span className="h-1 w-12 overflow-hidden rounded-full bg-slate-700">
                  <span className="block h-full w-1/2 animate-pulse rounded-full bg-sky-400" />
                </span>
              )}
            </li>
          );
        })}
      </ul>
    </div>
  );
}

function ResultView({ result }: { result: ClinicalResult }) {
  if (result.status === 'refused' || result.status === 'out_of_scope') {
    return (
      <div className="animate-slideUp space-y-6">
        {result.queryUnderstanding && (
          <QueryUnderstandingCard understanding={result.queryUnderstanding} />
        )}
        <RefusalPanel result={result} />
        {result.retrievalTrace && <RetrievalTrace trace={result.retrievalTrace} />}
        <Disclaimer />
      </div>
    );
  }

  return (
    <div className="animate-slideUp space-y-6">
      {/* Query understanding */}
      {result.queryUnderstanding && (
        <QueryUnderstandingCard understanding={result.queryUnderstanding} />
      )}

      {/* Supported header */}
      <div className="rounded-2xl border border-emerald-500/30 bg-emerald-500/5 p-6">
        <div className="flex items-center gap-3">
          <div className="flex h-12 w-12 items-center justify-center rounded-xl bg-emerald-500/10">
            <FileCheck className="h-6 w-6 text-emerald-400" />
          </div>
          <div>
            <h2 className="text-xl font-bold text-emerald-200">Supported by Available Evidence</h2>
            <div className="mt-1">
              <StatusBadge variant="supported" />
            </div>
          </div>
        </div>
      </div>

      {/* Evidence summary */}
      {result.answer && (
        <div className="rounded-xl border border-slate-700/60 bg-slate-800/40 p-5">
          <h3 className="text-sm font-semibold text-white">Evidence Summary</h3>
          <p className="mt-2 text-sm leading-relaxed text-slate-300">{result.answer}</p>
          {result.answerDisclaimer && (
            <p className="mt-3 text-xs italic text-slate-500">{result.answerDisclaimer}</p>
          )}
        </div>
      )}

      {/* Evidence grade + coverage */}
      <div className="grid grid-cols-1 gap-4 sm:grid-cols-3">
        {result.evidenceGrade && (
          <div className="rounded-xl border border-slate-700/60 bg-slate-800/40 p-5">
            <h3 className="text-sm font-semibold text-white">Evidence Grade</h3>
            <div className="mt-3 flex h-20 w-20 items-center justify-center rounded-full border-2 border-sky-500/40 bg-sky-500/10">
              <span className="text-2xl font-bold text-sky-300">{result.evidenceGrade}</span>
            </div>
            <p className="mt-3 text-xs text-slate-500">
              Recommendation grade from the indexed USPSTF source.
            </p>
          </div>
        )}
        {result.coverage && (
          <div className={result.evidenceGrade ? 'sm:col-span-2' : 'sm:col-span-3'}>
            <EvidenceCoverage coverage={result.coverage} />
          </div>
        )}
      </div>

      {/* Multi-source layout */}
      {result.multiSource && (
        <div>
          <h3 className="text-sm font-semibold text-white">Multi-Source Evidence</h3>
          <div className="mt-3 grid grid-cols-1 gap-4 sm:grid-cols-2">
            {result.multiSource.map((src, i) => (
              <div
                key={i}
                className="rounded-xl border border-slate-700/60 bg-slate-800/40 p-4"
              >
                <div className="text-xs font-medium text-sky-400">{src.organization}</div>
                <div className="mt-1 text-sm font-semibold text-white">{src.title}</div>
                <div className="mt-2 text-xs text-slate-400">
                  Source type: {src.sourceType}
                </div>
                {src.section && (
                  <div className="mt-1 text-xs text-slate-400">Section: {src.section}</div>
                )}
                <div className="mt-2 font-mono text-xs text-sky-400">
                  Retrieval score: {src.retrievalScore.toFixed(2)}
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Retrieved evidence */}
      {result.chunks && result.chunks.length > 0 && (
        <div>
          <h3 className="text-lg font-semibold text-white">Retrieved Evidence</h3>
          <div className="mt-3 space-y-3">
            {result.chunks.map((chunk) => (
              <EvidenceCard key={chunk.id} chunk={chunk} />
            ))}
          </div>
        </div>
      )}

      {/* Retrieval trace */}
      {result.retrievalTrace && <RetrievalTrace trace={result.retrievalTrace} />}

      {/* Limitations */}
      {result.limitations && result.limitations.length > 0 && (
        <div className="rounded-xl border border-slate-700/60 bg-slate-800/40 p-5">
          <h3 className="text-sm font-semibold text-white">Evidence Limitations</h3>
          <ul className="mt-2 space-y-1.5">
            {result.limitations.map((l) => (
              <li key={l} className="flex items-start gap-2 text-sm text-slate-400">
                <span className="mt-1.5 h-1 w-1 shrink-0 rounded-full bg-slate-500" />
                {l}
              </li>
            ))}
          </ul>
        </div>
      )}

      <Disclaimer />
    </div>
  );
}

function QueryUnderstandingCard({ understanding }: { understanding: QueryUnderstanding }) {
  return (
    <div className="rounded-xl border border-slate-700/60 bg-slate-800/40 p-5">
      <h3 className="text-sm font-semibold text-white">Query Understanding</h3>
      <div className="mt-3 grid grid-cols-2 gap-3 sm:grid-cols-4">
        {understanding.medication && <Field label="Medication" value={understanding.medication} />}
        {understanding.intent && <Field label="Intent" value={understanding.intent} />}
        {understanding.population && <Field label="Population" value={understanding.population} />}
        {understanding.cvdRisk && <Field label="CVD Risk" value={understanding.cvdRisk} />}
        {understanding.interaction && <Field label="Interaction" value={understanding.interaction} />}
        {understanding.age && <Field label="Age" value={understanding.age} />}
      </div>
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


