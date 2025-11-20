import os

INPUT_FILE = '../data/bulk_index.jsonl'
OUTPUT_DIR = '../data/bulk_parts/'
DOCS_PER_FILE = 1000  # We'll put 5000 documents in each smaller file

# Each document takes 2 lines in the JSONL file
LINES_PER_FILE = DOCS_PER_FILE * 2 

def split_file():
    print(f"Splitting {INPUT_FILE} into smaller files...")
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    
    try:
        with open(INPUT_FILE, 'r', encoding='utf-8') as f_in:
            file_index = 1
            lines_written = 0
            f_out = None
            
            for line in f_in:
                # Open a new file if needed
                if f_out is None or lines_written >= LINES_PER_FILE:
                    if f_out:
                        f_out.close()
                        print(f"Finished writing bulk_part_{file_index - 1}.jsonl")
                    
                    output_path = os.path.join(OUTPUT_DIR, f"bulk_part_{file_index}.jsonl")
                    f_out = open(output_path, 'w', encoding='utf-8')
                    file_index += 1
                    lines_written = 0
                
                # Write the line
                f_out.write(line)
                lines_written += 1
            
            if f_out:
                f_out.close()
                print(f"Finished writing bulk_part_{file_index - 1}.jsonl")
                
        print(f"\nSuccessfully split file into {file_index - 1} parts in '{OUTPUT_DIR}'")
        
    except FileNotFoundError:
        print(f"Error: Input file not found at {INPUT_FILE}")
    except Exception as e:
        print(f"An error occurred: {e}")

if __name__ == "__main__":
    split_file()