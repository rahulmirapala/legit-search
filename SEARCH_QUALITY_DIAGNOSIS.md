## Search Engine Quality Issues - Diagnosis & Solutions

### 🔍 **PROBLEMS IDENTIFIED:**

1. **CRITICAL: Relevance Failure (72.7% of queries)**
   - Top results don't contain query terms
   - Wrong documents being ranked highest
   - **Root cause**: Query is matching full_text of many docs, but boosting isn't working properly

2. **Limited Dataset**
   - Only 52 documents in index
   - All from 2017
   - Missing landmark Supreme Court cases

3. **Stemming Over-Aggressiveness**
   - Using kstem + possessive stemmer
   - Could be over-matching irrelevant terms

---

## 🔧 **SOLUTION PLAN**

### Phase 1: Fix Critical Relevance Issues (DO THIS FIRST) ⚡

#### A. Improve Field Boosting Strategy
**Problem**: case_name boost=3.0 isn't strong enough when full_text is huge

**Solution**:
```python
# In search.py - Increase case_name boost dramatically
fields = [
    f"case_name^{title_boost * 5}",  # Was 3.0, now 15.0 default
    f"case_name.shingle^{title_boost * 3}",
    "full_text",  # Lower priority
    "full_text.shingle^0.5"
]
```

#### B. Add Minimum Should Match
**Problem**: OR queries match too loosely

**Solution**:
```python
mm["minimum_should_match"] = "75%"  # Require 75% of terms to match
```

#### C. Use Cross-Fields Multi-Match
**Problem**: best_fields doesn't coordinate across fields well

**Solution**:
```python
mm["type"] = "cross_fields"  # Instead of best_fields
```

---

### Phase 2: Better Data Quality

#### D. Ingest More Documents
You have `/data/supreme_court_judgments/` folders from 1950-2025!

**Action**:
```bash
# Run your ingestion pipeline on ALL years, not just 2017
cd /home/chakri/Documents/Projects/legit-search
python scripts/1_pdf_to_jsonl.py  # Convert all PDFs
./scripts/2_bulk_upload.sh  # Upload to Elasticsearch
```

---

### Phase 3: Index Configuration Improvements

#### E. Add More Legal Synonyms
Your current synonyms are too limited.

**Action**: Expand `mapping.json` synonyms:
```json
"legal_synonyms": {
  "type": "synonym_graph",
  "lenient": true,
  "synonyms": [
    // Existing ones...
    "PIL, public interest litigation, writ petition",
    "Article 21, right to life, personal liberty",
    "Article 14, equality, equal protection",
    "Article 32, constitutional remedy, writ jurisdiction",
    "Section 498A, dowry harassment, matrimonial cruelty",
    "natural justice, audi alteram partem, fair hearing",
    "judicial review, writ, certiorari, mandamus",
    "Kesavananda Bharati, basic structure doctrine",
    "Vishaka, sexual harassment, workplace harassment"
  ]
}
```

#### F. Add Citation Field
**Problem**: Citations like "AIR 1973 SC 1461" need exact matching

**Action**: Add to `mapping.json`:
```json
"citations": {
  "type": "text",
  "analyzer": "keyword",
  "fields": {
    "exact": {"type": "keyword"}
  }
}
```

---

## 🚀 **QUICK WINS (Implement Now)**

### 1. Update search.py with better field config

```python
# Better field configuration for balanced search
fields = [
    f"case_name^{title_boost * 4}",  # Stronger boost
    f"case_name.exact^{title_boost * 6}",  # Add exact match
    f"case_name.shingle^{title_boost * 2}",
    "full_text^0.8",  # Lower full_text priority
    "full_text.shingle^0.5"
]

# Add minimum should match
mm["minimum_should_match"] = "2<75%"  # 2 terms=100%, 3+=75%
```

### 2. Add case_name exact matching

Update `mapping.json`:
```json
"case_name": {
  "type": "text",
  "analyzer": "legal_text_analyzer",
  "search_analyzer": "legal_text_search",
  "fields": {
    "raw": {"type": "keyword", "ignore_above": 256},
    "exact": {"type": "text", "analyzer": "whitespace"},  // ADD THIS
    "ngram": {...},
    "shingle": {...}
  }
}
```

### 3. Reduce stopword filtering

Current stopwords are removing important legal terms. Update `mapping.json`:
```json
"legal_stop": {
  "type": "stop",
  "stopwords": ["a", "an", "the", "of"]  // Keep it minimal for legal text
}
```

---

## 📊 **Expected Improvements**

After implementing Phase 1:
- **Relevance**: 90%+ queries should return relevant top result
- **Case name searches**: Direct hits for exact names
- **Concept searches**: Better term matching

After ingesting full dataset:
- **Coverage**: All landmark cases available
- **Search variety**: Historical + recent cases

---

## 🎯 **Priority Order**

1. **NOW**: Fix field boosting in search.py (5 min)
2. **TODAY**: Reduce stopwords, add exact field (15 min)
3. **THIS WEEK**: Ingest full dataset (1-2 hours)
4. **LATER**: Add citation field, expand synonyms

---

## Need help implementing any of these?
Let me know which fix you want to start with and I'll make the changes!
