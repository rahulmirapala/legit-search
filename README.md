# Legit Search

Production-ready Information Retrieval system for legal judgments featuring hybrid search (BM25 + semantic embeddings), optional LLM query expansion, cross-encoder reranking, and comprehensive evaluation toolkit — with FastAPI backend and React frontend.

## 🚀 Features

### Search Capabilities
- **Multi-mode search**: BM25, Hybrid (BM25 + semantic), Pure semantic
- **Query enhancement**: Spell correction + optional LLM expansion (Google Gemini)
- **Reranking**: Cross-encoder based result reranking
- **Filtering**: Year range and court filters
- **Highlighting**: Configurable snippet highlighting

### Backend Infrastructure
- **FastAPI** REST API with comprehensive error handling
- **Elasticsearch** 8.x with custom legal text analyzer
- **Structured JSON logging** with request ID correlation
- **Prometheus metrics** for monitoring
- **TTL caching** for identical queries
- **Pydantic** models for type safety

### Frontend
- **React** single-page application
- **Responsive design** with dark/light themes
- **Advanced filters** panel
- **Pagination** and result highlighting
- **Modal detail view**

### DevOps & Quality
- **Docker** containerization (backend, frontend, ES)
- **docker-compose** for local development
- **pytest** test suite (unit + integration)
- **GitHub Actions** CI pipeline (lint, test, security scan, build)
- **Evaluation harness** for retrieval quality metrics

## 📊 Architecture

```
┌─────────────┐      ┌──────────────┐      ┌─────────────────┐
│   React UI  │─────▶│  FastAPI API │─────▶│ Elasticsearch   │
│  (Frontend) │      │   (Backend)  │      │   (Storage)     │
└─────────────┘      └──────────────┘      └─────────────────┘
                            │
                            ├──▶ Gemini API (optional expansion)
                            ├──▶ Sentence-Transformers (embeddings)
                            └──▶ Cross-Encoder (reranking)
- `search_priority` (default: balanced): Emphasis on specific sections (heading, introduction, body, conclusion)
- `min_score` (default: 0.0): Minimum score threshold to include a hit
- `highlight_size` (default: 150): Per-fragment character size
- `highlight_fragments` (default: 3): Number of highlight fragments to return
- `raw_query` (default: false): When true, includes the raw Elasticsearch query body in the response
```

## Key Features (Backend)

Implemented:
1. Multi-field search (title boosted) via multi_match
2. Pagination & structured responses (SearchResponse model)
3. Optional spell correction & LLM expansion (Gemini)
4. TTL in-memory caching of identical queries
5. Health endpoint (/health) and Prometheus metrics (/metrics)
6. Index creation script with custom analyzer (scripts/create_index.py)
7. Logging middleware (baseline)
8. Highlight toggle & query trace metadata

Scaffolded / Planned:
1. Semantic embeddings (app/semantic.py) -> dense vector field
2. Cross-encoder reranking (app/rerank.py)
3. Advanced JSON logging + request IDs
4. Filters (year, date range, court) & aggregations
  "raw_query": {"query": {"multi_match": {"query": "final search query", "fields": ["case_name^3.0", "full_text"]}}}
5. PageRank / authority scoring integration
6. Evaluation harness & quality metrics

## 🎯 Quick Start

### Using Docker (Recommended)

```bash
# Clone the repository
git clone https://github.com/rahulmirapala/legit-search.git
cd legit-search

# Set environment variables (optional)
export LLM_API_KEY=your_google_ai_studio_key

# Start all services
docker-compose up -d

# Create index with mappings
docker-compose exec backend python scripts/create_index.py

# Ingest documents (example)
docker-compose exec backend python scripts/1_pdf_to_jsonl.py /data/pdfs corpus.jsonl
docker-compose exec backend bash scripts/2_bulk_upload.sh corpus.jsonl legal_judgments

# Generate embeddings (if using semantic search)
docker-compose exec backend python scripts/add_embeddings.py
```

