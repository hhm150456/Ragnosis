// ClinGuard clinical data structures.
// These types model the structured result objects that a future
// POST /analyze backend would return. The frontend only ever
// consumes these shapes — clinical logic lives in the service layer.

export type ResultStatus = 'supported' | 'refused' | 'out_of_scope' | 'error';

export type SourceType =
  | 'Recommendation'
  | 'Official Drug Label'
  | 'Preventive Recommendation';

export interface EvidenceSource {
  id: string;
  organization: string;
  title: string;
  sourceType: SourceType;
  publicationYear?: number;
  lastUpdated?: string;
  version?: string;
  evidenceGrade?: string;
  indexed: boolean;
  topics: string[];
  indexedSections?: string[];
  referenceNote: string;
  provenanceNote: string;
}

export interface EvidenceChunk {
  id: string;
  sourceId: string;
  sourceTitle: string;
  organization: string;
  sourceType: SourceType;
  section: string;
  page?: number;
  evidenceGrade?: string;
  retrievalScore: number;
  status: 'relevant' | 'partial' | 'not_relevant';
  excerpt: string;
  excerptIsMock: boolean;
}

export interface CoverageItem {
  label: string;
  found: boolean;
  note?: string;
}

export interface EvidenceCoverage {
  percentage: number;
  items: CoverageItem[];
  explanation: string;
}

export interface QueryUnderstanding {
  medication?: string;
  intent?: string;
  population?: string;
  cvdRisk?: string;
  interaction?: string;
  age?: string;
}

export interface RetrievalChunkRef {
  id: string;
  sourceTitle: string;
  section: string;
  score: number;
}

export interface RetrievalTrace {
  decomposition: {
    medication?: string;
    intent?: string;
    population?: string;
    interaction?: string;
  };
  retrievedChunks: RetrievalChunkRef[];
  note: string;
}

export interface MultiSourceEntry {
  organization: string;
  title: string;
  sourceType: SourceType;
  section?: string;
  retrievalScore: number;
}

export interface ClinicalResult {
  id: string;
  query: string;
  status: ResultStatus;
  queryUnderstanding?: QueryUnderstanding;
  answer?: string;
  answerDisclaimer?: string;
  evidenceGrade?: string;
  coverage?: EvidenceCoverage;
  chunks?: EvidenceChunk[];
  retrievalTrace?: RetrievalTrace;
  multiSource?: MultiSourceEntry[];
  refusalReason?: string;
  refusalDecision?: string;
  missingEvidence?: string[];
  foundEvidence?: string[];
  limitations?: string[];
  blockedExplanation?: string;
}

export interface ExampleQueryItem {
  id: string;
  label: string;
  query: string;
}

export interface EvaluationMetric {
  id: string;
  label: string;
  value: string;
  description: string;
}

export interface QueryOutcomeDatum {
  name: string;
  count: number;
}

export interface EvaluationCategory {
  id: string;
  title: string;
  description: string;
  examples: string[];
}
