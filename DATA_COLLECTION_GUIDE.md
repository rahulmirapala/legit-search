# Guide: Getting Indian Supreme Court Judgments Data

## Overview
Your project has scripts to process PDF judgments and load them into Elasticsearch. Here are the methods to obtain the data.

---

## 🔥 **Option 1: Indian Kanoon API (Recommended)**

**Indian Kanoon** provides free access to Indian Supreme Court judgments.

### Steps:
```bash
# 1. Install required packages
pip install requests beautifulsoup4

# 2. Create a data collection script
```

### Sample Script - Download from Indian Kanoon:
```python
# scripts/download_indiankanoon.py
import requests
import os
import time
from bs4 import BeautifulSoup

def download_judgments(year_start=2020, year_end=2024, max_per_year=100):
    """Download Supreme Court judgments from Indian Kanoon."""
    base_url = "https://indiankanoon.org"
    search_url = f"{base_url}/search/?formInput=doctypes:supremecourt"
    
    data_dir = "data/supreme_court_judgments"
    os.makedirs(data_dir, exist_ok=True)
    
    for year in range(year_start, year_end + 1):
        year_dir = os.path.join(data_dir, str(year))
        os.makedirs(year_dir, exist_ok=True)
        
        print(f"Downloading year {year}...")
        
        # Search for cases from this year
        url = f"{search_url}%20year:{year}&pagenum=0"
        
        try:
            response = requests.get(url)
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # Find case links
            case_links = soup.find_all('a', class_='cite_tag')[:max_per_year]
            
            for i, link in enumerate(case_links):
                case_url = base_url + link.get('href')
                case_name = link.text.strip()
                
                # Sanitize filename
                filename = f"{case_name.replace('/', '_')[:100]}.html"
                filepath = os.path.join(year_dir, filename)
                
                # Download case content
                case_response = requests.get(case_url)
                with open(filepath, 'w', encoding='utf-8') as f:
                    f.write(case_response.text)
                
                print(f"  Downloaded {i+1}/{len(case_links)}: {case_name}")
                time.sleep(1)  # Be respectful to the server
                
        except Exception as e:
            print(f"Error downloading year {year}: {e}")
            continue

if __name__ == "__main__":
    download_judgments(year_start=2020, year_end=2024, max_per_year=50)
```

---

## 📚 **Option 2: Judgments.ecourts.gov.in**

Official eCourts services portal.

### Manual Download:
1. Visit: https://judgments.ecourts.gov.in/
2. Select "Supreme Court" from the dropdown
3. Choose year range
4. Download judgments as PDFs
5. Organize in folder structure:
   ```
   data/supreme_court_judgments/
   ├── 2020/
   │   ├── case1.pdf
   │   └── case2.pdf
   ├── 2021/
   └── 2022/
   ```

---

## 🏛️ **Option 3: Supreme Court of India Official Website**

### Steps:
1. Visit: https://main.sci.gov.in/judgments
2. Browse by date/subject
3. Download PDFs manually
4. Save in year-based folders

---

## 🔍 **Option 4: Pre-processed Datasets**

### Kaggle Datasets:
- Search "Indian Supreme Court" on Kaggle
- Example: https://www.kaggle.com/datasets/
- Download CSV/JSON files
- Convert to your format

### GitHub Repositories:
- Search for "Indian legal judgments" on GitHub
- Many researchers share preprocessed datasets
- Clone and use directly

---

## 📄 **Your Project's Expected Format**

Based on your `1_pdf_to_jsonl.py` script, PDFs should be named:
```
Case_Name_vs_Respondent_on_19_May_1950.PDF
```

### Folder Structure:
```
data/
└── supreme_court_judgments/
    ├── 1950/
    │   ├── A_K_Gopalan_vs_State_on_19_May_1950.PDF
    │   └── ...
    ├── 1951/
    ├── 1952/
    └── ...
```

---

## 🚀 **Processing Pipeline (Once You Have PDFs)**

### Step 1: Organize PDFs
```bash
mkdir -p data/supreme_court_judgments/{1950..2024}
# Move PDFs to respective year folders
```

### Step 2: Convert PDFs to JSONL
```bash
cd /home/chakri/Documents/Projects/legit-search
PYTHONPATH=/home/chakri/Documents/Projects/legit-search \
/home/chakri/Documents/Projects/Chicken-Disease-Classification/chicken/bin/python \
scripts/1_pdf_to_jsonl.py
```

This creates: `data/bulk_index.jsonl`

### Step 3: Upload to Elasticsearch
```bash
cd scripts
bash 2_bulk_upload.sh
```

### Step 4: (Optional) Add Semantic Embeddings
```bash
PYTHONPATH=/home/chakri/Documents/Projects/legit-search \
/home/chakri/Documents/Projects/Chicken-Disease-Classification/chicken/bin/python \
scripts/add_embeddings.py
```

---

## 🎯 **Quick Test with Sample Data**

If you want to test the pipeline first:

### Create Test PDFs:
```python
# test_create_pdfs.py
from fpdf import FPDF
import os

os.makedirs('data/supreme_court_judgments/2020', exist_ok=True)

# Create sample PDF
pdf = FPDF()
pdf.add_page()
pdf.set_font("Arial", size=12)
pdf.multi_cell(0, 10, txt="Sample Supreme Court Judgment\n\nEquivalent citations: 2020 AIR 123\n\nThis is test content.")
pdf.output('data/supreme_court_judgments/2020/Test_Case_vs_State_on_15_Jan_2020.PDF')
print("Sample PDF created!")
```

---

## 📦 **Recommended Approach for You**

### For Quick Testing (Now):
1. Keep using the sample data I already loaded (8 cases)
2. Test all features with this data
3. Perfect your search/reranking/UI

### For Production Data (Later):
1. **Start Small**: Download 100-200 recent judgments (2020-2024) from Indian Kanoon
2. **Process**: Run the PDF → JSONL → Elasticsearch pipeline
3. **Validate**: Check search quality, tune parameters
4. **Scale Up**: Once satisfied, download more years (1950-2024)

### Recommended Script:
```bash
# Install dependencies
pip install requests beautifulsoup4 pypdf2

# Download recent cases (modify year range as needed)
python scripts/download_indiankanoon.py

# Process PDFs
python scripts/1_pdf_to_jsonl.py

# Upload to Elasticsearch
bash scripts/2_bulk_upload.sh

# Add embeddings for semantic search
python scripts/add_embeddings.py
```

---

## ⚠️ **Important Notes**

1. **Legal Compliance**: Respect website terms of service when scraping
2. **Rate Limiting**: Add delays between requests (1-2 seconds)
3. **Storage**: 10,000 judgments ≈ 5-10 GB (PDFs + index)
4. **Processing Time**: 10,000 PDFs → ~2-4 hours on average hardware
5. **Embeddings**: Semantic embeddings for 10k docs → ~6-8 hours (GPU recommended)

---

## 🆘 **Need Help?**

If you want me to:
1. Write a complete downloader script for a specific source
2. Create a data validation script
3. Set up automated data collection
4. Handle specific PDF formats

Just let me know which data source you prefer!

---

## 📊 **Current Status**

- ✅ Index created: `legit_search_index`
- ✅ Sample data: 8 landmark cases loaded
- ✅ Search working: Try "privacy", "fundamental rights"
- ⏳ Production data: Ready to ingest when you have PDFs

**Next Step**: Choose a data source above and let me know if you need help with the download script!
