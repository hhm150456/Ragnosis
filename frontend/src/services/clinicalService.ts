import { MOCK_RESULTS } from '@/data/mockData';
import type { ClinicalResult } from '@/types/clinical';

// Prototype keyword routing. This mimics the shape of a future
// POST /analyze backend call so the frontend only consumes structured
// ClinicalResult objects. Replace this function with an HTTP call later.

const has = (q: string, terms: string[]) =>
  terms.every((t) => q.includes(t));

export function analyzeQuery(query: string): ClinicalResult {
  const q = query.toLowerCase().trim();

  if (!q) {
    return {
      ...MOCK_RESULTS['generic-refusal'],
      query,
    };
  }

  if (has(q, ['aspirin', 'clopidogrel'])) {
    return { ...MOCK_RESULTS['aspirin-clopidogrel'], query };
  }

  if (has(q, ['aspirin', 'atorvastatin']) || has(q, ['aspirin', '70'])) {
    return { ...MOCK_RESULTS['combined-query'], query };
  }

  if (has(q, ['aspirin']) && (has(q, ['55']) || has(q, ['risk']))) {
    return { ...MOCK_RESULTS['aspirin-supported'], query };
  }

  if (has(q, ['aspirin'])) {
    return { ...MOCK_RESULTS['aspirin-supported'], query };
  }

  if (has(q, ['atorvastatin']) && (has(q, ['interaction']) || has(q, ['contraindication']))) {
    return { ...MOCK_RESULTS['atorvastatin-contraindication'], query };
  }

  if (has(q, ['atorvastatin'])) {
    return { ...MOCK_RESULTS['atorvastatin-contraindication'], query };
  }

  if (has(q, ['metformin'])) {
    return { ...MOCK_RESULTS['metformin'], query };
  }

  return { ...MOCK_RESULTS['generic-refusal'], query };
}

// Simulate an async API call so the UI can show the loading workflow.
export function analyzeQueryAsync(query: string): Promise<ClinicalResult> {
  return new Promise((resolve) => {
    setTimeout(() => resolve(analyzeQuery(query)), 1600);
  });
}
