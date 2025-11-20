import time
from typing import Any

class TTLCache:
    def __init__(self, ttl_seconds: int = 300, max_size: int = 500):
        self.ttl = ttl_seconds
        self.max_size = max_size
        self.store: dict[str, tuple[float, Any]] = {}

    def get(self, key: str):
        entry = self.store.get(key)
        if not entry:
            return None
        expires_at, value = entry
        if time.time() > expires_at:
            del self.store[key]
            return None
        return value

    def set(self, key: str, value: Any):
        if len(self.store) >= self.max_size:
            # naive eviction: remove oldest
            oldest_key = min(self.store.items(), key=lambda kv: kv[1][0])[0]
            del self.store[oldest_key]
        self.store[key] = (time.time() + self.ttl, value)

cache = TTLCache()

def make_cache_key(final_query: str, title_boost: float, page: int, page_size: int,
                   include_highlights: bool, expand: bool, spell: bool,
                   mode: str = "bm25", semantic_weight: float = 0.3, rerank: bool = False,
                   raw_query: bool = False, fuzzy: bool = False, synonyms: bool = False) -> str:
    return "|".join([
        final_query,
        f"boost={title_boost}",
        f"page={page}",
        f"size={page_size}",
        f"hl={int(include_highlights)}",
        f"expand={int(expand)}",
        f"spell={int(spell)}",
        f"mode={mode}",
        f"sem_w={semantic_weight}",
        f"rerank={int(rerank)}",
        f"raw={int(raw_query)}",
        f"fuzzy={int(fuzzy)}",
        f"syn={int(synonyms)}"
    ])
