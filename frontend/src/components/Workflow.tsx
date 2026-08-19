import { MessageSquare, FileSearch, FileCheck, ShieldCheck } from 'lucide-react';

const STEPS = [
  {
    n: '01',
    title: 'Clinical Question',
    desc: 'Understand the medication, intent, population, and evidence required.',
    icon: MessageSquare,
  },
  {
    n: '02',
    title: 'Evidence Retrieval',
    desc: 'Retrieve relevant evidence from the controlled clinical corpus.',
    icon: FileSearch,
  },
  {
    n: '03',
    title: 'Source Verification',
    desc: 'Verify source type, section, page, and evidence coverage.',
    icon: FileCheck,
  },
  {
    n: '04',
    title: 'Safe Answer',
    desc: 'Generate only when the available evidence is sufficient.',
    icon: ShieldCheck,
  },
];

export function Workflow() {
  return (
    <div>
      <h2 className="text-center text-xl font-semibold text-white sm:text-2xl">
        From clinical question to evidence-grounded result
      </h2>

      <div className="mt-8 grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-4 lg:gap-0">
        {STEPS.map((step, i) => {
          const Icon = step.icon;
          return (
            <div key={step.n} className="relative flex lg:block">
              <div className="flex-1 rounded-xl border border-slate-700/60 bg-slate-800/40 p-5">
                <div className="flex h-10 w-10 items-center justify-center rounded-lg bg-sky-500/10 border border-sky-500/20">
                  <Icon className="h-5 w-5 text-sky-400" />
                </div>
                <div className="mt-3 text-xs font-mono text-sky-500">{step.n}</div>
                <h3 className="mt-1 text-sm font-semibold text-white">{step.title}</h3>
                <p className="mt-1.5 text-xs leading-relaxed text-slate-400">{step.desc}</p>
              </div>

              {/* Arrow connector — desktop horizontal */}
              {i < STEPS.length - 1 && (
                <div className="hidden lg:flex lg:items-center lg:px-2">
                  <div className="h-px w-6 bg-gradient-to-r from-sky-500/40 to-sky-500/10" />
                </div>
              )}
              {/* Arrow connector — mobile vertical */}
              {i < STEPS.length - 1 && (
                <div className="flex items-center px-3 lg:hidden">
                  <div className="h-8 w-px bg-gradient-to-b from-sky-500/40 to-sky-500/10" />
                </div>
              )}
            </div>
          );
        })}
      </div>
    </div>
  );
}
