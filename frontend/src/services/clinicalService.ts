import type {
  ClinicalResult,
  EvidenceChunk,
  MultiSourceEntry,
  ResultStatus,
  RetrievalChunkRef,
  SourceType,
  GroundedClaim,
  QueryUnderstanding,
  EvidenceCoverage,
} from '@/types/clinical';

// ---------------------------------------------------------------------------
// Wired to the real backend (backend/api/main.py + routes/query.py).
// Replaces the keyword-routed MOCK_RESULTS prototype.
// ---------------------------------------------------------------------------

const API_BASE_URL =
  (import.meta.env.VITE_API_BASE_URL as string | undefined) ?? '';

// --- Wire-format types, mirroring backend/api/schemas.py exactly ----------
// Keep these in sync with schemas.py by hand; there's no shared codegen yet.

type AnswerStatus = 'answered' | 'partial_refusal' | 'full_refusal' | 'parse_error';

interface CitationOut {
  chunk_id: string;
  document_name: string;
  section_title: string;
  page_numbers: string;
  source_type: string;
}

interface RecommendationOut {
  claim: string;
  excerpt: string;
  evidence_grade: string | null;
  faithfulness_status: 'verified' | 'unverified';
  verification_reason: string | null;
  citation: CitationOut;
}

interface RetrievedChunkOut {
  chunk_id: string;
  collection: string;
  document_name: string;
  section_title: string;
  page_numbers: string;
  text: string;
  semantic_score: number;
  bm25_score: number;
  combined_score: number;
  rerank_score: number | null;
}

interface AnalyzeResponse {
  query: string;
  status: AnswerStatus;
  answer_summary: string;
  refusal_reason: string | null;
  recommendations: RecommendationOut[];
  dropped_claim_count: number;
  retrieved_chunks: RetrievedChunkOut[];
  low_confidence: boolean;
}

interface ApiErrorBody {
  detail?: string;
}

// --- Query request options ---------------------------------------------

export interface AnalyzeOptions {
  /** Chunks to retrieve per collection. Omit to use the backend's default (config.TOP_K_DEFAULT). */
  topK?: number;
  /** Abort the request early, e.g. if the user navigates away or issues a new query. */
  signal?: AbortSignal;
}

// ---------------------------------------------------------------------------
// Collection -> display metadata.
// backend/api/schemas.py doesn't return an `organization` field on chunks or
// citations (only `collection`, e.g. "recommendations" / "safety_labels"),
// so we infer it here from the two fixed collections defined in config.py.
// If a third collection is ever added, this mapping needs to grow with it —
// ideally the backend starts returning organization/source_type directly so
// this guess isn't needed on the frontend at all.
// ---------------------------------------------------------------------------

const COLLECTION_META: Record<string, { organization: string; sourceType: SourceType }> = {
  recommendations: { organization: 'USPSTF', sourceType: 'Preventive Recommendation' },
  safety_labels: { organization: 'DailyMed (FDA)', sourceType: 'Official Drug Label' },
};

function collectionMeta(collection: string) {
  return COLLECTION_META[collection] ?? { organization: collection, sourceType: 'Recommendation' as SourceType };
}

function firstPageNumber(pageNumbers: string): number | undefined {
  const match = pageNumbers.match(/\d+/);
  return match ? Number(match[0]) : undefined;
}

function deriveQueryUnderstanding(query: string): QueryUnderstanding {
  const normalized = query.toLowerCase();
  const medications = ['atorvastatin', 'aspirin', 'statin'].filter((name) =>
    normalized.includes(name),
  );
  const ageMatch = normalized.match(/\b(\d{2,3})[- ]year[- ]old\b/);
  const interaction = normalized.match(/\b(?:with|and|interact(?:ion)? between)\s+([a-z-]+)/)?.[1];

  return {
    medication: medications.length ? medications.join(', ') : undefined,
    intent: normalized.includes('interact') || normalized.includes('safety')
      ? 'Safety / interaction'
      : normalized.includes('eligible') || normalized.includes('prevent') || normalized.includes('start')
        ? 'Preventive medication eligibility'
        : 'Clinical evidence question',
    population: ageMatch ? `${ageMatch[1]}-year-old` : undefined,
    age: ageMatch?.[1],
    interaction,
  };
}

