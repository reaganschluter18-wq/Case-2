"""
S&P 500 10-K Filings Scraper - Google Colab Version
===================================================

This notebook scrapes 10-K filings from S&P 500 companies for the last 5 years.

SETUP INSTRUCTIONS FOR GOOGLE COLAB:
1. Copy this entire code into a Google Colab notebook
2. Run STEP 1 (pip install packages)
3. Run STEP 2 (mount Google Drive)
4. Edit STEP 3: Replace "YOUR_FOLDER_NAME_HERE" with your actual folder name
5. Run STEP 3 (load the scraper code)
6. Run STEP 4 (execute the scraper)
7. Files will be saved to your Google Drive automatically

"""

# ============================================================================
# STEP 1: Install required packages (run this cell first in Colab)
# ============================================================================
"""
!pip install requests pandas beautifulsoup4 lxml -q
"""

# ============================================================================
# STEP 2: Mount Google Drive (run this cell to connect your Google Drive)
# ============================================================================
"""
from google.colab import drive
drive.mount('/content/drive')
"""

# ============================================================================
# STEP 3: Run this cell to scrape 10-K filings
# ============================================================================

import os
import time
import requests
import pandas as pd
from datetime import datetime, timedelta
from pathlib import Path
from typing import List, Dict
from bs4 import BeautifulSoup
import traceback

# ============================================================================
# CONFIGURATION - INSERT YOUR GOOGLE DRIVE PATH HERE
# ============================================================================

# OPTION 1: Save to Google Drive (RECOMMENDED - files persist after session)
# Replace with your Google Drive folder path:
OUTPUT_DIR = "/content/drive/MyDrive/YOUR_FOLDER_NAME_HERE/sp500_10k_output"

# OPTION 2: Save to Colab temporary storage (files deleted when session ends)
# OUTPUT_DIR = "/content/sp500_10k_output"

# SEC requires contact info in User-Agent (format: Name email@domain.com)
USER_AGENT = "Reagan Schluter reaganschluter18@gmail.com"

# Number of years of filings to download
YEARS_TO_DOWNLOAD = 5

# ============================================================================
# SEC API Configuration
# ============================================================================
HEADERS = {
    "User-Agent": USER_AGENT,
    "Accept-Encoding": "gzip, deflate",
}
REQUEST_DELAY = 0.1  # 10 requests per second max per SEC guidelines


