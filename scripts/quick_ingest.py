import os
import re
import fitz  # PyMuPDF
import json
from datetime import datetime
import sys

# --- Utility Functions ---

def decontracted(phrase):
    phrase = re.sub(r"won\'t", "will not", phrase)
    phrase = re.sub(r"can\'t", "can not", phrase)
    phrase = re.sub(r"n\'t", " not", phrase)
    phrase = re.sub(r"\'re", " are", phrase)
    phrase = re.sub(r"\'s", " is", phrase)
    phrase = re.sub(r"\'d", " would", phrase)
    phrase = re.sub(r"\'ll", " will", phrase)
    phrase = re.sub(r"\'t", " not", phrase)
    phrase = re.sub(r"\'ve", " have", phrase)
    phrase = re.sub(r"\'m", " am", phrase)
    return phrase

def clean_text(text):
    text = decontracted(text)
    text = text.replace('\r', ' ').replace('\n', ' ')
    text = re.sub(r'\s+', ' ', text)
    return text

def parse_date_from_filename(date_str):
    try:
        dt = datetime.strptime(date_str, '%d_%B_%Y')
        return dt.strftime('%Y-%m-%d')
    except ValueError:
        return None

def extract_metadata_from_filename(filename):
    case_name = "Unknown Case"
    judgment_date = None
    name_part, ext = os.path.splitext(filename)
    parts = name_part.split('_on_')
    if len(parts) >= 2:
        case_name = parts[0].replace('_', ' ').strip()
        date_part_raw = parts[1]
        date_match = re.search(r'(\d{1,2}_[A-Za-z]+_\d{4})', date_part_raw)
        if date_match:
            judgment_date = parse_date_from_filename(date_match.group(1))
    return case_name, judgment_date

def extract_citation_from_text(text):
    citation_match = re.search(r'Equivalent citations:\s*(.*?)(?=\n)', text, re.IGNORECASE)
    if citation_match:
        return citation_match.group(1).strip()
    scc_match = re.search(r'(\(\d{4}\)\s+\d+\s+SCC\s+\d+)', text)
    if scc_match:
        return scc_match.group(1)
    return "Unknown Citation"

def main():
    # Hardcoded for quick ingestion of 2017
    root_directory = 'data/supreme_court_judgments'
    output_file = 'data/quick_bulk.jsonl'
    target_year = '2017'
    limit = 50

    print(f"Starting quick ingestion for year {target_year}. Output: {output_file}")
    
    doc_count = 0
    with open(output_file, 'w', encoding='utf-8') as f:
        year_path = os.path.join(root_directory, target_year)
        if os.path.isdir(year_path):
            print(f"--- Processing folder: {target_year} ---")
            files = [f for f in os.listdir(year_path) if f.lower().endswith(".pdf")]
            # Sort to be deterministic
            files.sort()
            
            for filename in files:
                if doc_count >= limit:
                    break
                
                filepath = os.path.join(year_path, filename)
                try:
                    case_name, judgment_date = extract_metadata_from_filename(filename)
                    doc = fitz.open(filepath)
                    full_text = ""
                    for page in doc:
                        full_text += page.get_text()
                    doc.close()
                    citation = extract_citation_from_text(full_text)
                    clean_text_content = clean_text(full_text)
                    
                    # Add pdf_filename directly here since we know it!
                    doc_data = {
                        "case_name": case_name,
                        "judgment_date": judgment_date,
                        "citation_id": citation,
                        "full_text": clean_text_content,
                        "year": int(target_year),
                        "court": "Supreme Court of India",
                        "pdf_filename": filename  # Deterministic link!
                    }
                    
                    f.write(json.dumps({"index": {"_index": "legit_search_index"}}) + "\n")
                    f.write(json.dumps(doc_data) + "\n")
                    
                    doc_count += 1
                    if doc_count % 10 == 0:
                        print(f"  Processed {doc_count} documents...")
                except Exception as e:
                    print(f"  Error processing {filename}: {e}")
        else:
            print(f"Folder {year_path} not found.")

    print(f"--- COMPLETED ---")
    print(f"Total documents processed: {doc_count}")

if __name__ == "__main__":
    main()
