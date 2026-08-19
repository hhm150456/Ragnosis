"""
Day 4 (interim) — minimal retrieval-confidence gate.

The full safety layer planned in this package's README (retrieval
confidence threshold, unsupported-claim/faithfulness check, refusal
template) isn't built yet. This module is just the first, cheapest piece of
that: if the best-scoring retrieved chunk is clearly weak, refuse before
spending a generation call on it at all, rather than letting a low-quality
match get sent to the LLM and hoping it declines gracefully.

This is intentionally conservative and narrow:
- It only ever refuses; it never overrides generation with an answer.
- It only fires when EVERY retrieved chunk is below MIN_CONFIDENCE_THRESHOLD.
  A single strong match is enough to pass the gate and proceed to generation.
- The empty-retrieval case (nothing came back at all) is deliberately left
  alone here — backend.src.generation.generator.generate_answer already
  produces a clean refusal for that, so duplicating it would just be two
  code paths saying the same thing.

The downstream generation layer's own grounding checks
(backend.src.generation.response_parser) still run on anything that clears
this gate — this is a pre-filter, not a replacement for that validation.
"""

from __future__ import annotations

from config import MIN_CONFIDENCE_THRESHOLD


def low_confidence_reason(retrieval_results: dict[str, list]) -> str | None:
    """
    retrieval_results: output of HybridRetriever.retrieve_compound(), keyed
        by collection name.

    Returns a human-readable refusal reason if retrieval confidence is too
    low to proceed to generation, or None if it's fine to continue.
    """
    all_chunks = [chunk for chunks in retrieval_results.values() for chunk in chunks]
    if not all_chunks:
        return None

    best_score = max(chunk.combined_score for chunk in all_chunks)
    if best_score < MIN_CONFIDENCE_THRESHOLD:
        return (
            f"The best-matching retrieved evidence scored {best_score:.2f} "
            f"(combined BM25 + semantic), below the minimum confidence "
            f"threshold of {MIN_CONFIDENCE_THRESHOLD}. Treating this as "
            "insufficiently supported rather than risking a low-confidence answer."
        )
    return None