Access:
- Frontend: http://localhost:3000
- Backend API: http://localhost:8000
- API Docs: http://localhost:8000/docs
- Elasticsearch: http://localhost:9200

### Manual Setup

#### Backend
```bash
pip install -r requirements.txt
python scripts/create_index.py
python -m uvicorn app.main:app --reload
```

#### Frontend
```bash
cd frontend
npm install
npm start
```

## Ingestion Workflow
1. Convert PDFs to JSONL:
	```bash
	python scripts/1_pdf_to_jsonl.py input_folder output.jsonl
	```
2. (Optional) Split large JSONL:
	```bash
	python scripts/3_split_bulk_file.py output.jsonl 5000
	```
3. Bulk upload:
	```bash
	bash scripts/2_bulk_upload.sh output.jsonl index_name
	```

## � PDF Linking & Enrichment

Judgment documents can be heuristically linked to local PDF files for direct viewing. The backend exposes two kinds of PDF data per search hit:

```
pdf_candidates  // lightweight guesses derived at query time
pdf_url         // deterministic URL if `pdf_filename` stored in the document
```

### Mapping Requirement
Your Elasticsearch index mapping must include a `pdf_filename` keyword field (added in `mapping.json`). If the index predates this addition, re-create it or update the mapping:

```bash
curl -X PUT "$ES_HOST/$INDEX_NAME/_mapping" -H 'Content-Type: application/json' -d '{"properties":{"pdf_filename":{"type":"keyword"}}}'
```

### Enrichment Script
Run the enrichment script to populate `pdf_filename` and (optionally) `pdf_url` directly in documents:

```bash
# Dry-run (preview matches; no writes)
python scripts/enrich_pdf_links.py --index legit_search_index --pdf-root data/supreme_court_judgments --dry-run

# Commit updates with relaxed density threshold
python scripts/enrich_pdf_links.py --index legit_search_index --pdf-root data/supreme_court_judgments --min-density 0.3 --commit

# Force re-evaluate documents already having pdf_filename
python scripts/enrich_pdf_links.py --index legit_search_index --pdf-root data/supreme_court_judgments --force --commit
```

Key threshold flags:
- `--min-score` (default 2): Minimum overlapping token count.
- `--min-density` (default 0.5): overlap / token_count(case_name).
- Lower thresholds increase recall but may reduce precision.

### Verification
After committing, sample a few documents:

```bash
curl "$ES_HOST/$INDEX_NAME/_search?pretty" -H 'Content-Type: application/json' -d '{"size":5,"query":{"exists":{"field":"pdf_filename"}}}' | grep -i pdf_filename
```

### Frontend Behavior (if present)
When `pdf_url` is present, the UI can render an "Open PDF" button that loads `/pdfs/<year>/<filename>` directly. Without it, it may fall back to fuzzy candidate listing.

### Improving Accuracy
- Integrate citation metadata (e.g., SCC citation ↔ official filename) instead of pure token overlap.
- Use fuzzy token matching (RapidFuzz) with ratio thresholds.
- Manually curate exceptions (constitutional bench landmark cases) for guaranteed precision.

### Troubleshooting
| Symptom | Cause | Remedy |
|---------|-------|--------|
| Few enrichments | Thresholds too strict | Lower `--min-density` or `--min-score` |
| Wrong matches | Thresholds too lax | Increase thresholds; add `--force` after corrections |
| Slow run | Large index + all-year scan | Ensure `year` field populated; raise `--min-score` to prune |
| No pdf_url | File missing or year inferred wrong | Verify file path exists under `data/supreme_court_judgments/<year>` |


## �🔍 API Reference

### Search Endpoint
```
GET /search
```

