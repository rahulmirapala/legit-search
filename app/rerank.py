"""Reranking utilities using an optional cross-encoder model.
If model lib not installed, functions degrade gracefully.
"""
from typing import List, Dict
import os

_RERANK_MODEL = os.getenv("RERANK_MODEL", "cross-encoder/ms-marco-MiniLM-L-6-v2")
_ce = None

def get_model():
    """Lazy load the cross-encoder model."""
    global _ce
    if _ce is None:
        try:
            from sentence_transformers import CrossEncoder  # type: ignore
            _ce = CrossEncoder(_RERANK_MODEL)
            print(f"Loaded reranking model: {_RERANK_MODEL}")
        except Exception as e:
            print(f"Warning: Could not load reranking model: {e}")
            _ce = False
    return _ce if _ce is not False else None

def rerank(query: str, hits: List[Dict]) -> List[Dict]:
    """Rerank hits based on cross-encoder scores.
    Each hit expected to have case_name and full_text or highlights.
    Returns hits sorted by rerank_score (descending).
    """
    model = get_model()
    if not model or not hits:
        return hits  # No change
    
    # Build query-document pairs for scoring
    pairs = []
    for h in hits:
        # Combine case_name with either highlights or truncated full_text
        doc_text = h.get('case_name', '')
        if h.get('highlights'):
            doc_text += ' ' + ' '.join(h['highlights'])
        elif h.get('full_text'):
            doc_text += ' ' + h['full_text'][:500]  # Use first 500 chars
        pairs.append((query, doc_text))
    
    # Get rerank scores
    scores = model.predict(pairs)
    
    # Attach scores and sort
    for h, s in zip(hits, scores):
        h['rerank_score'] = float(s)
    
    return sorted(hits, key=lambda x: x.get('rerank_score', 0), reverse=True)

def is_available() -> bool:
    """Check if reranking is available."""
    return get_model() is not None