function deriveCoverage(response: AnalyzeResponse): EvidenceCoverage {
  const collections = new Set(response.retrieved_chunks.map((chunk) => chunk.collection));
  const citedChunkIds = new Set(response.recommendations.map((recommendation) => recommendation.citation.chunk_id));
  const hasRetrievedEvidence = response.retrieved_chunks.length > 0;
  const hasCitedEvidence = citedChunkIds.size > 0;
  const hasVerifiedClaims =
    response.recommendations.length > 0 &&
    response.recommendations.every(
      (recommendation) => recommendation.faithfulness_status === 'verified',
    );
  const items = [
    {
      label: 'Relevant source material retrieved',
      found: hasRetrievedEvidence,
      note: hasRetrievedEvidence ? `${response.retrieved_chunks.length} chunk(s)` : 'No chunks returned',
    },
    {
      label: 'Evidence cited in the result',
      found: hasCitedEvidence,
      note: hasCitedEvidence ? `${citedChunkIds.size} citation(s)` : 'No grounded claims',
    },
    {
      label: 'Claims verified against cited text',
      found: hasVerifiedClaims,
      note:
        response.recommendations.length === 0
          ? 'No claims generated'
          : hasVerifiedClaims
            ? 'All claims verified'
            : 'One or more claims failed verification',
    },
    {
      label: 'Recommendation corpus searched',
      found: collections.has('recommendations'),
    },
    {
      label: 'Drug-label corpus searched',
      found: collections.has('safety_labels'),
    },
  ];

  const percentage = Math.round((items.filter((item) => item.found).length / items.length) * 100);
  return {
    percentage,
    items,
    explanation: response.low_confidence
      ? 'Coverage is shown for transparency, but confidence was too low to generate an answer.'
      : response.status === 'partial_refusal' || response.status === 'full_refusal'
        ? 'Retrieved evidence was available, but the final answer was blocked or partially refused because claim support was incomplete.'
        : 'Coverage reflects both the evidence returned and the claims verified against cited text.',
  };
}

function mapStatus(status: AnswerStatus): ResultStatus {
  switch (status) {
    case 'answered':
      return 'supported';
    case 'partial_refusal':
    case 'full_refusal':
      return 'refused';
    case 'parse_error':
      return 'error';
    default:
      return 'error';
  }
}

function mapChunks(response: AnalyzeResponse): EvidenceChunk[] {
  const citedChunkIds = new Set(response.recommendations.map((r) => r.citation.chunk_id));

  return response.retrieved_chunks.map((chunk): EvidenceChunk => {
    const meta = collectionMeta(chunk.collection);
    return {
      id: chunk.chunk_id,
      sourceId: chunk.document_name,
      sourceTitle: chunk.document_name,
      organization: meta.organization,
      sourceType: meta.sourceType,
      section: chunk.section_title,
      page: firstPageNumber(chunk.page_numbers),
      // Only recommendations carry an evidence grade in the current API;
      // retrieved-but-uncited chunks don't have one.
      evidenceGrade: undefined,
      retrievalScore: chunk.rerank_score ?? chunk.combined_score,
      // Heuristic: a chunk actually cited in a recommendation is "relevant";
      // everything else retrieved is "partial" until the backend exposes a
      // real per-chunk relevance verdict.
      status: citedChunkIds.has(chunk.chunk_id) ? 'relevant' : 'partial',
      excerpt: chunk.text,
      excerptIsMock: false,
    };
  });
}

function mapMultiSource(response: AnalyzeResponse): MultiSourceEntry[] {
  const byDocument = new Map<string, MultiSourceEntry>();

  for (const chunk of response.retrieved_chunks) {
    const meta = collectionMeta(chunk.collection);
    const existing = byDocument.get(chunk.document_name);
    const score = chunk.rerank_score ?? chunk.combined_score;

    if (!existing || score > existing.retrievalScore) {
      byDocument.set(chunk.document_name, {
        organization: meta.organization,
        title: chunk.document_name,
        sourceType: meta.sourceType,
        section: chunk.section_title,
        retrievalScore: score,
      });
    }
  }

  return Array.from(byDocument.values());
}

