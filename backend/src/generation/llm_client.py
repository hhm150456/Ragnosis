"""
LLM client wrapper for the generation layer.

Switchable backend, same pattern as src/embeddings/embedder.py. Set
GENERATION_BACKEND and the corresponding model name in config.py before use —
model name placeholders are intentionally left for you to fill in with
whatever you have API access to (check your provider's current docs; model
names change over time and this repo should not hardcode one that may be
stale).
"""

import os
from functools import lru_cache

from config import (
    GENERATION_BACKEND,
    GENERATION_MODEL_ANTHROPIC,
    GENERATION_MODEL_OPENAI,
    GENERATION_MODEL_GEMINI,
    GENERATION_TEMPERATURE,
    GENERATION_MAX_TOKENS,
)


class LLMClient:
    def __init__(self, backend: str = GENERATION_BACKEND):
        self.backend = backend
        if backend == "anthropic":
            self._client = _load_anthropic_client()
        elif backend == "openai":
            self._client = _load_openai_client()
        elif backend == "gemini":
            self._client = _load_gemini_client()
        else:
            raise ValueError(f"Unknown GENERATION_BACKEND: {backend}")

    def generate(self, system_prompt: str, user_prompt: str) -> str:
        """Returns the raw text response from the model. Caller is
        responsible for JSON parsing/validation (see response_parser.py)."""
        if self.backend == "anthropic":
            response = self._client.messages.create(
                model=GENERATION_MODEL_ANTHROPIC,
                max_tokens=GENERATION_MAX_TOKENS,
                temperature=GENERATION_TEMPERATURE,
                system=system_prompt,
                messages=[{"role": "user", "content": user_prompt}],
            )
            return "".join(
                block.text for block in response.content if getattr(block, "type", None) == "text"
            )
        elif self.backend == "gemini":
            from google.genai import types

            response = self._client.models.generate_content(
                model=GENERATION_MODEL_GEMINI,
                contents=user_prompt,
                config=types.GenerateContentConfig(
                    system_instruction=system_prompt,
                    temperature=GENERATION_TEMPERATURE,
                    max_output_tokens=GENERATION_MAX_TOKENS,
                ),
            )
            return response.text
        else:  # openai
            response = self._client.chat.completions.create(
                model=GENERATION_MODEL_OPENAI,
                max_tokens=GENERATION_MAX_TOKENS,
                temperature=GENERATION_TEMPERATURE,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt},
                ],
            )
            return response.choices[0].message.content


@lru_cache(maxsize=1)
def _load_anthropic_client():
    import anthropic

    api_key = os.environ.get("ANTHROPIC_API_KEY")
    if not api_key:
        raise EnvironmentError(
            "GENERATION_BACKEND is 'anthropic' but ANTHROPIC_API_KEY is not set. "
            "Set it in your .env file."
        )
    return anthropic.Anthropic(api_key=api_key)


@lru_cache(maxsize=1)
def _load_gemini_client():
    from google import genai

    api_key = os.environ.get("GEMINI_API_KEY") or os.environ.get("GOOGLE_API_KEY")
    if not api_key:
        raise EnvironmentError(
            "GENERATION_BACKEND is 'gemini' but neither GEMINI_API_KEY nor GOOGLE_API_KEY "
            "is set. Set GEMINI_API_KEY in your .env file."
        )
    return genai.Client(api_key=api_key)


@lru_cache(maxsize=1)
def _load_openai_client():
    from openai import OpenAI

    api_key = os.environ.get("OPENAI_API_KEY")
    if not api_key:
        raise EnvironmentError(
            "GENERATION_BACKEND is 'openai' but OPENAI_API_KEY is not set. "
            "Set it in your .env file."
        )
    return OpenAI(api_key=api_key)