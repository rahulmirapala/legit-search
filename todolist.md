# Improvement Backlog Detailed Guide

This document explains each backlog item: what it means, why it matters, suggested tools/libraries, key implementation steps, and acceptance criteria.

---
## 1. Define ES index mapping
Purpose: Prevent unpredictable dynamic mappings; enable better search relevance.
Tools: Elasticsearch Python client.
Steps: Create script `scripts/create_index.py` that checks if index exists; if not, PUT with mappings (text fields with keyword subfields, custom analyzer). Fields: case_name(text+keyword), judgment_date(date), citation_id(keyword), full_text(text), year(integer).
Acceptance: Running script creates index with expected mappings; `GET /legit_search_index` shows configured analyzers.

## 2. Centralize configuration
Purpose: Avoid hardcoding host/index names; simpler environment changes.
Tools: Pydantic BaseSettings or python-dotenv.
Steps: Add `app/config.py` with class Settings; load ES_HOST, INDEX_NAME, PAGE_SIZE_DEFAULT, TITLE_BOOST_DEFAULT.
Acceptance: Changing .env value reflects in API without code change.

## 3. Refactor search utilities
Purpose: Separation of concerns improves testability.
Tools: Python modules.
Steps: Split into `spell.py`, `query_builder.py`; `es_client.py` returns singleton ES client.
Acceptance: Old functions still work; imports updated; tests pass.

## 4. Add pagination to /search
Purpose: Allow browsing beyond first 10 results.
Tools: FastAPI query params.
Steps: Add `page`, `page_size`; compute `from = (page-1)*page_size`; pass size and from to ES.
Acceptance: Page navigation returns correct slices; page 2 differs from page 1.

## 5. Switch to multi_match query
Purpose: `query_string` is brittle; `multi_match` safer for user input.
Tools: ES query DSL.
Steps: Replace builder with multi_match type='best_fields', fields ["case_name^boost", "full_text"]. Escape reserved characters or rely on multi_match.
Acceptance: Special chars no longer 400 errors; relevance comparable or better.

## 6. Introduce Pydantic models
Purpose: Structured validation and auto docs.
Tools: Pydantic (built into FastAPI).
Steps: Create `schemas.py` with SearchRequest/SearchResponse; adapt endpoint.
Acceptance: OpenAPI shows models; invalid params yield 422.

## 7. Improve spell correction
Purpose: Prevent incorrect correction of legal acronyms.
Tools: Add whitelist (set) & toggle param `spell=false`.
Steps: Skip correction for whitelisted tokens; if param false, bypass.
Acceptance: Queries keep 'AIR', 'SCC' intact; disabling works.

## 8. Add filters
Purpose: Targeted subset of documents.
Tools: ES bool query with filter clauses.
Steps: Accept year_from/year_to/date_from/date_to/citation_substring; build must + filter arrays.
Acceptance: Filtering reduces result set appropriately.

## 9. Add health endpoint
Purpose: Quick status check.
Tools: FastAPI route.
Steps: `/health` performs `ping()` and optionally `count` on index.
Acceptance: Returns JSON {"elasticsearch": "up", "index_exists": true}.

## 10. Structured logging
Purpose: Better observability & machine parsing.
Tools: Python logging, loguru or structlog.
Steps: Configure logger at startup; middleware logs request id, latency.
Acceptance: Logs appear in JSON format with required fields.

## 11. Bulk upload validation
Purpose: Detect and retry failures in ingestion.
Tools: Parse `_bulk` response JSON.
Steps: After curl, or via Python script, inspect `items`; collect errors; write `failed.jsonl` with those docs.
Acceptance: Running validation shows zero or lists failed docs; option to reupload.

## 12. Deterministic document IDs
Purpose: Avoid duplicates when reindexing.
Tools: hashlib.sha256.
Steps: Compute hash of filename + year; use `{ "index": {"_index":..., "_id": hash}}` in bulk file.
Acceptance: Re-running ingestion does not create duplicates.

## 13. Enhance citation extraction
Purpose: More accurate citation data.
Tools: Regex patterns.
Steps: Add patterns for AIR, SCR, SCC variants; split on commas; store array.
Acceptance: Citation array contains distinct normalized entries.

## 14. Improve text cleaning
Purpose: Remove noise, preserve structure.
Tools: Regex, heuristic page header removal.
Steps: Detect repeating header lines; remove page numbers; keep paragraph breaks.
Acceptance: Clean text improves readability; fewer artifacts.

## 15. Add OCR fallback
Purpose: Handle scanned PDFs.
Tools: pytesseract, pdf2image.
Steps: Detect low extracted char ratio; convert pages to images; OCR; merge text; mark `ocr_used=True`.
Acceptance: Scanned judgment yields non-empty text.

