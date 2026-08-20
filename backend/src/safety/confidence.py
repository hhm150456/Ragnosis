"""
Pre-generation retrieval-confidence gate.

If the best-scoring retrieved chunk is clearly weak, refuse before spending a
generation call on it at all, rather than letting a low-quality match get
sent to the LLM and hoping it declines gracefully.

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

import re

from config import MIN_CONFIDENCE_THRESHOLD, OUT_OF_CORPUS_QUERY_TERMS


def invalid_query_reason(query: str) -> str | None:
    """Return a refusal reason for input too weak to search reliably."""
    words = [word for word in query.split() if any(character.isalnum() for character in word)]
    if not words or not any(sum(character.isalpha() for character in word) >= 2 for word in words):
        return (
            "The query is too short or contains insufficient clinical language "
            "to search the evidence corpus. Please enter a medication, condition, "
            "or clinical question."
        )
    return None


def low_confidence_reason(query: str, retrieval_results: dict[str, list]) -> str | None:
    """
    retrieval_results: output of HybridRetriever.retrieve_compound(), keyed
        by collection name.

    Returns a human-readable refusal reason if retrieval confidence is too
    low to proceed to generation, or None if it's fine to continue.
    """
    query_terms = set(re.findall(r"[a-z0-9]+", query.casefold()))
    unsupported_terms = query_terms & OUT_OF_CORPUS_QUERY_TERMS
    if unsupported_terms:
        terms = ", ".join(sorted(unsupported_terms))
        return f"The query mentions out-of-corpus subject matter: {terms}."

    all_chunks = [chunk for chunks in retrieval_results.values() for chunk in chunks]
    if not all_chunks:
        return None

    # combined_score is the stable score calibrated against the configured
    # threshold. rerank_score may be an unbounded model-specific logit.
    best_score = max(chunk.combined_score for chunk in all_chunks)
    if best_score < MIN_CONFIDENCE_THRESHOLD:
        return (
            f"The best-matching retrieved evidence scored {best_score:.2f} "
            f"(combined BM25 + semantic), below the minimum confidence "
            f"threshold of {MIN_CONFIDENCE_THRESHOLD}. Treating this as "
            "insufficiently supported rather than risking a low-confidence answer."
        )
    return None
