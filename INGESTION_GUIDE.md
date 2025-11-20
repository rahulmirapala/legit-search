# Local Judgment Ingestion Guide

Due to Indian Kanoon's rate limiting (Cloudflare 500 errors), we recommend **manual download** followed by automated processing.

## 📋 Recommended Workflow

### Option A: Manual Download from Indian Kanoon (Reliable)

1. **Manually browse and download** judgments:
   - Visit: https://indiankanoon.org/search/?formInput=doctypes:supremecourt
   - Filter by year, topic, etc.
   - Click on individual cases
   - Copy the full text and save as `.txt` files

2. **Organize files** in this structure:
   ```
   data/supreme_court_judgments/
   ├── 2024/
   │   ├── Case_Name_1_on_15_January_2024.txt
   │   └── Case_Name_2_on_20_March_2024.txt
   ├── 2023/
   │   └── Case_Name_3_on_10_June_2023.txt
   ```

3. **Convert to JSONL**:
   ```bash
   python scripts/2_txt_to_jsonl.py --input data/supreme_court_judgments --output data/judgments.jsonl
   ```

4. **Upload to Elasticsearch**:
   ```bash
   bash scripts/2_bulk_upload.sh data/judgments.jsonl legal_judgments
   ```

5. **(Optional) Generate embeddings for semantic search**:
   ```bash
   python scripts/add_embeddings.py
   ```

### Option B: Supreme Court Official Portal (Authoritative)

1. Visit: https://main.sci.gov.in/judgments
2. Download PDFs using the official search
3. Save to `data/sc_pdfs/YYYY/` folders
4. Convert using the PDF script:
   ```bash
   python scripts/1_pdf_to_jsonl.py
   ```
5. Upload as above

### Option C: Scheduled Scraping (Advanced)

For **automated periodic ingestion**, you need:

1. **Install headless browser** (to handle JavaScript rendering):
   ```bash
   pip install playwright
   playwright install chromium
   ```

2. **Create a scheduled job** (cron) that:
   - Runs once daily/weekly
   - Uses Playwright to render Indian Kanoon pages
   - Extracts new judgments published since last run
   - Saves to `data/supreme_court_judgments/`
   - Runs conversion + upload pipeline

3. **Respect upstream**:
   - Add 5-10 second delays between requests
   - Limit to 50-100 judgments per run
   - Use User-Agent headers
   - Monitor for 429/500 responses and backoff

**Sample scheduled script** (example only - not production ready):
```python
# scripts/scheduled_ingest.py (EXAMPLE - requires Playwright)
from playwright.sync_api import sync_playwright
import time

def scrape_latest_judgments():
    with sync_playwright() as p:
        browser = p.chromium.launch()
        page = browser.new_page()
        page.goto("https://indiankanoon.org/search/?formInput=doctypes:supremecourt")
        # ... extract results, save files
        browser.close()
```

### Option D: Academic Datasets (Bulk)

Search for existing legal datasets:
- **Indian Legal Dataset** repositories on GitHub
- **Kaggle** legal datasets
- Academic research dataset releases
- Law school/university portals

These often provide cleaned JSON/CSV with thousands of cases.

## 🚫 Why Automated Download Fails

The `scripts/download_indiankanoon.py` script encounters:
- **Cloudflare 500 errors**: Rate limiting / anti-bot protection
- **Dynamic content**: JavaScript-rendered results require headless browser
- **IP blocking**: Repeated requests from same IP get throttled

**Not recommended** for production without:
- Rotating proxies
- Playwright/Puppeteer integration
- Exponential backoff
- Legal review of scraping compliance

## ✅ Recommended Approach for This Project

**For demonstration/portfolio**:
- Manually download 20-50 representative cases
- Use the conversion + upload pipeline
- Showcase search quality with curated dataset

**For production**:
- Partner with legal data providers
- Use official APIs when available
- Scheduled ingestion with proper rate limiting
- Cache aggressively to reduce upstream dependency

## 📝 File Format Examples

### .txt file format (from Indian Kanoon):
```
Case: Union of India vs XYZ
Citation: (2024) 1 SCC 123
Year: 2024
Source: https://indiankanoon.org/doc/12345/

================================================================================

1. This is the judgment text...
2. Facts of the case...
```

### Companion _meta.json file (auto-saved by downloader):
```json
{
  "case_name": "Union of India vs XYZ",
  "citation_id": "(2024) 1 SCC 123",
  "year": 2024,
  "judgment_date": "15_January_2024",
  "source_url": "https://indiankanoon.org/doc/12345/",
  "filename": "Union_of_India_vs_XYZ_on_15_January_2024.txt"
}
```

## 🔧 Troubleshooting

| Problem | Solution |
|---------|----------|
| Download script returns 500 | Use manual download (Option A) |
| Need thousands of cases | Use academic datasets (Option D) |
| Want latest judgments daily | Implement scheduled scraping with Playwright (Option C) |
| PDFs not parsing correctly | Check PyMuPDF version, ensure text-based PDFs (not scanned images) |
| Elasticsearch upload fails | Check ES running: `curl localhost:9200/_cluster/health` |
| No embeddings generated | Ensure sentence-transformers installed in Chicken env |

## 📊 Sample Dataset

We've included 8 sample cases in `data/sample_cases.json` to get started immediately:
```bash
# Load sample data
python -c "import json; import requests; 
samples = json.load(open('data/sample_cases.json')); 
for doc in samples:
    requests.post('http://localhost:9200/legal_judgments/_doc', json=doc)"
```

Then test: http://localhost:3000 and search for "privacy" or "fundamental rights"

---

## Next Steps

1. Choose your ingestion method (A, B, C, or D)
2. Prepare your dataset
3. Run conversion: `python scripts/2_txt_to_jsonl.py`
4. Upload: `bash scripts/2_bulk_upload.sh data/judgments.jsonl legal_judgments`
5. Enjoy fast local search at http://localhost:3000