function mapAnalyzeResponse(response: AnalyzeResponse): ClinicalResult {
  const status = mapStatus(response.status);
  const chunks = mapChunks(response);
  const retrievedChunkRefs: RetrievalChunkRef[] = response.retrieved_chunks.map((c) => ({
    id: c.chunk_id,
    sourceTitle: c.document_name,
    section: c.section_title,
    score: c.rerank_score ?? c.combined_score,
  }));

  const firstEvidenceGrade = response.recommendations.find((r) => r.evidence_grade)?.evidence_grade;
  const claims: GroundedClaim[] = response.recommendations.map((recommendation) => ({
    claim: recommendation.claim,
    excerpt: recommendation.excerpt,
    faithfulnessStatus: recommendation.faithfulness_status,
    verificationReason: recommendation.verification_reason ?? undefined,
  }));

  return {
    id: crypto.randomUUID(),
    query: response.query,
    status,
    // The backend doesn't currently decompose the query (medication/intent/
    // population/etc.) — that lived only in the mock data. Leave undefined
    // rather than fabricate it; wire this up if/when the backend returns it.
    queryUnderstanding: deriveQueryUnderstanding(response.query),
    answer: response.answer_summary || undefined,
    claims,
    answerDisclaimer:
      response.recommendations.some(
        (recommendation) => recommendation.faithfulness_status === 'unverified',
      )
        ? 'One or more claims could not be verified against the cited source text.'
        : response.dropped_claim_count > 0
          ? `${response.dropped_claim_count} claim(s) were dropped for insufficient grounding.`
          : undefined,
    evidenceGrade: firstEvidenceGrade ?? undefined,
    coverage: deriveCoverage(response),
    chunks,
    retrievalTrace: {
      decomposition: {},
      retrievedChunks: retrievedChunkRefs,
      note:
        response.low_confidence
          ? 'Retrieval confidence was too low to attempt generation; showing retrieved chunks only.'
          : 'Chunks retrieved by hybrid (BM25 + semantic) search across both collections.',
    },
    multiSource: mapMultiSource(response),
    refusalReason: response.refusal_reason ?? undefined,
    refusalDecision: undefined,
    missingEvidence: response.low_confidence ? ['Sufficient retrieval confidence'] : undefined,
    foundEvidence: response.retrieved_chunks.length
      ? [`${response.retrieved_chunks.length} evidence chunk(s) retrieved`]
      : undefined,
    limitations: [
      'Query understanding is inferred from the submitted wording; it is not a clinical diagnosis.',
      'Evidence grade is only shown when the cited backend recommendation includes one.',
      ...(response.dropped_claim_count > 0
        ? [`${response.dropped_claim_count} claim(s) were removed during grounding validation.`]
        : []),
    ],
    blockedExplanation:
      response.status === 'full_refusal' ? response.refusal_reason ?? undefined : undefined,
  };
}

function errorResult(query: string, message: string): ClinicalResult {
  return {
    id: crypto.randomUUID(),
    query,
    status: 'error',
    refusalReason: message,
    blockedExplanation: message,
  };
}

// ---------------------------------------------------------------------------
// Public API
// ---------------------------------------------------------------------------

/**
 * Calls POST /api/query and maps the response into a ClinicalResult.
 * Never throws — network/HTTP failures resolve to a ClinicalResult with
 * status "error" so the UI can render it like any other result card.
 */
export async function analyzeQuery(query: string, options: AnalyzeOptions = {}): Promise<ClinicalResult> {
  const trimmed = query.trim();
  if (!trimmed) {
    return errorResult(query, 'Enter a question before submitting.');
  }

  let res: Response;
  try {
    res = await fetch(`${API_BASE_URL}/api/query`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ query: trimmed, top_k: options.topK ?? null }),
      signal: options.signal,
    });
  } catch (err) {
    if (err instanceof DOMException && err.name === 'AbortError') {
      throw err; // let callers handle cancellation, don't render it as an error card
    }
    return errorResult(trimmed, `Could not reach the backend at ${API_BASE_URL}. Is it running?`);
  }

  if (!res.ok) {
    let detail = `Request failed with status ${res.status}.`;
    try {
      const body = (await res.json()) as ApiErrorBody;
      if (body.detail) detail = body.detail;
    } catch {
      // response wasn't JSON; keep the generic message
    }
    return errorResult(trimmed, detail);
  }

  const data = (await res.json()) as AnalyzeResponse;
  return mapAnalyzeResponse(data);
}

/**
 * @deprecated Use `analyzeQuery` directly — it's already async and hits the
 * real backend now. Kept as an alias so existing callers don't break while
 * the rest of the frontend is migrated off the mock-data flow.
 */
export const analyzeQueryAsync = analyzeQuery;