## 16. Unit tests core functions
Purpose: Guard against regressions.
Tools: pytest.
Steps: Tests for date parsing, citation extraction, query builder, pagination math.
Acceptance: `pytest` passes locally & in CI.

## 17. Integration tests with ES
Purpose: Validate end-to-end behavior.
Tools: docker-compose for test ES.
Steps: Start ES, index fixture docs, call API, assert responses.
Acceptance: All integration tests green.

## 18. CI workflow
Purpose: Automated quality gates.
Tools: GitHub Actions.
Steps: Add workflow YAML: setup Python, install deps, run ruff, black --check, pytest, pip-audit.
Acceptance: PRs show passing checks.

## 19. Add pre-commit hooks
Purpose: Enforce style before commit.
Tools: pre-commit.
Steps: `.pre-commit-config.yaml`; install; include black, isort, ruff.
Acceptance: Commits auto-format or fail if issues.

## 20. Add README sections
Purpose: Better onboarding.
Tools: Markdown.
Steps: Add Setup, Ingestion, Index creation, API examples, Troubleshooting.
Acceptance: README covers common tasks clearly.

## 21. Add Makefile tasks
Purpose: One-line developer commands.
Tools: Make.
Steps: Targets: create-index, ingest, split, upload, run, test, lint.
Acceptance: `make run` starts API; tasks documented.

## 22. Environment variable loading
Purpose: Config override without code edits.
Tools: python-dotenv or Pydantic Settings.
Steps: `.env` file; load at startup; fallback defaults.
Acceptance: Changing ES host in .env reflected after restart.

## 23. Add caching layer
Purpose: Reduce ES load for repeated queries.
Tools: In-memory TTL cache initially; optional Redis.
Steps: Implement key builder; check cache before search; store after.
Acceptance: Repeat identical query faster; log cache hits.

## 24. Add highlight toggle
Purpose: Speed queries when highlights unnecessary.
Tools: Query param `include_highlights: bool`.
Steps: Conditionally add highlight section in query body.
Acceptance: Setting false removes highlight overhead.

## 25. Add rate limiting
Purpose: Protect ES under traffic spikes.
Tools: slowapi or custom token bucket.
Steps: Middleware; limit per IP (e.g., 60/min); return 429 on excess.
Acceptance: Exceeding limit yields 429 response.

## 26. Add metrics
Purpose: Operational insights.
Tools: prometheus-client, FastAPI instrumentation.
Steps: Expose `/metrics`; track request latency, ES duration, cache hits.
Acceptance: Prometheus scrapes meaningful metrics.

## 27. Add tracing
Purpose: Distributed performance visibility.
Tools: OpenTelemetry SDK + exporter (OTLP/Jaeger).
Steps: Instrument FastAPI and ES client; spans show timeline.
Acceptance: Traces visible in chosen backend.

## 28. Dockerize project
Purpose: Consistent deployment.
Tools: Dockerfile, docker-compose (API + ES).
Steps: Multi-stage build; small final image; compose sets ES + API service.
Acceptance: `docker compose up` runs API accessible at host port.

## 29. Security hardening
Purpose: Reduce attack surface.
Tools: CORS middleware; pip-audit; optional auth.
Steps: Restrict origins; add dependency scan; configure ES auth if enabled.
Acceptance: Security checks pass; restricted origins enforced.

## 30. Add semantic search option
Purpose: Improve relevance via embeddings.
Tools: sentence-transformers, vector store (Elasticsearch dense vectors or FAISS).
Steps: Embed docs; store vectors; add `semantic=true` param to run vector similarity + BM25 hybrid.
Acceptance: Semantic queries return conceptually related cases.

## 31. Implement reranking
Purpose: Better ordering of top results.
Tools: cross-encoder model (e.g., ms-marco variants).
Steps: Take top N BM25 hits; rerank by model scoring; replace order.
Acceptance: Reranked list improves judged relevance in manual tests.

## 32. Synonym & stopword lists
Purpose: Improve query expansion and precision.
Tools: ES custom analyzer; synonyms file; stopwords file.
Steps: Update index settings; reindex docs.
Acceptance: Queries with synonyms match expanded results.

## 33. Query logging/audit
Purpose: Usage analytics & improvement feedback.
Tools: SQLite/Postgres or flat file logging.
Steps: Middleware logs anonymized query, timestamp, response time.
Acceptance: Log store accumulates entries; can derive top queries.

## 34. Error handling middleware
Purpose: Uniform error responses.
Tools: FastAPI custom exception handlers.
Steps: Wrap 500s with correlation id; map known exceptions to structured JSON.
Acceptance: Error payloads conform to schema.

