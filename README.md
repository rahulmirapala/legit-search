# ⚖️ Legit Search: Advanced Legal Information Retrieval System

## Project Overview

**Legit Search** is a powerful Information Retrieval (IR) system designed to provide fast, accurate, and relevant search capabilities over a large corpus of **Indian Supreme Court judgments (1950-2024)**.

The system is built on a modern **FastAPI** backend and a high-performance **Elasticsearch** engine, utilizing a meticulous data pipeline to ensure maximum search precision and user control over relevance.

### Core Features
* **Structured Metadata:** Accurate extraction and indexing of **Case Name**, **Judgment Date**, **Citation ID**, and **Year** directly from complex PDF files and filenames.
* **Advanced Relevance Scoring (BM25):** Utilizes the modern BM25 algorithm for precise keyword ranking, with options for recency-biased scoring.
* **Dynamic Boosting:** Allows the user to dynamically adjust the **weight** of search terms in the **Case Name** (title) versus the **Full Text**.
* **Boolean Query Support:** Correctly interprets logical search operators (`AND`, `OR`, `NOT`) for highly specific legal queries.
* **Dynamic Retrieval Size:** Allows the user to specify the exact number of documents to retrieve per query.
* **Snippets & Highlights:** Returns highlighted text snippets demonstrating exactly why a document was retrieved.

---

## 🛠️ Technology Stack

| Component | Technology | Purpose |
| :--- | :--- | :--- |
| **Data Processing** | Python, **PyMuPDF**, Regex | PDF text extraction and metadata parsing. |
| **Search Engine** | **Elasticsearch (v7.17)** | High-performance, scalable inverted index. |
| **Backend API** | **FastAPI** | High-speed, modern, asynchronous web framework. |
| **Linguistic Analysis** | NLTK, Custom Elasticsearch Analyzer | Stop word removal, stemming, and tokenization. |
| **Containerization** | Docker | Hosts the Elasticsearch service. |

---

## 🚀 Setup and Indexing Workflow

### Prerequisites

1.  **Docker Desktop:** Must be installed and running.
2.  **Python 3.8+:** Installed.
3.  **Kaggle Dataset:** Unzipped into `data/supreme_court_judgments/`.

### Phase 1: Preparation

1.  **Install Dependencies:** Run this from the project root (`legit_search/`).
    ```bash
    pip install -r requirements.txt
    ```

2.  **Start Services:** Start your Elasticsearch container (named `legit-search`).
    ```bash
    docker start legit-search
    ```

3.  **Create Index Blueprint (The Schema):** Send the `template.json` to the running Elasticsearch instance.
    ```powershell
    curl -ContentType "application/json" -Method PUT -Uri http://localhost:9200/legit_search_index -InFile "template.json"
    ```

### Phase 2: Data Processing & Upload (The 1-Command Index)

This process runs your two Python scripts and your PowerShell script to process, split, and upload all data.

1.  **Navigate to Scripts:**
    ```bash
    cd scripts
    ```

2.  **Process and Split Data:** Run the first two processing steps (PDF extraction and file splitting).
    ```bash
    python 1_pdf_to_jsonl.py
    python 3_split_bulk_file.py
    ```

3.  **Upload All Parts:** Execute the single PowerShell script to upload all chunks to Elasticsearch.
    ```powershell
    .\4_upload_all_parts.ps1
    ```

---

## 💻 Running the Application

1.  **Navigate to Root:**
    ```bash
    cd ..
    ```

2.  **Start the FastAPI Server:**
    ```bash
    uvicorn app.main:app --reload
    ```
    *Wait for the `Successfully connected to Elasticsearch.` message.*

3.  **Access the API Documentation:** Open your browser to the interactive API endpoint.
    ```
    [http://127.0.0.1:8000/docs](http://127.0.0.1:8000/docs)
    ```

## API Endpoint Usage (`/search`)

The primary endpoint allows precise control over search relevance and scoring strategies.

| Parameter | Type | Default | Description |
| :--- | :--- | :--- | :--- |
| **`q`** | `string` | *Required* | The search query (e.g., `drunk AND drive`). |
| **`title_boost`** | `float` | `3.0` | **Scoring Control:** Weights the importance of matches in the `case_name` field. |
| **`size`** | `integer` | `10` | **Retrieval Size:** The number of documents to return in the result list. |
| **`score_mode`** | `enum` | `best_match` | **Ranking Strategy:** Toggles between `best_match` (BM25) and `recent_biased` (BM25 + Date Decay). |

### Example Queries:

| Query String | Logic Applied |
| :--- | :--- |
| `crime AND rape` | **High Precision:** Requires both terms to be present in the document. |
| `article 21` | **Relevance:** Searches for the phrase "article 21". |
| `drunk drive` | **Phrase Matching:** Since the default operator is AND, this finds highly relevant drunk driving cases. |
| `habeus corpus NOT appeal` | **Exclusion:** Finds documents about the writ but excludes all appeal cases. |