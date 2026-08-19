import { SourceCard } from '@/components/SourceCard';
import { Disclaimer } from '@/components/Disclaimer';
import { EVIDENCE_SOURCES } from '@/data/mockData';

export function Sources() {
  const recommendations = EVIDENCE_SOURCES.filter(
    (s) => s.sourceType === 'Preventive Recommendation'
  );
  const drugLabels = EVIDENCE_SOURCES.filter(
    (s) => s.sourceType === 'Official Drug Label'
  );

  return (
    <div className="space-y-8">
      <div>
        <h1 className="text-2xl font-bold text-white sm:text-3xl">Evidence Sources</h1>
        <p className="mt-1 text-sm text-slate-400">
          ClinGuard uses a controlled corpus of clinical recommendations and official drug-label
          information.
        </p>
      </div>

      <section>
        <h2 className="text-lg font-semibold text-white">Recommendation Corpus</h2>
        <div className="mt-4 grid grid-cols-1 gap-4 lg:grid-cols-2">
          {recommendations.map((s) => (
            <SourceCard key={s.id} source={s} />
          ))}
        </div>
      </section>

      <section>
        <h2 className="text-lg font-semibold text-white">Drug Safety Corpus</h2>
        <div className="mt-4 grid grid-cols-1 gap-4 lg:grid-cols-2">
          {drugLabels.map((s) => (
            <SourceCard key={s.id} source={s} />
          ))}
        </div>
      </section>

      <Disclaimer />
    </div>
  );
}