## 35. Improve spell performance
Purpose: Lower latency on long queries.
Tools: LRU cache for token corrections.
Steps: Cache corrected tokens; skip re-correction; disable for >N words.
Acceptance: Long query latency reduced measurably.

## 36. Add citation search endpoint
Purpose: Allow precise citation lookups.
Tools: New route `/search/citation` using term/keyword queries.
Steps: Accept citation string; perform keyword match; partial via wildcard or match_phrase.
Acceptance: Known citation returns exact case.

## 37. Add year stats endpoint
Purpose: Provide distribution insights.
Tools: ES aggregations (terms or date_histogram).
Steps: Endpoint runs aggregation on `year`; returns counts.
Acceptance: JSON lists years and doc counts.

## 38. Bulk ingestion progress bar
Purpose: Better feedback during long ingestion.
Tools: tqdm.
Steps: Wrap iteration over PDFs; show rate and ETA.
Acceptance: CLI shows live progress.

## 39. Deduplication check
Purpose: Identify near duplicate docs.
Tools: Hashing (SimHash or MinHash) or simple normalized SHA256.
Steps: Scan all docs; build map of hashes; flag collisions.
Acceptance: Report lists duplicates or states none found.

## 40. Title boost limits
Purpose: Prevent extreme boosts harming relevance.
Tools: Clamp logic.
Steps: Config min/max; enforce in endpoint; return applied value.
Acceptance: Supplying out-of-range value automatically clamps.

## 41. Replace prints in scripts
Purpose: Consistent logging levels.
Tools: logging module.
Steps: Initialize logger; replace print with logger.info/error; add `--verbose` flag for DEBUG.
Acceptance: Running script produces structured logs, respects verbosity.

## 42. Parameterize ingestion paths
Purpose: Flexible ingestion for different datasets.
Tools: argparse / click.
Steps: Add CLI args: --root, --output, --year-from, --year-to.
Acceptance: Different paths processed without code changes.

## 43. Improve splitting script
Purpose: More robust large file handling.
Tools: Python IO.
Steps: Add size-based mode; manifest JSON describing parts; resume logic if partially completed.
Acceptance: Manifest file lists all part filenames and doc counts.

## 44. Bulk upload retry tool
Purpose: Efficient correction of failed items.
Tools: Python script parsing error log.
Steps: Read `failed.jsonl`; re-upload using smaller batches; report success count.
Acceptance: After retry, remaining failures minimal or zero.

## 45. Add OpenAPI examples
Purpose: Better API exploration.
Tools: FastAPI `schema_extra` or `example` attribute in Pydantic models.
Steps: Populate example search request/response.
Acceptance: Swagger UI shows examples pre-filled.

## 46. Citation normalization function
Purpose: Consistent formatting for sorting/filtering.
Tools: Regex & normalization rules.
Steps: Map variants to canonical form; store `citations_normalized` array.
Acceptance: Different input formats map to same normalized citation.

## 47. Implement search safety
Purpose: Prevent errors from special characters.
Tools: Character escaping / fallback to multi_match.
Steps: Escape reserved chars when using query_string; (Earlier replaced by multi_match, but keep for safety if both modes exist.)
Acceptance: Queries containing + - : ( ) no longer fail.

## 48. Highlight context merging
Purpose: Improve readability of highlight fragments.
Tools: Algorithm to merge overlapping or adjacent fragments if gap < N chars.
Steps: Post-process highlight list; merge and truncate.
Acceptance: Fewer fragmented sentences in response highlights.

## 49. Add test fixtures
Purpose: Reproducible tests & quick start.
Tools: Store small sample PDFs and expected JSON.
Steps: `tests/fixtures/` folder with PDFs + metadata JSON.
Acceptance: Tests load fixtures reliably; no external dependencies.

## 50. Performance benchmark suite
Purpose: Track regressions and optimize.
Tools: pytest-benchmark or custom timing harness.
Steps: Benchmark spell correction, query build, ES latency on sample queries; store baseline results.
Acceptance: Benchmark report generated; changes can be compared.

## 51. Create todolist.md explanations
Purpose: Provide this reference document.
Acceptance: File committed with all items documented (this file).

---
## Suggested Initial Implementation Order
1. 1, 2, 6, 4, 5
2. 10, 11, 16, 18, 28
3. 23, 24, 25, 26, 9
4. Remaining items by strategic need.

## Notes
- Some items (30–31) are higher complexity; schedule after core stability.
- Reindex required after analyzer changes (1, 32).
- Semantic features (30, 31) benefit from having benchmark suite (50).

---
Feel free to prune or reprioritize. Start small, keep changes incremental.
