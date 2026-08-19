import {
  BarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
  Cell,
} from 'recharts';
import { MetricCard } from '@/components/MetricCard';
import { Disclaimer } from '@/components/Disclaimer';
import {
  EVALUATION_METRICS,
  QUERY_OUTCOMES,
  EVALUATION_CATEGORIES,
} from '@/data/mockData';

const BAR_COLORS: Record<string, string> = {
  Supported: '#0ea5e9',
  'Correct Refusal': '#10b981',
  'Incorrect Refusal': '#f59e0b',
  'Unsupported Answer': '#ef4444',
};

export function Evaluation() {
  return (
    <div className="space-y-8">
      <div>
        <span className="text-xs font-semibold uppercase tracking-[0.2em] text-sky-400">
          Prototype Evaluation
        </span>
        <h1 className="mt-2 text-2xl font-bold text-white sm:text-3xl">System Evaluation</h1>
        <p className="mt-1 text-sm text-slate-400">
          Measure retrieval quality, grounding, and controlled refusal.
        </p>
      </div>

      {/* Metric cards */}
      <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-4">
        {EVALUATION_METRICS.map((m) => (
          <MetricCard key={m.id} label={m.label} value={m.value} description={m.description} />
        ))}
      </div>
      <p className="text-xs italic text-slate-500">
        Demonstration values only. Replace with measured evaluation results before final
        presentation.
      </p>

      {/* Chart */}
      <div className="rounded-xl border border-slate-700/60 bg-slate-800/40 p-6">
        <h2 className="text-sm font-semibold text-white">Query Outcomes</h2>
        <div className="mt-6 h-72 w-full">
          <ResponsiveContainer width="100%" height="100%">
            <BarChart data={QUERY_OUTCOMES} margin={{ top: 10, right: 10, left: -20, bottom: 0 }}>
              <CartesianGrid strokeDasharray="3 3" stroke="#1e293b" vertical={false} />
              <XAxis
                dataKey="name"
                tick={{ fill: '#94a3b8', fontSize: 12 }}
                axisLine={{ stroke: '#334155' }}
              />
              <YAxis tick={{ fill: '#94a3b8', fontSize: 12 }} axisLine={{ stroke: '#334155' }} />
              <Tooltip
                cursor={{ fill: '#1e293b50' }}
                contentStyle={{
                  background: '#0f172a',
                  border: '1px solid #334155',
                  borderRadius: 8,
                  color: '#e2e8f0',
                  fontSize: 12,
                }}
              />
              <Bar dataKey="count" radius={[6, 6, 0, 0]}>
                {QUERY_OUTCOMES.map((entry) => (
                  <Cell key={entry.name} fill={BAR_COLORS[entry.name] ?? '#0ea5e9'} />
                ))}
              </Bar>
            </BarChart>
          </ResponsiveContainer>
        </div>
      </div>

      {/* Categories */}
      <div className="grid grid-cols-1 gap-4 lg:grid-cols-3">
        {EVALUATION_CATEGORIES.map((cat) => (
          <div key={cat.id} className="rounded-xl border border-slate-700/60 bg-slate-800/40 p-5">
            <h3 className="text-sm font-semibold text-white">{cat.title}</h3>
            <p className="mt-1.5 text-xs text-slate-400">{cat.description}</p>
            <ul className="mt-3 space-y-1.5">
              {cat.examples.map((ex) => (
                <li key={ex} className="flex items-center gap-2 text-xs text-slate-300">
                  <span className="h-1 w-1 rounded-full bg-sky-400" />
                  {ex}
                </li>
              ))}
            </ul>
          </div>
        ))}
      </div>

      <Disclaimer />
    </div>
  );
}
