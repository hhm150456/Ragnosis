import type {
  EvaluationCategory,
  EvaluationMetric,
  EvidenceSource,
  ExampleQueryItem,
  QueryOutcomeDatum,
} from '@/types/clinical';

export const EXAMPLE_QUERIES: ExampleQueryItem[] = [
  {
    id: 'aspirin-statin',
    label: 'Aspirin with atorvastatin',
    query: 'Can a 68-year-old on atorvastatin start daily aspirin?',
  },
  {
    id: 'statin-eligibility',
    label: 'Statin eligibility',
    query: 'What evidence supports statin use for primary prevention?',
  },
  {
    id: 'atorvastatin-safety',
    label: 'Atorvastatin safety',
    query: 'What safety warnings apply to atorvastatin?',
  },
  {
    id: 'unsupported-interaction',
    label: 'Unsupported interaction',
    query: 'Does aspirin interact with clopidogrel?',
  },
];

export const EVIDENCE_SOURCES: EvidenceSource[] = [
  {
    id: 'uspstf-aspirin',
    organization: 'USPSTF',
    title: 'Aspirin Use to Prevent Cardiovascular Disease',
    sourceType: 'Preventive Recommendation',
    publicationYear: 2022,
    evidenceGrade: 'C',
    indexed: true,
    topics: ['aspirin', 'cardiovascular disease', 'primary prevention'],
    indexedSections: ['Recommendation', 'Rationale', 'Practice Considerations'],
    referenceNote: 'Indexed recommendation source for aspirin prevention questions.',
    provenanceNote: 'Controlled USPSTF corpus document.',
  },
  {
    id: 'uspstf-statin',
    organization: 'USPSTF',
    title: 'Statin Use for the Primary Prevention of Cardiovascular Disease',
    sourceType: 'Preventive Recommendation',
    publicationYear: 2022,
    evidenceGrade: 'B',
    indexed: true,
    topics: ['statins', 'cardiovascular disease', 'primary prevention'],
    indexedSections: ['Recommendation', 'Rationale', 'Practice Considerations'],
    referenceNote: 'Indexed recommendation source for statin eligibility questions.',
    provenanceNote: 'Controlled USPSTF corpus document.',
  },
  {
    id: 'dailymed-atorvastatin',
    organization: 'DailyMed (FDA)',
    title: 'Atorvastatin Calcium Prescribing Information',
    sourceType: 'Official Drug Label',
    indexed: true,
    topics: ['atorvastatin', 'contraindications', 'warnings', 'drug interactions'],
    indexedSections: ['Contraindications', 'Warnings and Precautions', 'Drug Interactions'],
    referenceNote: 'Indexed official label for atorvastatin safety questions.',
    provenanceNote: 'Controlled DailyMed/FDA label corpus document.',
  },
];

export const EVALUATION_METRICS: EvaluationMetric[] = [
  {
    id: 'decision-accuracy',
    label: 'Decision Accuracy',
    value: 'n/a',
    description: 'Run the evaluation endpoint to calculate this metric.',
  },
  {
    id: 'citation-validity',
    label: 'Citation Validity',
    value: 'n/a',
    description: 'Share of claims citing retrieved chunks.',
  },
  {
    id: 'faithfulness',
    label: 'Faithfulness',
    value: 'n/a',
    description: 'Share of claims supported by their cited chunk text.',
  },
  {
    id: 'queries-run',
    label: 'Queries Run',
    value: '0',
    description: 'Evaluation queries executed in the current session.',
  },
];

export const QUERY_OUTCOMES: QueryOutcomeDatum[] = [
  { name: 'Supported', count: 0 },
  { name: 'Correct Refusal', count: 0 },
  { name: 'Incorrect Refusal', count: 0 },
  { name: 'Unsupported Answer', count: 0 },
];

export const EVALUATION_CATEGORIES: EvaluationCategory[] = [
  {
    id: 'in-scope',
    title: 'In-scope questions',
    description: 'Questions expected to be answerable from the indexed corpus.',
    examples: EXAMPLE_QUERIES.slice(0, 3).map((item) => item.query),
  },
  {
    id: 'ambiguous',
    title: 'Ambiguous questions',
    description: 'Questions that may retrieve weak or incomplete evidence.',
    examples: ['Does aspirin interact with clopidogrel?'],
  },
  {
    id: 'out-of-domain',
    title: 'Out-of-domain questions',
    description: 'Questions expected to trigger a controlled refusal.',
    examples: ['What is the best treatment for bacterial pneumonia?'],
  },
];
