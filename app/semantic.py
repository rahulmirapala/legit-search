"""Semantic embedding utilities for hybrid search.
If sentence-transformers is available, provides embedding generation.
"""
from typing import List, Optional
import os

_MODEL_NAME = os.getenv("EMBED_MODEL", "sentence-transformers/all-MiniLM-L6-v2")
_model = None

def get_model():
    """Lazy load the embedding model."""
    global _model
    if _model is None:
        try:
            from sentence_transformers import SentenceTransformer  # type: ignore
            _model = SentenceTransformer(_MODEL_NAME)
        except Exception as e:
            print(f"Warning: Could not load embedding model: {e}")
            _model = False
    return _model if _model is not False else None

def embed_texts(texts: List[str]) -> List[List[float]]:
    """Generate embeddings for a list of texts."""
    model = get_model()
    if not model:
        return []
    return model.encode(texts, convert_to_numpy=False, show_progress_bar=False).tolist()

def embed_query(query: str) -> Optional[List[float]]:
    """Generate embedding for a single query."""
    model = get_model()
    if not model:
        return None
    return model.encode([query], convert_to_numpy=False, show_progress_bar=False)[0].tolist()

def is_available() -> bool:
    """Check if semantic embeddings are available."""
    return get_model() is not None
