import { Search, FileCheck, ShieldAlert } from 'lucide-react';
import { Disclaimer } from '@/components/Disclaimer';

const PRINCIPLES = [
  {
    n: '01',
    title: 'Retrieve',
    desc: 'Find evidence from a controlled clinical corpus.',
    icon: Search,
  },
  {
    n: '02',
    title: 'Verify',
    desc: 'Check whether retrieved evidence covers the claim required by the question.',
    icon: FileCheck,
  },
  {
    n: '03',
    title: 'Refuse',
    desc: 'Block unsupported claims when evidence is insufficient.',
    icon: ShieldAlert,
  },
];

export function About() {
  return (
    <div className="space-y-8">
      <div>
        <h1 className="text-2xl font-bold text-white sm:text-3xl">About ClinGuard</h1>
        <p className="mt-2 max-w-2xl text-sm leading-relaxed text-slate-300">
          ClinGuard is a research prototype exploring evidence-grounded clinical retrieval and
          controlled refusal.
        </p>
      </div>

      {/* Principles */}
      <div className="grid grid-cols-1 gap-4 sm:grid-cols-3">
        {PRINCIPLES.map((p) => {
          const Icon = p.icon;
          return (
            <div
              key={p.n}
              className="rounded-xl border border-slate-700/60 bg-slate-800/40 p-5"
            >
              <div className="flex h-10 w-10 items-center justify-center rounded-lg bg-sky-500/10 border border-sky-500/20">
                <Icon className="h-5 w-5 text-sky-400" />
              </div>
              <div className="mt-3 font-mono text-xs text-sky-500">{p.n}</div>
              <h3 className="mt-1 text-sm font-semibold text-white">{p.title}</h3>
              <p className="mt-1.5 text-xs leading-relaxed text-slate-400">{p.desc}</p>
            </div>
          );
        })}
      </div>

      {/* Current scope */}
      <div className="grid grid-cols-1 gap-4 sm:grid-cols-3">
        <InfoCard title="Current Scope" items={['Aspirin', 'Statins', 'Atorvastatin']} />
        <InfoCard title="Evidence Sources" items={['USPSTF', 'DailyMed']} />
        <div className="rounded-xl border border-slate-700/60 bg-slate-800/40 p-5">
          <h3 className="text-sm font-semibold text-white">Design Philosophy</h3>
          <p className="mt-2 text-xs leading-relaxed text-slate-400">
            ClinGuard intentionally keeps its evidence corpus narrow to prioritize retrieval
            precision, source traceability, and clinical safety.
          </p>
        </div>
      </div>

      <Disclaimer />
    </div>
  );
}

function InfoCard({ title, items }: { title: string; items: string[] }) {
  return (
    <div className="rounded-xl border border-slate-700/60 bg-slate-800/40 p-5">
      <h3 className="text-sm font-semibold text-white">{title}</h3>
      <ul className="mt-3 space-y-1.5">
        {items.map((it) => (
          <li key={it} className="flex items-center gap-2 text-sm text-slate-300">
            <span className="h-1.5 w-1.5 rounded-full bg-sky-400" />
            {it}
          </li>
        ))}
      </ul>
    </div>
  );
}