**Parameters:**
- `q` (required): Search query
- `page` (default: 1): Page number
- `page_size` (default: 10, max: 100): Results per page
- `title_boost` (default: 3.0): Title field boost weight
- `include_highlights` (default: true): Include snippets
- `expand` (default: false): LLM query expansion
- `spell` (default: true): Spell correction
- `mode` (default: "bm25"): Search mode - "bm25", "hybrid", "semantic"
- `semantic_weight` (default: 0.3): Semantic score weight (hybrid mode)
- `rerank` (default: false): Apply cross-encoder reranking
- `year_from`, `year_to`: Year range filter
- `court`: Court name filter

**Response:**
```json
{
  "total_hits": 150,
  "page": 1,
  "page_size": 10,
  "results": [
    {
      "case_name": "XYZ v. State",
      "year": 2020,
      "score": 12.5,
      "highlights": ["...relevant <em>snippet</em>..."],
      "citation_id": "2020-SC-123"
    }
  ],
  "corrected_query": "corrected query",
  "expanded_terms": ["term1", "term2"],
  "final_query": "final search query"
}
```

Each search hit can additionally include:

```json
{
  "pdf_candidates": ["2017/puttaswamy_judgment.pdf", "2017/privacy_case.pdf"],
  "pdf_url": "/pdfs/2017/puttaswamy_judgment.pdf"
}
```

Field meanings:
- `pdf_candidates`: Heuristic file path candidates derived from local PDF repository (may contain false positives).
- `pdf_url`: Deterministic direct link served by backend if document was enriched with a matching `pdf_filename`.

### Other Endpoints
- `GET /health` - Health check
- `GET /metrics` - Prometheus metrics
- `GET /aggregations` - Facet counts (years, courts)
- `GET /stats` - Index document & store size statistics
- `GET /explain/{doc_id}` - Detailed term scoring explanation for a single document
- `GET /pdf/search?case_name=...&year=YYYY` - Returns array of fuzzy matched PDF filenames with scores
- `GET /pdf/link?case_name=...&year=YYYY` - Returns best single PDF match `{ path, score, density, url }` or 404
- `GET /pdf/file?path=YYYY/filename.pdf` - Streams the raw PDF file

## 🧪 Testing & Evaluation

### Run Tests
```bash
# All tests
pytest tests/ -v

# Unit tests only
pytest tests/ -v -m unit

# Integration tests
pytest tests/ -v -m integration

# With coverage
pytest tests/ --cov=app --cov-report=html
```

### Evaluate Retrieval Quality
```bash
python scripts/evaluate.py \
  --queries sample_queries.jsonl \
  --qrels sample_qrels.jsonl \
  --output results.json
```

Compares BM25, hybrid, semantic, and reranking across metrics:
- Precision@5, Precision@10
- Recall@10
- Mean Reciprocal Rank (MRR)
- NDCG@10

## 📦 Project Structure

```
legit-search/
├── app/
│   ├── main.py              # FastAPI application
│   ├── search.py            # Query builders
│   ├── semantic.py          # Embedding utilities
│   ├── rerank.py            # Cross-encoder reranking
│   ├── config.py            # Settings management
│   ├── schemas.py           # Pydantic models
│   ├── cache.py             # TTL cache
│   ├── llm.py               # LLM query expansion
│   ├── logging_config.py    # JSON logging setup
│   └── metrics.py           # Prometheus metrics
├── scripts/
│   ├── 1_pdf_to_jsonl.py    # PDF extraction
│   ├── 2_bulk_upload.sh     # ES bulk upload
│   ├── 3_split_bulk_file.py # Split large files
│   ├── enrich_pdf_links.py  # Heuristic enrichment of ES docs with pdf_filename/pdf_url
│   ├── create_index.py      # Index creation
│   ├── add_embeddings.py    # Generate embeddings
│   └── evaluate.py          # Evaluation harness
├── frontend/
│   ├── src/
│   │   ├── App.js           # Main component
│   │   ├── components/      # UI components
│   │   ├── api.js           # API client
│   │   └── index.css        # Styling
│   └── public/
├── tests/                   # Test suite
├── Dockerfile               # Backend container
├── Dockerfile.frontend      # Frontend container
├── docker-compose.yml       # Multi-service orchestration
└── .github/workflows/ci.yml # CI pipeline
```