class SP500_10K_Scraper:
    """Scraper for S&P 500 10-K filings"""

    def __init__(self, output_dir: str):
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.headers = HEADERS.copy()

    def get_sp500_companies(self) -> pd.DataFrame:
        """Get list of current S&P 500 companies"""
        print("Fetching S&P 500 companies list...")

        # Try multiple sources (Wikipedia is primary, with fallbacks)
        sources = [
            {
                'name': 'Wikipedia',
                'url': 'https://en.wikipedia.org/wiki/List_of_S%26P_500_companies',
                'type': 'html'
            },
            {
                'name': 'GitHub CSV',
                'url': 'https://raw.githubusercontent.com/datasets/s-and-p-500-companies/master/data/constituents.csv',
                'type': 'csv'
            }
        ]

        for source in sources:
            try:
                print(f"  Trying {source['name']}...")

                if source['type'] == 'csv':
                    df = pd.read_csv(source['url'])

                    # Standardize column names
                    column_map = {}
                    for col in df.columns:
                        col_lower = col.lower()
                        if 'symbol' in col_lower:
                            column_map[col] = 'ticker'
                        elif 'security' in col_lower or 'name' in col_lower:
                            column_map[col] = 'company_name'
                        elif 'cik' in col_lower:
                            column_map[col] = 'cik'

                    df = df.rename(columns=column_map)

                    # Ensure we have required columns
                    if 'ticker' not in df.columns or 'company_name' not in df.columns:
                        continue

                    companies = df[['ticker', 'company_name']].copy()

                    # Add CIK if available
                    if 'cik' in df.columns:
                        companies['cik'] = df['cik'].astype(str).str.zfill(10)
                    else:
                        companies['cik'] = None

                    # Clean tickers
                    companies['ticker'] = companies['ticker'].str.replace('.', '-')

                    print(f"  ✓ Found {len(companies)} S&P 500 companies")
                    return companies

                elif source['type'] == 'html':
                    headers = {
                        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
                    }
                    response = requests.get(source['url'], headers=headers)
                    response.raise_for_status()

                    tables = pd.read_html(response.text)
                    df = tables[0]

                    # Standardize columns
                    df.columns = df.columns.str.strip()
                    companies = df[['Symbol', 'Security']].copy()
                    companies.columns = ['ticker', 'company_name']
                    companies['ticker'] = companies['ticker'].str.replace('.', '-')
                    companies['cik'] = None

                    print(f"  ✓ Found {len(companies)} S&P 500 companies")
                    return companies

            except Exception as e:
                print(f"  ✗ Failed: {e}")
                continue

        raise Exception("Could not fetch S&P 500 companies from any source")

    def get_cik_for_ticker(self, ticker: str) -> str:
        """Get CIK (Central Index Key) for a ticker symbol"""
        try:
            url = "https://www.sec.gov/files/company_tickers.json"
            headers = {"User-Agent": USER_AGENT}

            response = requests.get(url, headers=headers)
            time.sleep(REQUEST_DELAY)

            if response.status_code == 200:
                data = response.json()

                for entry in data.values():
                    if entry['ticker'].upper() == ticker.upper():
                        cik = str(entry['cik']).zfill(10)
                        return cik

            return None

        except Exception as e:
            print(f"  Error getting CIK for {ticker}: {e}")
            return None

    def get_10k_filings(self, cik: str, ticker: str, years: int = 5) -> List[Dict]:
        """Get 10-K filings for a company from the last N years"""
        try:
            url = f"https://data.sec.gov/submissions/CIK{cik}.json"
            headers = {
                "User-Agent": USER_AGENT,
                "Accept-Encoding": "gzip, deflate"
            }

            response = requests.get(url, headers=headers)
            time.sleep(REQUEST_DELAY)

            if response.status_code != 200:
                print(f"  ✗ Failed to get submissions: HTTP {response.status_code}")
                return []

            data = response.json()
            filings = []
            recent_filings = data.get('filings', {}).get('recent', {})

            if not recent_filings:
                print(f"  ✗ No recent filings found")
                return []

            # Filter for 10-K filings from last N years
            cutoff_date = datetime.now() - timedelta(days=years*365)
            forms = recent_filings.get('form', [])
            filing_dates = recent_filings.get('filingDate', [])
            accession_numbers = recent_filings.get('accessionNumber', [])
            primary_documents = recent_filings.get('primaryDocument', [])

            for i in range(len(forms)):
                # Only process 10-K forms (not 10-K/A amendments)
                if forms[i] == '10-K':
                    filing_date = datetime.strptime(filing_dates[i], '%Y-%m-%d')
                    if filing_date >= cutoff_date:
                        accession = accession_numbers[i].replace('-', '')
                        primary_doc = primary_documents[i]
                        filing_url = f"https://www.sec.gov/Archives/edgar/data/{cik}/{accession}/{primary_doc}"

                        filings.append({
                            'ticker': ticker,
                            'company_name': '',  # Will be filled in later
                            'cik': cik,
                            'form': forms[i],
                            'filing_date': filing_dates[i],
                            'accession_number': accession_numbers[i],
                            'url': filing_url,
                            'filename': f"{ticker}_{filing_dates[i]}_10K.html"
                        })

            print(f"  ✓ Found {len(filings)} 10-K filings")
            return filings

        except Exception as e:
            print(f"  ✗ Error: {e}")
            return []

    def parse_html_to_text(self, html_content: bytes) -> str:
        """Parse HTML and extract clean text"""
        try:
            soup = BeautifulSoup(html_content, 'lxml')

            # Remove script and style elements
            for script in soup(["script", "style"]):
                script.decompose()

            # Get text
            text = soup.get_text()

            # Clean up whitespace
            lines = (line.strip() for line in text.splitlines())
            chunks = (phrase.strip() for line in lines for phrase in line.split("  "))
            text = ' '.join(chunk for chunk in chunks if chunk)

            return text
        except Exception as e:
            print(f"  ✗ Error parsing HTML: {e}")
            return ""

    def download_and_parse_filing(self, filing: Dict) -> Dict:
        """Download filing and parse to text"""
        try:
            # Use proper headers for SEC archives
            headers = {
                "User-Agent": USER_AGENT,
                "Accept-Encoding": "gzip, deflate",
                "Host": "www.sec.gov"
            }
            response = requests.get(filing['url'], headers=headers)
            time.sleep(REQUEST_DELAY)

            if response.status_code == 200:
                text_content = self.parse_html_to_text(response.content)
                filing['text_content'] = text_content
                filing['text_length'] = len(text_content)

                if not text_content:
                    print(f"    ⚠️  Warning: Parsed text is empty")
                    return None

                print(f"    ✓ Downloaded and parsed ({len(text_content):,} characters)")
                return filing
            else:
                print(f"    ✗ Download failed: HTTP {response.status_code}")
                return None

        except Exception as e:
            print(f"    ✗ Error: {e}")
            return None

    def scrape_all(self, years: int = 5, max_companies: int = None) -> pd.DataFrame:
        """Scrape all 10-K filings for S&P 500 companies"""
        print("="*80)
        print("S&P 500 10-K Filings Scraper")
        print("="*80)
        print(f"\n📅 Downloading 10-K filings from last {years} years")
        print(f"📁 Output directory: {self.output_dir}")
        print(f"👤 User-Agent: {USER_AGENT}\n")

        # Get S&P 500 companies
        companies = self.get_sp500_companies()

        # Limit companies if specified (for testing)
        if max_companies:
            companies = companies.head(max_companies)
            print(f"\n⚠️  LIMITED TO FIRST {max_companies} COMPANIES FOR TESTING\n")

        # Load existing filings if CSV already exists (for resume capability)
        existing_filings = []
        existing_keys = set()
        output_csv = self.output_dir / "sp500_10k_filings.csv"

        if output_csv.exists():
            print(f"📋 Found existing CSV, loading to avoid re-downloading...")
            try:
                existing_df = pd.read_csv(output_csv)
                existing_filings = existing_df.to_dict('records')
                for filing in existing_filings:
                    key = f"{filing.get('ticker', '')}_{filing.get('filing_date', '')}_{filing.get('accession_number', '')}"
                    existing_keys.add(key)
                print(f"   Loaded {len(existing_filings)} existing filings\n")
            except Exception as e:
                print(f"   Warning: Could not load existing CSV: {e}\n")
                existing_filings = []
                existing_keys = set()

        all_filings = existing_filings.copy()
        failed_companies = []
        newly_downloaded = 0
        skipped_count = 0

        for idx, row in companies.iterrows():
            ticker = row['ticker']
            company_name = row['company_name']
            cik = row.get('cik', None) if pd.notna(row.get('cik')) else None

            print(f"\n[{idx+1}/{len(companies)}] {ticker} - {company_name}")

            # Get CIK if not available
            if not cik:
                print(f"  Getting CIK for {ticker}...")
                cik = self.get_cik_for_ticker(ticker)

            if not cik:
                print(f"  ✗ Could not find CIK")
                failed_companies.append(ticker)
                continue

            # Get filings
            filings = self.get_10k_filings(cik, ticker, years)
            if not filings:
                failed_companies.append(ticker)
                continue

            # Download and parse each filing
            for filing in filings:
                filing['company_name'] = company_name

                # Check if already downloaded
                filing_key = f"{filing['ticker']}_{filing['filing_date']}_{filing['accession_number']}"
                if filing_key in existing_keys:
                    print(f"  ⏭️  Skipping {filing['filename']} (already downloaded)")
                    skipped_count += 1
                    continue

                print(f"  Downloading {filing['filename']}...")
                parsed_filing = self.download_and_parse_filing(filing)

                if parsed_filing and parsed_filing['text_content']:
                    all_filings.append(parsed_filing)
                    existing_keys.add(filing_key)
                    newly_downloaded += 1
                    print(f"    📊 Total: {len(all_filings)} filings ({newly_downloaded} new, {skipped_count} skipped)")

            # Save progress after each company
            if all_filings:
                self._save_to_csv(all_filings)

        # Final save
        df = self._save_to_csv(all_filings)

        print(f"\n{'='*80}")
        print(f"✅ Scraping Complete!")
        print(f"{'='*80}")
        print(f"Total filings in CSV: {len(all_filings)}")
        print(f"  - Newly downloaded: {newly_downloaded}")
        print(f"  - Previously existed: {skipped_count}")
        print(f"Companies processed: {len(companies) - len(failed_companies)}/{len(companies)}")

        if failed_companies:
            print(f"\n⚠️  Failed companies ({len(failed_companies)}): {', '.join(failed_companies[:20])}")
            if len(failed_companies) > 20:
                print(f"    ... and {len(failed_companies) - 20} more")

        print(f"\n📄 Output: {output_csv}")

        return df

    def _save_to_csv(self, filings: List[Dict]) -> pd.DataFrame:
        """Save filings to CSV"""
        if not filings:
            return None

        df = pd.DataFrame(filings)

        # Reorder columns
        columns = ['ticker', 'company_name', 'cik', 'filing_date', 'accession_number',
                   'url', 'text_length', 'text_content']
        columns = [col for col in columns if col in df.columns]
        df = df[columns]

        # Save to CSV with explicit flushing
        csv_path = self.output_dir / "sp500_10k_filings.csv"
        with open(csv_path, 'w', encoding='utf-8', newline='') as f:
            df.to_csv(f, index=False)
            f.flush()
            os.fsync(f.fileno())

        return df


