"""LLM integration helpers.

Query expansion uses Google AI Studio (Gemini). The API key can be supplied via:
1. `.env` file loaded by `Settings` (variable: llm_api_key)
2. Environment variable names `LLM_API_KEY` or legacy `GEMINI_API_KEY`

If no key or library present, expansion returns an empty list silently.
"""
from typing import List
import os
from .config import get_settings

try:
    import google.generativeai as genai  # type: ignore
except ImportError:  # Library not installed yet
    genai = None  # type: ignore

_EXPANSION_PROMPT = (
    "You are a legal search assistant. Given a short user query, list 3 to 5 related legal "
    "terms or synonyms relevant to Indian constitutional or Supreme Court jurisprudence. "
    "Return ONLY a comma-separated list of terms. Query: "
)

def _resolve_api_key() -> str | None:
    settings_key = get_settings().llm_api_key
    if settings_key:
        return settings_key
    # Fallback to direct env variables
    return os.getenv("LLM_API_KEY") or os.getenv("GEMINI_API_KEY")

def _init_client(api_key: str):
    if not genai:
        return None
    genai.configure(api_key=api_key)
    return genai


def expand_query_safe(query: str) -> List[str]:
    api_key = _resolve_api_key()
    if not api_key or not genai:
        return []  # expansion disabled
    try:
        _init_client(api_key)
        model = genai.GenerativeModel("gemini-pro")
        response = model.generate_content(_EXPANSION_PROMPT + query)
        text = response.text.strip()
        # Expect comma-separated terms
        parts = [p.strip() for p in text.split(",") if p.strip()]
        # Basic sanity filter: keep short terms
        return [p for p in parts if 1 < len(p) <= 40][:6]
    except Exception:
        return []

_REWRITE_PROMPT = (
    "You are a legal search assistant. Rewrite the user's query into an optimal concise "
    "boolean-style search expression for Supreme Court judgments. Preserve intent; use AND/OR only if helpful. Query: "
)

def rewrite_query_safe(query: str) -> str | None:
    api_key = _resolve_api_key()
    if not api_key or not genai:
        return None
    try:
        _init_client(api_key)
        model = genai.GenerativeModel("gemini-pro")
        response = model.generate_content(_REWRITE_PROMPT + query)
        text = (response.text or "").strip()
        # Strip surrounding quotes if present
        if (text.startswith('"') and text.endswith('"')) or (text.startswith("'") and text.endswith("'")):
            text = text[1:-1]
        # Avoid overly long rewrites
        return text[:200] if text else None
    except Exception:
        return None

_CLASSIFY_PROMPT = (
    "Classify the legal query into 1-3 high-level categories from: constitutional rights, procedure, criminal law, civil law, administrative law, taxation, environment, labour, intellectual property, miscellaneous. Return ONLY comma-separated categories. Query: "
)

def classify_query_safe(query: str) -> List[str]:
    api_key = _resolve_api_key()
    if not api_key or not genai:
        return []
    try:
        _init_client(api_key)
        model = genai.GenerativeModel("gemini-pro")
        response = model.generate_content(_CLASSIFY_PROMPT + query)
        text = (response.text or "").strip()
        parts = [p.strip().lower() for p in text.split(',') if p.strip()]
        # Basic normalization
        unique = []
        for p in parts:
            if p not in unique:
                unique.append(p)
        return unique[:3]
    except Exception:
        return []
