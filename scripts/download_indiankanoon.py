#!/usr/bin/env python3
"""
Download Indian Supreme Court judgments from Indian Kanoon.
Usage: python download_indiankanoon.py --year-start 2020 --year-end 2024 --max-per-year 100
"""

import requests
import os
import time
import json
import re
from bs4 import BeautifulSoup
from datetime import datetime
import argparse

class IndianKanoonDownloader:
    def __init__(self, output_dir="data/supreme_court_judgments"):
        self.base_url = "https://indiankanoon.org"
        self.output_dir = output_dir
        os.makedirs(output_dir, exist_ok=True)
        
    def sanitize_filename(self, text):
        """Create a safe filename from text."""
        # Remove invalid characters
        text = re.sub(r'[<>:"/\\|?*]', '', text)
        # Replace spaces with underscores
        text = text.replace(' ', '_')
        # Limit length
        return text[:150]
    
    def parse_judgment_date(self, text):
        """Try to extract judgment date from text."""
        # Look for date patterns like "15 January 2020" or "15-01-2020"
        date_patterns = [
            r'(\d{1,2})\s+(January|February|March|April|May|June|July|August|September|October|November|December)\s+(\d{4})',
            r'(\d{1,2})-(\d{1,2})-(\d{4})',
            r'(\d{4})-(\d{1,2})-(\d{1,2})',
        ]
        
        for pattern in date_patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                try:
                    if len(match.groups()) == 3:
                        if match.group(2).isdigit():
                            # DD-MM-YYYY format
                            dt = datetime.strptime(f"{match.group(1)}-{match.group(2)}-{match.group(3)}", "%d-%m-%Y")
                        else:
                            # DD Month YYYY format
                            dt = datetime.strptime(f"{match.group(1)} {match.group(2)} {match.group(3)}", "%d %B %Y")
                        return dt.strftime("%d_%B_%Y")
                except:
                    continue
        return None
    
    def extract_citation(self, soup):
        """Extract citation from judgment page."""
        # Look for citation in various places
        citation_patterns = [
            r'(\d{4}\s+\w+\s+\d+)',
            r'AIR\s+\d{4}\s+SC\s+\d+',
            r'\(\d{4}\)\s+\d+\s+SCC\s+\d+',
        ]
        
        text = soup.get_text()
        for pattern in citation_patterns:
            match = re.search(pattern, text)
            if match:
                return match.group(0)
        
        return "Unknown_Citation"
    
    def download_judgment_text(self, case_url):
        """Download the text content of a judgment."""
        try:
            response = requests.get(case_url, timeout=30)
            response.raise_for_status()
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # Find the judgment text container
            judgment_div = soup.find('div', class_='judgments')
            if judgment_div:
                text = judgment_div.get_text(separator=' ', strip=True)
            else:
                text = soup.get_text(separator=' ', strip=True)
            
            return soup, text
        except Exception as e:
            print(f"    Error downloading {case_url}: {e}")
            return None, None
    
    def download_year(self, year, max_cases=100):
        """Download judgments for a specific year."""
        year_dir = os.path.join(self.output_dir, str(year))
        os.makedirs(year_dir, exist_ok=True)
        
        print(f"\n{'='*60}")
        print(f"Downloading Supreme Court judgments for year {year}")
        print(f"{'='*60}")
        
        downloaded = 0
        page = 0
        
        while downloaded < max_cases:
            # Search URL for Supreme Court cases in this year
            search_url = f"{self.base_url}/search/?formInput=doctypes:supremecourt%20year:{year}&pagenum={page}"
            
            try:
                print(f"\nFetching page {page + 1}...")
                response = requests.get(search_url, timeout=30)
                response.raise_for_status()
                soup = BeautifulSoup(response.content, 'html.parser')
                
                # Find all case result divs
                results = soup.find_all('div', class_='result')
                
                if not results:
                    print(f"No more results found for year {year}")
                    break
                
                for result in results:
                    if downloaded >= max_cases:
                        break
                    
                    # Extract case title and link
                    title_link = result.find('a', class_='cite_tag')
                    if not title_link:
                        continue
                    
                    case_name = title_link.get_text(strip=True)
                    case_url = self.base_url + title_link.get('href')
                    
                    print(f"\n[{downloaded + 1}/{max_cases}] {case_name[:80]}...")
                    
                    # Download judgment content
                    judgment_soup, judgment_text = self.download_judgment_text(case_url)
                    
                    if not judgment_text:
                        continue
                    
                    # Extract metadata
                    date_str = self.parse_judgment_date(judgment_text)
                    citation = self.extract_citation(judgment_soup) if judgment_soup else "Unknown"
                    
                    # Create filename in expected format
                    if date_str:
                        filename = f"{self.sanitize_filename(case_name)}_on_{date_str}.txt"
                    else:
                        filename = f"{self.sanitize_filename(case_name)}_{year}.txt"
                    
                    filepath = os.path.join(year_dir, filename)
                    
                    # Save judgment
                    with open(filepath, 'w', encoding='utf-8') as f:
                        f.write(f"Case: {case_name}\n")
                        f.write(f"Citation: {citation}\n")
                        f.write(f"Year: {year}\n")
                        f.write(f"Source: {case_url}\n")
                        f.write(f"\n{'='*80}\n\n")
                        f.write(judgment_text)
                    
                    # Also save metadata as JSON
                    metadata = {
                        "case_name": case_name,
                        "citation_id": citation,
                        "year": year,
                        "judgment_date": date_str,
                        "source_url": case_url,
                        "filename": filename
                    }
                    
                    meta_file = filepath.replace('.txt', '_meta.json')
                    with open(meta_file, 'w', encoding='utf-8') as f:
                        json.dump(metadata, f, indent=2)
                    
                    downloaded += 1
                    print(f"    ✓ Saved: {filename}")
                    
                    # Be respectful - wait between requests
                    time.sleep(2)
                
                # Move to next page
                page += 1
                time.sleep(3)  # Longer delay between pages
                
            except Exception as e:
                print(f"Error processing page {page}: {e}")
                break
        
        print(f"\n{'='*60}")
        print(f"Downloaded {downloaded} judgments for year {year}")
        print(f"Saved to: {year_dir}")
        print(f"{'='*60}")
        
        return downloaded
    
    def download_range(self, year_start, year_end, max_per_year=100):
        """Download judgments for a range of years."""
        total = 0
        for year in range(year_start, year_end + 1):
            count = self.download_year(year, max_per_year)
            total += count
            print(f"\nTotal downloaded so far: {total}")
            time.sleep(5)  # Delay between years
        
        print(f"\n{'='*60}")
        print(f"DOWNLOAD COMPLETE")
        print(f"Total judgments downloaded: {total}")
        print(f"Years: {year_start}-{year_end}")
        print(f"{'='*60}")
        
        return total

