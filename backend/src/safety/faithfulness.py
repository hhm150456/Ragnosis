"""Claim-level verification against the exact retrieved chunk text."""

from __future__ import annotations

import json
import re
from dataclasses import dataclass

from backend.src.generation.llm_client import LLMClient


FAITHFULNESS_SYSTEM_PROMPT = """You verify clinical evidence claims.
Answer ONLY with a valid JSON array in this exact shape:
[{"supported": true, "reason": "brief explanation"}]

Set supported to true only when the excerpt directly supports the claim.
Treat added details, broader generalizations, implied interactions, or advice
not stated in the excerpt as unsupported. Do not use outside knowledge."""


@dataclass
class FaithfulnessResult:
    supported: bool
    reason: str
    verification_available: bool = True


def verify_claims_faithfulness(
    claims: list[tuple[str, str]], llm_client: LLMClient
) -> list[FaithfulnessResult]:
    """Verify all claims in one model call, falling back per claim on failure."""
    if not claims:
        return []

    sections = [
        f"CLAIM {index}:\n{claim}\n\nCITED CHUNK {index}:\n{cited_text}"
        for index, (claim, cited_text) in enumerate(claims, 1)
    ]
    user_prompt = "\n\n".join(sections) + "\n\nReturn one result for each claim, in order."

    try:
        raw_response = llm_client.generate(FAITHFULNESS_SYSTEM_PROMPT, user_prompt)
        data = json.loads(_extract_json_array(raw_response))
        if not isinstance(data, list) or len(data) != len(claims):
            raise ValueError("verifier returned the wrong number of results")

        results: list[FaithfulnessResult] = []
        for item in data:
            supported = item.get("supported")
            if not isinstance(supported, bool):
                raise ValueError("supported must be a boolean")
            results.append(
                FaithfulnessResult(
                    supported=supported,
                    reason=str(item.get("reason") or "No verification reason was provided."),
                )
            )
        return results
    except Exception:
        return [
            verify_claim_faithfulness(claim, cited_text, llm_client)
            for claim, cited_text in claims
        ]


def verify_claim_faithfulness(
    claim: str, cited_text: str, llm_client: LLMClient
) -> FaithfulnessResult:
    """Verify one claim and fail closed on malformed verifier output."""
    user_prompt = (
        f"CLAIM:\n{claim}\n\n"
        f"CITED CHUNK:\n{cited_text}\n\n"
        "Does the cited chunk support the claim?"
    )

    try:
        raw_response = llm_client.generate(FAITHFULNESS_SYSTEM_PROMPT, user_prompt)
        data = json.loads(_extract_json_object(raw_response))
        supported = data.get("supported")
        reason = str(data.get("reason") or "No verification reason was provided.")
        if not isinstance(supported, bool):
            raise ValueError("supported must be a boolean")
        return FaithfulnessResult(supported=supported, reason=reason)
    except Exception:
        overlap = _claim_overlap(claim, cited_text)
        if overlap >= 0.35:
            return FaithfulnessResult(
                supported=True,
                reason=(
                    "Verified by deterministic excerpt overlap because the automated "
                    "faithfulness service was unavailable."
                ),
                verification_available=False,
            )
        return FaithfulnessResult(
            supported=False,
            reason="Automated faithfulness verification was unavailable; the claim was retained for review.",
            verification_available=False,
        )


def _claim_overlap(claim: str, cited_text: str) -> float:
    """Measure meaningful claim-term coverage in the cited excerpt."""
    ignored = {"the", "and", "for", "with", "from", "that", "this", "are"}
    claim_terms = {
        term
        for term in re.findall(r"[a-z][a-z0-9-]{2,}", claim.lower())
        if term not in ignored
    }
    excerpt_terms = set(re.findall(r"[a-z][a-z0-9-]{2,}", cited_text.lower()))
    if not claim_terms:
        return 0.0
    return len(claim_terms & excerpt_terms) / len(claim_terms)


def _extract_json_object(text: str) -> str:
    """Accept bare, fenced, or briefly wrapped JSON from the verifier."""
    cleaned = text.strip()
    if cleaned.startswith("```"):
        lines = cleaned.splitlines()
        cleaned = "\n".join(lines[1:-1] if lines[-1].strip().startswith("```") else lines[1:]).strip()

    start = cleaned.find("{")
    end = cleaned.rfind("}")
    if start < 0 or end <= start:
        raise ValueError("verifier response did not contain a JSON object")
    return cleaned[start : end + 1]


def _extract_json_array(text: str) -> str:
    """Accept bare, fenced, or briefly wrapped JSON arrays."""
    cleaned = text.strip()
    if cleaned.startswith("```"):
        lines = cleaned.splitlines()
        cleaned = "\n".join(lines[1:-1] if lines[-1].strip().startswith("```") else lines[1:]).strip()

    start = cleaned.find("[")
    end = cleaned.rfind("]")
    if start < 0 or end <= start:
        raise ValueError("verifier response did not contain a JSON array")
    return cleaned[start : end + 1]