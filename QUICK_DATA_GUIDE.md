# 🎯 Quick Start: Getting Supreme Court Data

## Current Status
- ✅ **System Running**: Backend (port 8000) + Frontend (port 3000) + Elasticsearch (port 9200)
- ✅ **Sample Data**: 8 landmark cases already loaded for testing
- ⏳ **Production Data**: Ready to ingest real Supreme Court judgments

---

## 🚀 Three Ways to Get Data

### Option 1: Use Indian Kanoon (Recommended - Automated)

**Download recent judgments automatically:**

```bash
cd /home/chakri/Documents/Projects/legit-search

# Install required packages
/home/chakri/Documents/Projects/Chicken-Disease-Classification/chicken/bin/python -m pip install \
    requests beautifulsoup4 --trusted-host pypi.org --trusted-host files.pythonhosted.org

# Download 50 recent cases per year (2022-2024)
/home/chakri/Documents/Projects/Chicken-Disease-Classification/chicken/bin/python \
    scripts/download_indiankanoon.py \
    --year-start 2022 \
    --year-end 2024 \
    --max-per-year 50
```

**Or use the interactive pipeline:**
```bash
bash scripts/quick_ingest.sh
```

This will:
1. Download judgments from Indian Kanoon
2. Convert to JSONL format
3. Upload to Elasticsearch
4. (Optional) Generate semantic embeddings

---

### Option 2: Manual Download from eCourts

1. Visit: https://judgments.ecourts.gov.in/
2. Select "Supreme Court"
3. Choose date range
4. Download PDFs
5. Organize in folders:
   ```
   data/supreme_court_judgments/
   ├── 2020/
   │   └── case1.pdf
   ├── 2021/
   └── 2022/
   ```
6. Run processing pipeline:
   ```bash
   PYTHONPATH=/home/chakri/Documents/Projects/legit-search \
   /home/chakri/Documents/Projects/Chicken-Disease-Classification/chicken/bin/python \
       scripts/1_pdf_to_jsonl.py
   
   bash scripts/2_bulk_upload.sh
   ```

---

### Option 3: Keep Using Sample Data (For Testing)

The system already has 8 cases loaded. Perfect for:
- Testing search features
- Trying different modes (BM25, semantic, hybrid)
- Developing UI features
- Performance tuning

**Sample searches that work now:**
- `privacy` → 2 results
- `fundamental rights` → 6 results
- `harassment` → Vishaka guidelines
- `reservation` → Mandal Commission
- `basic structure` → Constitutional cases

---

## 📊 Data Statistics

### Current Sample Data
- **Cases**: 8 landmark Supreme Court judgments
- **Years**: 1973-2018
- **Size**: ~50 KB
- **Coverage**: Constitutional law, fundamental rights

### Production Data (When Downloaded)
- **100 recent cases**: ~50-100 MB
- **1000 cases**: ~500 MB - 1 GB
- **10,000 cases**: ~5-10 GB
- **Processing time**: ~1-2 minutes per 100 cases

---

## 🔄 Data Pipeline

```
Download         Process          Upload           Search
--------        ---------        --------        ---------
PDFs/TXT   →    JSONL      →     ES Index   →    Your App
(Indian         (metadata         (full-text      (React UI)
 Kanoon)         extraction)       search)
```

### Full Pipeline Commands:

```bash
# 1. Download (choose one method above)
python scripts/download_indiankanoon.py

# 2. Process to JSONL
PYTHONPATH=/home/chakri/Documents/Projects/legit-search \
/home/chakri/Documents/Projects/Chicken-Disease-Classification/chicken/bin/python \
    scripts/1_pdf_to_jsonl.py

# 3. Upload to Elasticsearch
bash scripts/2_bulk_upload.sh

# 4. (Optional) Add semantic embeddings
PYTHONPATH=/home/chakri/Documents/Projects/legit-search \
/home/chakri/Documents/Projects/Chicken-Disease-Classification/chicken/bin/python \
    scripts/add_embeddings.py
```

---

## 🧪 Verify Data

After uploading, check your data:

```bash
# Count documents in index
curl -sS 'http://localhost:9200/legit_search_index/_count' | python3 -m json.tool

# Get sample document
curl -sS 'http://localhost:9200/legit_search_index/_search?size=1' | python3 -m json.tool

# Search via API
curl -sS 'http://localhost:8000/search?q=test&page_size=5'

# Open frontend
google-chrome http://localhost:3000  # or your browser
```

---

## 📂 Data Directory Structure

```
legit-search/
├── data/
│   ├── supreme_court_judgments/    # Downloaded cases organized by year
│   │   ├── 2020/
│   │   ├── 2021/
│   │   └── 2022/
│   └── bulk_index.jsonl            # Processed data ready for ES
├── scripts/
│   ├── download_indiankanoon.py    # Automated downloader
│   ├── 1_pdf_to_jsonl.py          # PDF processor
│   ├── 2_bulk_upload.sh           # ES uploader
│   ├── add_embeddings.py          # Semantic embeddings
│   └── quick_ingest.sh            # Full pipeline
└── DATA_COLLECTION_GUIDE.md       # Detailed guide
```

---

## ⚡ Quick Commands

### Start Everything
```bash
# Backend (if not running)
cd /home/chakri/Documents/Projects/legit-search
/home/chakri/Documents/Projects/Chicken-Disease-Classification/chicken/bin/python \
    -m uvicorn app.main:app --host 0.0.0.0 --port 8000 &

# Frontend (if not running)
cd frontend && npm start &

# Elasticsearch (if not running)
docker start elasticsearch-legit
```

### Download 100 Recent Cases (Quick Test)
```bash
/home/chakri/Documents/Projects/Chicken-Disease-Classification/chicken/bin/python \
    scripts/download_indiankanoon.py \
    --year-start 2023 \
    --year-end 2024 \
    --max-per-year 50
```

### Clear and Reload Data
```bash
# Delete old data
curl -XDELETE 'http://localhost:9200/legit_search_index'

# Recreate index
PYTHONPATH=/home/chakri/Documents/Projects/legit-search \
/home/chakri/Documents/Projects/Chicken-Disease-Classification/chicken/bin/python \
    scripts/create_index.py

# Re-upload
bash scripts/2_bulk_upload.sh
```

---

## 📖 Next Steps

1. **For Testing Now**: Use the existing 8 sample cases
2. **For Small Production**: Download 100-200 recent cases (2022-2024)
3. **For Full Production**: Download 1000+ cases across multiple years
4. **For Semantic Search**: Run `add_embeddings.py` after upload (requires time)

---

## 🆘 Need Help?

**Common Issues:**

1. **"Module not found"** → Use PYTHONPATH as shown above
2. **"Connection refused"** → Check Elasticsearch is running: `docker ps`
3. **"Download failed"** → Check internet connection, retry with delays
4. **"Out of memory"** → Reduce `max_per_year` or process in batches

**Want me to:**
- Write a custom scraper for a specific website?
- Help with specific PDF formats?
- Optimize the data pipeline?
- Add data validation/cleaning?

Just ask! 🚀

---

**Current Services:**
- Frontend: http://localhost:3000 ✅
- Backend: http://localhost:8000 ✅
- Elasticsearch: http://localhost:9200 ✅