def main():
    parser = argparse.ArgumentParser(description='Download Indian Supreme Court judgments from Indian Kanoon')
    parser.add_argument('--year-start', type=int, default=2022, help='Start year (default: 2022)')
    parser.add_argument('--year-end', type=int, default=2024, help='End year (default: 2024)')
    parser.add_argument('--max-per-year', type=int, default=50, help='Maximum cases per year (default: 50)')
    parser.add_argument('--output-dir', type=str, default='data/supreme_court_judgments', help='Output directory')
    
    args = parser.parse_args()
    
    print(f"""
    ╔═══════════════════════════════════════════════════════════╗
    ║   Indian Kanoon Supreme Court Judgment Downloader         ║
    ╚═══════════════════════════════════════════════════════════╝
    
    Configuration:
    - Years: {args.year_start} to {args.year_end}
    - Max per year: {args.max_per_year}
    - Output: {args.output_dir}
    
    Starting download...
    """)
    
    downloader = IndianKanoonDownloader(output_dir=args.output_dir)
    total = downloader.download_range(args.year_start, args.year_end, args.max_per_year)
    
    print(f"\n✅ Successfully downloaded {total} judgments!")
    print(f"\nNext steps:")
    print(f"1. Process the downloaded files:")
    print(f"   python scripts/1_pdf_to_jsonl.py")
    print(f"2. Upload to Elasticsearch:")
    print(f"   bash scripts/2_bulk_upload.sh")

if __name__ == "__main__":
    main()