# ============================================================================
# MAIN EXECUTION
# ============================================================================

def main(max_companies: int = None):
    """
    Main execution function

    Args:
        max_companies: Limit to first N companies (for testing).
                       Use None to scrape all S&P 500 companies.

    Examples:
        # Test with 5 companies
        df = main(max_companies=5)

        # Scrape all S&P 500 companies
        df = main()
    """
    scraper = SP500_10K_Scraper(output_dir=OUTPUT_DIR)
    df = scraper.scrape_all(years=YEARS_TO_DOWNLOAD, max_companies=max_companies)

    if df is not None and len(df) > 0:
        print(f"\n✅ Success! CSV file saved.")
        print(f"📊 Rows: {len(df)}")
        print(f"📏 Columns: {', '.join(df.columns.tolist())}")

        # In Colab, show download link
        try:
            from google.colab import files
            print(f"\n📥 To download the CSV file, run:")
            print(f"   files.download('{OUTPUT_DIR}/sp500_10k_filings.csv')")
        except:
            pass

        return df
    else:
        print("\n⚠️  No filings were downloaded.")
        return None


# ============================================================================
# STEP 4: RUN THE SCRAPER (Choose one option below)
# ============================================================================

if __name__ == "__main__":
    # OPTION A: Test with just 5 companies first (RECOMMENDED - takes ~5 minutes)
    print("Starting test run with 5 companies...")
    df = main(max_companies=5)

    # OPTION B: Uncomment below to scrape ALL S&P 500 companies (takes 3-6 hours)
    # print("Starting full scrape of all S&P 500 companies...")
    # df = main()

    # View sample results
    if df is not None and len(df) > 0:
        print("\n" + "="*80)
        print("Sample Data Preview:")
        print("="*80)
        print(df[['ticker', 'company_name', 'filing_date', 'text_length']].head(10))

        print("\n" + "="*80)
        print(f"✅ File saved to your Google Drive:")
        print(f"📁 {OUTPUT_DIR}/sp500_10k_filings.csv")
        print("="*80)
