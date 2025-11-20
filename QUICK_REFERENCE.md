# Quick Reference Guide - Legit Search

## 🚀 Common Commands

### Local Development
```bash
# Start backend
python -m uvicorn app.main:app --reload

# Start frontend
cd frontend && npm start

# Run tests
pytest tests/ -v
pytest tests/ -m unit --cov=app
```

### Docker
```bash
# Start all services
docker-compose up -d

# View logs
docker-compose logs -f backend

# Stop services
docker-compose down

# Rebuild after changes
docker-compose up -d --build
```

### Ingestion Pipeline
```bash
# 1. Create index
python scripts/create_index.py

# 2. Extract PDFs to JSONL
python scripts/1_pdf_to_jsonl.py /path/to/pdfs output.jsonl

# 3. Split large files (optional)
python scripts/3_split_bulk_file.py output.jsonl 5000

# 4. Bulk upload
bash scripts/2_bulk_upload.sh output.jsonl legal_judgments

# 5. Generate embeddings (for semantic search)
python scripts/add_embeddings.py
```

## 🔍 Search Examples

### Basic Search
```bash
curl "http://localhost:8000/search?q=fundamental%20rights"
```

### With Filters
```bash
curl "http://localhost:8000/search?q=privacy&year_from=2015&year_to=2020&court=Supreme%20Court"
```

### Hybrid Search
```bash
curl "http://localhost:8000/search?q=judicial%20review&mode=hybrid&semantic_weight=0.4"
```

### With Reranking
```bash
curl "http://localhost:8000/search?q=constitutional%20law&rerank=true"
```

### With Expansion
```bash
curl "http://localhost:8000/search?q=free%20speech&expand=true"
```

### All Features Combined
```bash
curl "http://localhost:8000/search?q=privacy&mode=hybrid&rerank=true&expand=true&year_from=2010&page_size=20"
```

## 📊 Monitoring

### Health Check
```bash
curl http://localhost:8000/health
```

### Metrics
```bash
curl http://localhost:8000/metrics
```

### Aggregations
```bash
curl http://localhost:8000/aggregations
```

## 🧪 Testing & Evaluation

### Run All Tests
```bash
pytest tests/ -v
```

### Unit Tests Only
```bash
pytest tests/ -v -m unit
```

### Integration Tests
```bash
pytest tests/ -v -m integration
```

### Coverage Report
```bash
pytest tests/ --cov=app --cov-report=html
open htmlcov/index.html
```

### Evaluate Retrieval Quality
```bash
python scripts/evaluate.py \
  --queries sample_queries.jsonl \
  --qrels sample_qrels.jsonl \
  --output results.json
```

## 🔧 Configuration

### Environment Variables
```bash
# Required
export ES_HOST=http://localhost:9200
export INDEX_NAME=legal_judgments

# Optional
export LLM_API_KEY=your_google_ai_studio_key
export EMBED_MODEL=sentence-transformers/all-MiniLM-L6-v2
export RERANK_MODEL=cross-encoder/ms-marco-MiniLM-L-6-v2
```

### .env File (for docker-compose)
```env
ES_HOST=http://elasticsearch:9200
INDEX_NAME=legal_judgments
LLM_API_KEY=your_api_key_here
```

## 🛠️ Code Quality

### Format Code
```bash
black app
isort app
```

### Lint
```bash
flake8 app
```

### Security Scan
```bash
bandit -r app
safety check
```

## 🐛 Troubleshooting

### Elasticsearch Connection Issues
```bash
# Check if ES is running
curl http://localhost:9200

# Check ES logs
docker-compose logs elasticsearch

# Restart ES
docker-compose restart elasticsearch
```

### Backend Issues
```bash
# Check backend logs
docker-compose logs backend

# Restart backend
docker-compose restart backend

# Check health
curl http://localhost:8000/health
```

### Frontend Issues
```bash
# Check build logs
cd frontend && npm run build

# Clear cache
rm -rf frontend/node_modules frontend/build
cd frontend && npm install && npm start
```

### Embedding/Reranking Not Working
```bash
# Install dependencies
pip install sentence-transformers

# Check model loading
python -c "from app.semantic import is_available; print(is_available())"
python -c "from app.rerank import is_available; print(is_available())"
```

## 📦 Deployment Checklist

- [ ] Set environment variables
- [ ] Run tests: `pytest tests/ -v`
- [ ] Build Docker images: `docker-compose build`
- [ ] Create ES index: `python scripts/create_index.py`
- [ ] Ingest documents
- [ ] Generate embeddings (if using semantic search)
- [ ] Test all endpoints
- [ ] Check logs are structured JSON
- [ ] Verify metrics endpoint
- [ ] Test frontend UI
- [ ] Run security scans
- [ ] Set up monitoring/alerting
- [ ] Configure backups for ES data volume

## 🎯 Performance Tuning

### Backend
- Adjust cache TTL in `app/cache.py`
- Tune ES connection pool in `app/main.py`
- Optimize page_size limits
- Enable/disable features based on load

### Elasticsearch
- Adjust heap size: `ES_JAVA_OPTS=-Xms2g -Xmx2g`
- Tune refresh_interval for bulk indexing
- Configure replicas for high availability
- Use index aliases for zero-downtime updates

### Frontend
- Enable CDN for static assets
- Configure Nginx caching
- Optimize bundle size
- Lazy load components

## 📚 Resources

- FastAPI Docs: https://fastapi.tiangolo.com/
- Elasticsearch Guide: https://www.elastic.co/guide/
- Sentence-Transformers: https://www.sbert.net/
- React Docs: https://react.dev/
- Prometheus Metrics: https://prometheus.io/

---

**Need Help?** Check `IMPLEMENTATION_SUMMARY.md` for detailed feature documentation.