## 🛠️ Development

### Code Quality
```bash
# Linting
flake8 app
black app
isort app

# Security scan
bandit -r app
safety check
```

### Environment Variables
```bash
ES_HOST=http://localhost:9200
INDEX_NAME=legal_judgments
LLM_API_KEY=<your-google-ai-studio-key>
EMBED_MODEL=sentence-transformers/all-MiniLM-L6-v2
RERANK_MODEL=cross-encoder/ms-marco-MiniLM-L-6-v2
```

## 🎓 Use Cases

- **Legal Research**: Search Supreme Court judgments by topic, citation, year
- **Academic Study**: Compare retrieval methods (BM25 vs semantic vs hybrid)
- **IR Experimentation**: Evaluate query expansion, reranking, filtering strategies
- **Demo/Portfolio**: Showcase full-stack IR system with modern ML techniques

## 📝 Citation

If you use this project, please cite:
```
@software{legit_search,
  author = {Your Name},
  title = {Legit Search: Hybrid Legal Information Retrieval System},
  year = {2024},
  url = {https://github.com/rahulmirapala/legit-search}
}
```

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## 📄 License

MIT

## ♿ Accessibility (Planned Enhancements)

To ensure inclusive usage, planned UI improvements include:
- Keyboard navigation for all interactive controls (search, pagination, PDF modal).
- ARIA roles on modal dialogs and result lists.
- Visible focus outlines (WCAG 2.1 AA) and high‑contrast toggle.
- Screen‑reader friendly labeling for action buttons (Explain, Save, Copy Citation, Open PDF).

Backend suggestions:
- Provide alt text / description metadata for judgments (e.g., bench strength, key issues) to support assistive summarization.
- Offer a plain‑text extraction endpoint for large‑scale TTS processing.

Contributions implementing these are welcome—open a PR referencing this section.

## 🌐 Live Search (Indian Kanoon) & Limitations

The UI includes a "Live Search" button that opens Indian Kanoon pre‑filtered to Supreme Court judgments (`doctypes:supremecourt`). This is an external, third‑party site not under this project's control. Important notes:

### Why You Sometimes See Cloudflare 500 Errors
- Indian Kanoon intermittently returns **HTTP 500** for search requests (observed via Cloudflare edge in New Delhi).
- These are upstream availability or rate‑limit issues; your browser and our app are functioning correctly.
- Repeated automated requests or rapid reloads can increase the likelihood of 5xx responses.

### How We Handle It
- Backend endpoint: `GET /live/status` performs a lightweight probe and caches for 30 seconds.
- Frontend displays a red banner when the live source is unstable (>=500 or fetch failure).
- We do **not** proxy or scrape aggressively to respect upstream resources.

### Recommended Workflow
1. Use local index (the normal Search button) for fast, reliable semantic + BM25 retrieval.
2. If you need the authoritative formatted judgment page, click Live Search once; if a 500 appears, wait 30–60 seconds and retry.
3. For intensive research, ingest judgments locally using the ingestion scripts instead of repeatedly hitting the external site.

### Fallback & Alternatives
- Supreme Court official portal (https://main.sci.gov.in/judgments) provides PDFs but less flexible search.
- You can build a cron ingestion pipeline to avoid reliance on live external search.

### Etiquette / Fair Use
- Avoid rapid scripted requests to external sites.
- Consider adding exponential backoff if you extend the live integration.

### Troubleshooting
| Symptom | Cause | Action |
|---------|-------|--------|
| 500 error page (Cloudflare) | Upstream transient failure | Retry later; rely on local index |
| Blank page/tab did not open | Browser blocked popups | Right‑click "Open link in new tab" |
| Slow external load | Network latency / CDN edge | Wait; do not refresh repeatedly |
| Local search works, live fails | External outage | Proceed with local results, schedule ingestion |

If persistent 500s occur for hours, prefer local ingestion and treat the external source as temporarily unavailable.
