"""
Prompt construction for the grounded generation layer.

Core design decision: the model is asked to cite by CHUNK ID, never by
writing its own document name / section / page number. We resolve the
actual citation metadata ourselves from the retrieval layer's trusted
output. This means the model literally cannot hallucinate a wrong page
number or section title — it can only fail to ground a claim at all
(pick no matching chunk_id, or invent one), both of which are checkable
and caught in response_parser.py / generator.py.

Output is strict JSON so it can be programmatically validated and, later,
fed into the Day 4 faithfulness check.
"""

from backend.src.retrieval.hybrid_retriever import RetrievedChunk
from config import COLLECTION_RECOMMENDATIONS, COLLECTION_SAFETY_LABELS

SYSTEM_PROMPT = """You are a clinical evidence retrieval assistant. You answer questions ONLY using \
the excerpts provided to you in the CONTEXT section below. You have no other medical knowledge \
available to you for this task, even if you happen to know the answer from general training.

STRICT RULES — violating any of these is a critical failure:

1. Use ONLY the provided context excerpts. Never use outside medical knowledge, even if you are \
confident it is correct. If the context doesn't say it, you don't know it.
2. Every claim you make MUST be tied to exactly one provided chunk, referenced by its chunk_id. \
Do not write your own document name, section name, or page number — you will reference chunks by \
ID only, and the citation details will be resolved separately from trusted metadata.
3. Never invent a chunk_id. Only use chunk_id values that appear in the CONTEXT section, copied exactly.
4. If the question requires evidence this context does not contain — even partially — say so \
explicitly rather than guessing or extrapolating. A partially-grounded answer must clearly separate \
what IS supported from what is NOT.
5. If NONE of the provided context addresses the question, refuse entirely. Do not attempt an answer \
built from general knowledge.
6. Output ONLY valid JSON matching the schema below. No markdown code fences, no preamble, no \
commentary outside the JSON structure.

OUTPUT SCHEMA (JSON):
{
  "status": "answered" | "partial_refusal" | "full_refusal",
  "refusal_reason": string or null,
  "answer_summary": string,
  "recommendations": [
    {
      "claim": string,
      "evidence_grade": string or null,
      "excerpt": string,
      "source_chunk_id": string
    }
  ]
}

Field guidance:
- "status": "answered" if the context fully supports a response; "partial_refusal" if some but not \
all of the question is grounded (explain the gap in refusal_reason AND still populate \
recommendations with what IS supported); "full_refusal" if nothing relevant was retrieved.
- "refusal_reason": required and specific when status is not "answered". State plainly what the \
provided context does not cover — do not soften it into a vague deflection.
- "answer_summary": 1-3 plain-language sentences. If status is full_refusal, this should say so \
plainly, not attempt a partial answer.
- "recommendations": one entry per distinct grounded claim. Empty list if status is full_refusal.
- "excerpt": a short supporting quote or close paraphrase from the cited chunk (under 40 words), \
not the full chunk text.
- "evidence_grade": only for chunks from the recommendations collection where a USPSTF grade \
(A/B/C/D/I) is explicitly present in the chunk metadata or text; otherwise null.
- "source_chunk_id": must exactly match a chunk_id shown in CONTEXT. This is validated after your \
response — an invented or mismatched id will cause that claim to be discarded."""


def format_context(results: dict[str, list[RetrievedChunk]]) -> str:
    """
    Formats retrieved chunks from both collections into the CONTEXT block
    the model sees, grouped by collection so the model can reason about
    which evidence type it's drawing from.
    """
    sections = []

    labels = {
        COLLECTION_RECOMMENDATIONS: "PREVENTIVE MEDICATION RECOMMENDATIONS (USPSTF)",
        COLLECTION_SAFETY_LABELS: "DRUG SAFETY LABELS (DailyMed/FDA)",
    }

    for collection_name, chunks in results.items():
        label = labels.get(collection_name, collection_name)
        sections.append(f"=== {label} ===")

        if not chunks:
            sections.append(
                "(No chunks were retrieved from this source for this query. If the question "
                "needs this type of evidence, you do not have it — reflect that in your status "
                "and refusal_reason.)"
            )
            continue

        for c in chunks:
            doc = c.metadata.get("document_name", "unknown document")
            section_title = c.metadata.get("section_title", "unknown section")
            page = c.metadata.get("page_numbers", "?")
            sections.append(
                f"[chunk_id: {c.chunk_id}]\n"
                f"(from: {doc}, section: {section_title}, page: {page})\n"
                f"{c.text}\n"
            )

    return "\n".join(sections)


def build_user_prompt(query: str, results: dict[str, list[RetrievedChunk]]) -> str:
    context_block = format_context(results)
    return (
        f"CONTEXT:\n{context_block}\n\n"
        f"QUESTION:\n{query}\n\n"
        f"Respond with the JSON object described in your instructions. Nothing else."
    )
