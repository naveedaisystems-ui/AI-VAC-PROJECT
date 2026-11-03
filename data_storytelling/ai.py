"""Optional Gemini integration; deterministic local analysis remains the default."""

from __future__ import annotations

import os
from typing import Any


def gemini_api_key() -> str | None:
    return os.getenv("GOOGLE_API_KEY") or os.getenv("GEMINI_API_KEY")


def gemini_available() -> bool:
    return bool(gemini_api_key())


def generate_gemini_text(prompt: str, model: str | None = None) -> str:
    """Send an explicitly requested prompt to Gemini without sending raw rows."""
    key = gemini_api_key()
    if not key:
        raise RuntimeError(
            "Set GOOGLE_API_KEY or GEMINI_API_KEY in the environment to use Gemini."
        )

    from google import genai

    client = genai.Client(api_key=key)
    response = client.models.generate_content(
        model=model or os.getenv("GEMINI_MODEL", "gemini-2.5-flash"),
        contents=prompt,
    )
    text = getattr(response, "text", None)
    if not text:
        raise RuntimeError("Gemini returned no text. Check the API response or quota.")
    return str(text)


def question_prompt(columns: list[str], sample_summary: dict[str, Any]) -> str:
    return (
        "Generate at least 10 answerable analytical questions grouped under Trends, "
        "Comparisons, Distributions, and Relationships. Use only these column names "
        f"and observed summary: columns={columns}; summary={sample_summary}. "
        "Do not make up dataset results or claim questions have been answered."
    )
