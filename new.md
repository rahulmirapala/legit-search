## Project Enhancements Overview

This file documents the newly implemented backend improvements: configuration management, pagination, multi_match search, caching, optional LLM-based query expansion, health endpoint, and structured response models.

### 1. Configuration (`app/config.py`)
Reason: Avoid hard-coded Elasticsearch host and index name; allow environment overrides.
Implementation: Pydantic `Settings` with `.env` support (fields: `es_host`, `index_name`, defaults). Function `get_settings()` is cached for performance.
Next: Add more fields (e.g., highlight sizes, max boost limits) as needed.

### 2. Schemas (`app/schemas.py`)
Reason: Strongly typed API responses and automatic OpenAPI documentation.
Implementation: `SearchHit` and `SearchResponse` Pydantic models. Endpoint now returns `SearchResponse` ensuring consistent shape.

### 3. Caching (`app/cache.py`)
Reason: Reduce Elasticsearch load for repeated identical queries (same parameters). Quick TTL-based in-memory cache.
Implementation: `TTLCache` storing entries as `(expiry_timestamp, value)`. Key builder `make_cache_key()` incorporates query text, boost, pagination, highlights, expansion, spell flags.
Tradeoff: Not shared between processes; acceptable for development.
Next: Replace with Redis for multi-instance deployments.

### 4. Query Expansion (`app/llm.py`)
Reason: Optional LLM (Google AI Studio / Gemini) based query expansion to surface related legal terms.
Implementation: Checks `LLM_API_KEY` env variable; if available, calls generative model with a focused prompt returning comma-separated terms.
Safety: If library/API missing or errors occur, returns empty list without failing the search.
Next: Add rate limiting, caching expansions, and evaluation of benefit.

### 5. Enhanced Search Endpoint (`app/main.py` changes)
Features Added:
- Pagination: `page`, `page_size` translated into `from` and `size` for ES.
- Title Boost clamp: Accepts `title_boost` within [1.0, 10.0].
- Highlight toggle: `include_highlights` boolean removes highlight section for performance when false.
- Spell correction toggle: `spell` param enables/disables `autospell`.
- LLM expansion toggle: `expand` param integrates optional expansion terms appended to query.
- Caching: Uses generated cache key; returns cached payload if found.
- Health endpoint: `/health` indicates ES connectivity and index existence.
Data Flow:
1. Optional spell correction.
2. Optional LLM expansion.
3. Build final query string.
4. Compose ES multi_match query via new builder (`build_multi_match_query`).
5. Execute search; format hits into `SearchResponse`.
6. Cache the response payload.

### 6. Multi-Match Query Builder (`app/search.py`)
Reason: Replace brittle `query_string` with safer `multi_match` (type `best_fields`). Allows better control over boosting and user queries without errors due to reserved characters.
Implementation: `build_multi_match_query()` with parameters: query text, title boost, pagination offsets, and highlight toggle.
Legacy: The original `build_search_query` retained for reference/testing only.

### 7. Health Endpoint
Reason: Simple operational visibility for deployment and automated checks.
Implementation: `/health` verifies ES ping and index existence: returns JSON with status fields.

### 8. Environment / Secret Handling
LLM API key pulled from `LLM_API_KEY` environment variable to avoid committing secrets. (Ensure `.env` is added to `.gitignore`).
Next: Add `.gitignore` line if missing and sample `.env.example`.

### 9. Future Steps Suggested
- Add index creation script (`scripts/create_index.py`).
- Introduce filters and additional analyzers.
- Add tests for new modules (cache key uniqueness, expansion fallback, pagination math).
- Implement frontend consuming new pagination and expansion parameters.

### 9.1 Added Index Creation Script
`scripts/create_index.py` creates index with custom analyzer `legal_text_analyzer` and explicit field mappings.

### 9.2 Logging & Metrics
`app/logging_config.py` sets a basic formatter; middleware in `main.py` logs request method, path, status, and duration.
`app/metrics.py` exposes Prometheus metrics at `/metrics` and tracks request count & latency via middleware.

### 9.3 Semantic Embeddings
`app/semantic.py` loads a sentence-transformers model (default `all-MiniLM-L6-v2`) if available and provides `embed_texts`. Not yet integrated into search; planned hybrid retrieval.

### 9.4 Reranking
`app/rerank.py` optionally loads a cross-encoder model (`ms-marco-MiniLM-L-6-v2`) and provides `rerank(query, hits)` to reorder results by model score. Integration path: call after ES retrieval and before caching.

### 9.5 Next Integration Plan for Semantic & Rerank
1. Store document chunk embeddings (new index field or external vector store).
2. Accept `semantic=true` query param -> perform embedding of query, run approximate nearest neighbor search.
3. Merge lexical + vector scores (weighted sum) then run cross-encoder rerank for top 50.
4. Cache final list.

### 9.6 Additional Dependencies Needed (Optional)
Add to requirements if you proceed: `sentence-transformers`, `prometheus-client`.


### 10. Risks / Considerations
- Cache staleness: 5-minute TTL may serve outdated results after reindex. Acceptable during development.
- Expansion quality depends on LLM; need evaluation before enabling by default.
- Missing `pydantic` dependency currently (needs addition to requirements.txt).
- No error codes standardization yet; still generic HTTP responses.

### 11. Required Dependency Update
Add `pydantic` and `google-generativeai` (optional) to `requirements.txt` for full functionality.

### 12. Testing Recommendations
Unit Tests:
- `test_cache.py`: Ensure expiry works and eviction removes oldest.
- `test_query_builder.py`: Check field list and pagination offsets.
- `test_llm_expansion.py`: With and without API key (mock environment).

Integration Tests:
- Start ES; index sample docs; verify pagination total and page boundaries.

### 13. Metrics to Add Later
- Request latency
- Cache hit ratio
- Expansion usage rate

### 14. How to Use New Parameters
Example request:
`/search?q=right to privacy&page=2&page_size=5&title_boost=4&include_highlights=false&expand=true&spell=true`

    ### 15. Rollback Plan
    If multi_match causes relevance regression, revert to legacy builder (`build_search_query`) by switching call in `main.py`.

---
This document will evolve as new features (filters, semantic search, reranking) are implemented.