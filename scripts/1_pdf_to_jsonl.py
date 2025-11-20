import os
import re
import fitz  # PyMuPDF
import json
from datetime import datetime

# --- Utility Functions ---

def decontracted(phrase):
    """Expands common English contractions."""
    # (Same as before)
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
    """Applies minimal cleaning to the text."""
    text = decontracted(text)
    text = text.replace('\r', ' ').replace('\n', ' ')
    text = re.sub(r'\s+', ' ', text) # Replace multiple whitespace
    return text

# --- NEW METADATA FUNCTIONS ---

def parse_date_from_filename(date_str):
    """Attempts to parse a date string like 19_May_1950 and convert to yyyy-MM-dd."""
    try:
        # Based on filename format: 19_May_1950
        dt = datetime.strptime(date_str, '%d_%B_%Y')
        return dt.strftime('%Y-%m-%d')  # Return in ES-compatible format
    except ValueError:
        return None

def extract_metadata_from_filename(filename):
    """
    Extracts Case Name and Date from the PDF filename.
    e.g., A_K_Gopalan_vs_..._on_19_May_1950_1.PDF
    """
    case_name = "Unknown Case"
    judgment_date = None
    
    name_part, ext = os.path.splitext(filename)
    parts = name_part.split('_on_')
    
    if len(parts) >= 2:
        # Case Name is everything before '_on_'
        case_name = parts[0].replace('_', ' ').strip()
        
        # Date is in the part after '_on_'
        date_part_raw = parts[1]
        date_match = re.search(r'(\d{1,2}_[A-Za-z]+_\d{4})', date_part_raw)
        if date_match:
            judgment_date = parse_date_from_filename(date_match.group(1))
            
    return case_name, judgment_date

def extract_citation_from_text(text):
    """
    Extracts Citation ID from the PDF text.
    Based on "Equivalent citations: 1950 AIR 27, 1950 SCR 88" 
    """
    # Regex to find "Equivalent citations:" and capture everything after it until the next line
    citation_match = re.search(r'Equivalent citations:\s*(.*?)(?=\n)', text, re.IGNORECASE)
    if citation_match:
        return citation_match.group(1).strip()
    
    # Fallback for SCC
    scc_match = re.search(r'(\(\d{4}\)\s+\d+\s+SCC\s+\d+)', text)
    if scc_match:
        return scc_match.group(1)
        
    return "Unknown Citation"

# --- Main Processing Loop (Updated) ---
def main():
    root_directory = '../data/supreme_court_judgments'
    output_file = '../data/bulk_index.jsonl'
    
    script_dir = os.path.dirname(__file__)
    root_directory = os.path.join(script_dir, root_directory)
    output_file = os.path.join(script_dir, output_file)

    print(f"Starting processing. Output file: {output_file}")
    
    doc_count = 0
    with open(output_file, 'w', encoding='utf-8') as f:
        for year_folder in sorted(os.listdir(root_directory)):
            year_path = os.path.join(root_directory, year_folder)
            
            if os.path.isdir(year_path) and year_folder.isdigit():
                print(f"--- Processing folder: {year_folder} ---")
                for filename in os.listdir(year_path):
                    if filename.lower().endswith(".pdf"):
                        filepath = os.path.join(year_path, filename)
                        
                        try:
                            # 1. Extract from filename FIRST
                            case_name, judgment_date = extract_metadata_from_filename(filename)

                            # 2. Extract text from PDF
                            doc = fitz.open(filepath)
                            full_text = ""
                            for page in doc:
                                full_text += page.get_text()
                            doc.close()

                            # 3. Get citation from text
                            citation = extract_citation_from_text(full_text)
                            
                            # 4. Clean Full Text
                            clean_text_content = clean_text(full_text)

                            # 5. Prepare the JSON data
                            doc_data = {
                                "case_name": case_name,
                                "judgment_date": judgment_date,
                                "citation_id": citation,
                                "full_text": clean_text_content,
                                "year": int(year_folder),
                                "court": "Supreme Court of India"
                            }
                            
                            # 6. Write to bulk file
                            f.write(json.dumps({"index": {"_index": "legit_search_index"}}) + "\n")
                            f.write(json.dumps(doc_data) + "\n")
                            
                            doc_count += 1
                            if doc_count % 100 == 0:
                                print(f"  Processed {doc_count} documents...")

                        except Exception as e:
                            print(f"  Error processing {filename}: {e}")

    print(f"--- COMPLETED ---")
    print(f"Total documents processed: {doc_count}")
    print(f"Bulk file created: {output_file}")

if __name__ == "__main__":
    main()