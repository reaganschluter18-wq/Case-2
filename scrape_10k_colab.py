"""
S&P 500 10-K Filings Scraper for Google Colab
Scrapes 10-K filings from SEC EDGAR and saves to Google Drive as CSV
Reads company list from your existing CSV file
"""

# Install required packages (run this cell first in Colab)
# !pip install pandas requests beautifulsoup4 lxml

import os
import time
import requests
import pandas as pd
from datetime import datetime, timedelta
from pathlib import Path
import json
from typing import List, Dict
from bs4 import BeautifulSoup
import re

# ============================================================================
# CONFIGURATION - MODIFY THESE VALUES
# ============================================================================

# Path to your CSV file OR folder containing CSV files
# Single file: "/content/drive/MyDrive/company_data.csv"
# Folder: "/content/drive/MyDrive/MyFolder" (will read ALL .csv files)
INPUT_CSV_PATH = "/content/drive/MyDrive/YOUR_INPUT_FILE.csv"

# Your Google Drive output folder path (after mounting)
# Example: "/content/drive/MyDrive/SEC_Filings_Output"
GOOGLE_DRIVE_FOLDER = "/content/drive/MyDrive/YOUR_OUTPUT_FOLDER_HERE"

# SEC requires contact info in User-Agent
USER_AGENT = "Reagan reaganschluter18@gmail.com"

# Number of years of filings to download
YEARS_TO_DOWNLOAD = 5

# ============================================================================
# MOUNT GOOGLE DRIVE (Run this in Colab)
# ============================================================================
from google.colab import drive
drive.mount('/content/drive')

# ============================================================================
# SEC API Configuration
# ============================================================================
SEC_API_BASE = "https://data.sec.gov"
HEADERS = {
    "User-Agent": USER_AGENT,
    "Accept-Encoding": "gzip, deflate",
    "Host": "www.sec.gov"
}
REQUEST_DELAY = 0.1  # 10 requests per second max


class SECFilingScraper:
    """Scraper for SEC 10-K filings"""

    def __init__(self, output_dir: str):
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.headers = HEADERS.copy()

    def load_companies_from_csv(self, csv_path: str) -> pd.DataFrame:
        """Load company data from user's CSV file or folder"""
        print(f"Loading company data from: {csv_path}")

        try:
            # Check if path is a directory - if so, read all CSV files
            if os.path.isdir(csv_path):
                print(f"📂 Reading all CSV files from folder...")
                csv_files = [f for f in os.listdir(csv_path) if f.endswith('.csv')]

                if not csv_files:
                    print("⚠️  No CSV files found in directory!")
                    return None

                print(f"Found {len(csv_files)} CSV file(s):")
                for f in csv_files:
                    print(f"  - {f}")

                # Read and combine all CSV files
                dfs = []
                for csv_file in csv_files:
                    file_path = os.path.join(csv_path, csv_file)
                    print(f"\n  Reading: {csv_file}")
                    df_temp = pd.read_csv(file_path)
                    print(f"    Rows: {len(df_temp)}")
                    dfs.append(df_temp)

                # Combine all dataframes
                df = pd.concat(dfs, ignore_index=True)
                print(f"\n✅ Combined total rows: {len(df)}")
            else:
                # Read single CSV file
                df = pd.read_csv(csv_path)

            print(f"\nCSV columns found: {df.columns.tolist()}")

            # Map user's columns to standard names
            # User has: company name, form type, cik, date filed, file name
            column_mapping = {}

            for col in df.columns:
                col_lower = col.lower().strip()
                if 'company' in col_lower and 'name' in col_lower:
                    column_mapping[col] = 'company_name'
                elif 'cik' in col_lower:
                    column_mapping[col] = 'cik'
                elif 'form' in col_lower and 'type' in col_lower:
                    column_mapping[col] = 'form_type'
                elif 'date' in col_lower and 'filed' in col_lower:
                    column_mapping[col] = 'date_filed'
                elif 'file' in col_lower and 'name' in col_lower:
                    column_mapping[col] = 'file_name'

            # Rename columns
            df = df.rename(columns=column_mapping)

            # Ensure we have required columns
            if 'company_name' not in df.columns or 'cik' not in df.columns:
                print("\n⚠️  ERROR: CSV must have 'company name' and 'cik' columns!")
                return None

            # Standardize CIK format (pad to 10 digits)
            df['cik'] = df['cik'].astype(str).str.zfill(10)

            # Extract ticker from company name if possible (fallback)
            # We'll try to extract ticker from file_name or use company_name
            if 'file_name' in df.columns:
                df['ticker'] = df['file_name'].str.extract(r'^([A-Z]+)', expand=False)

            if 'ticker' not in df.columns or df['ticker'].isna().all():
                # Use first word of company name as ticker fallback
                df['ticker'] = df['company_name'].str.split().str[0].str.upper()

            # Filter for 10-K forms only if form_type column exists
            if 'form_type' in df.columns:
                df = df[df['form_type'].str.contains('10-K', case=False, na=False)]
                print(f"Filtered to {len(df)} 10-K entries")

            # Get unique companies (in case there are multiple filings per company)
            companies = df[['ticker', 'company_name', 'cik']].drop_duplicates(subset=['cik'])

            print(f"Found {len(companies)} unique companies to process")
            print(f"\nSample companies:")
            print(companies.head())

            return companies

        except Exception as e:
            print(f"Error loading CSV: {e}")
            import traceback
            traceback.print_exc()
            return None

    def get_10k_filings(self, cik: str, ticker: str, years: int = 5) -> List[Dict]:
        """Get 10-K filings for a company from the last N years"""
        print(f"Fetching 10-K filings for {ticker} (CIK: {cik})...")

        try:
            url = f"https://data.sec.gov/submissions/CIK{cik}.json"
            headers = {
                "User-Agent": USER_AGENT,
                "Accept-Encoding": "gzip, deflate",
                "Host": "data.sec.gov"
            }

            response = requests.get(url, headers=headers)
            time.sleep(REQUEST_DELAY)

            if response.status_code != 200:
                print(f"  Failed to get submissions for {ticker}: {response.status_code}")
                return []

            data = response.json()
            filings = []
            recent_filings = data.get('filings', {}).get('recent', {})

            if not recent_filings:
                print(f"  No recent filings found for {ticker}")
                return []

            # Filter for 10-K filings from last N years
            cutoff_date = datetime.now() - timedelta(days=years*365)
            forms = recent_filings.get('form', [])
            filing_dates = recent_filings.get('filingDate', [])
            accession_numbers = recent_filings.get('accessionNumber', [])
            primary_documents = recent_filings.get('primaryDocument', [])

            for i in range(len(forms)):
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

            print(f"  Found {len(filings)} 10-K filings for {ticker}")
            return filings

        except Exception as e:
            print(f"  Error getting filings for {ticker}: {e}")
            return []

    def parse_html_to_text(self, html_content: bytes) -> str:
        """Parse HTML and extract clean text"""
        try:
            # Parse HTML
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
            print(f"  Error parsing HTML: {e}")
            return ""

    def download_and_parse_filing(self, filing: Dict) -> Dict:
        """Download filing and parse to text"""
        try:
            response = requests.get(filing['url'], headers=self.headers)
            time.sleep(REQUEST_DELAY)

            if response.status_code == 200:
                # Parse HTML to clean text
                text_content = self.parse_html_to_text(response.content)
                filing['text_content'] = text_content
                filing['text_length'] = len(text_content)
                return filing
            else:
                print(f"  Failed to download {filing['filename']}: {response.status_code}")
                filing['text_content'] = ""
                filing['text_length'] = 0
                return None

        except Exception as e:
            print(f"  Error downloading {filing['filename']}: {e}")
            filing['text_content'] = ""
            filing['text_length'] = 0
            return None

    def scrape_all(self, csv_path: str, years: int = 5) -> pd.DataFrame:
        """Scrape all 10-K filings for companies from CSV and save to CSV"""
        # Load companies from user's CSV
        companies = self.load_companies_from_csv(csv_path)

        if companies is None or len(companies) == 0:
            print("No companies loaded from CSV!")
            return None

        all_filings = []
        failed_companies = []

        for idx, row in companies.iterrows():
            ticker = row['ticker']
            company_name = row['company_name']
            cik = row['cik']

            print(f"\n[{idx+1}/{len(companies)}] Processing {ticker} - {company_name}")

            if not cik or pd.isna(cik):
                print(f"  No CIK found for {ticker}")
                failed_companies.append(ticker)
                continue

            # Get filings from EDGAR
            filings = self.get_10k_filings(cik, ticker, years)
            if not filings:
                failed_companies.append(ticker)
                continue

            # Download and parse each filing
            for filing in filings:
                filing['company_name'] = company_name
                print(f"  Downloading and parsing {filing['filename']}...")
                parsed_filing = self.download_and_parse_filing(filing)

                if parsed_filing and parsed_filing['text_content']:
                    all_filings.append(parsed_filing)
                    print(f"    ✓ Parsed {len(parsed_filing['text_content']):,} characters")
                else:
                    print(f"    ✗ Failed to parse filing")

            # Save progress after each company (in case of interruption)
            if all_filings:
                self._save_to_csv(all_filings)

        # Final save
        df = self._save_to_csv(all_filings)

        print(f"\n{'='*80}")
        print(f"Scraping complete!")
        print(f"Total filings downloaded: {len(all_filings)}")
        print(f"Companies processed: {len(companies) - len(failed_companies)}/{len(companies)}")

        if failed_companies:
            print(f"\nFailed companies ({len(failed_companies)}): {', '.join(failed_companies[:20])}")
            if len(failed_companies) > 20:
                print(f"... and {len(failed_companies) - 20} more")

        return df

    def _save_to_csv(self, filings: List[Dict]) -> pd.DataFrame:
        """Save filings to CSV"""
        if not filings:
            return None

        # Create DataFrame
        df = pd.DataFrame(filings)

        # Reorder columns
        columns = ['ticker', 'company_name', 'cik', 'filing_date', 'accession_number',
                   'url', 'text_length', 'text_content']

        # Only keep columns that exist
        columns = [col for col in columns if col in df.columns]
        df = df[columns]

        # Save to CSV
        csv_path = self.output_dir / "sp500_10k_filings.csv"
        df.to_csv(csv_path, index=False, encoding='utf-8')
        print(f"\n💾 Saved {len(df)} filings to {csv_path}")

        return df


def main():
    """Main execution function"""
    print("="*80)
    print("S&P 500 10-K Filings Scraper for Google Colab")
    print("="*80)

    # Check if input CSV is configured
    if "YOUR_INPUT_FILE.csv" in INPUT_CSV_PATH:
        print("\n⚠️  ERROR: Please configure INPUT_CSV_PATH at the top of the script!")
        print(f"   Current value: {INPUT_CSV_PATH}")
        print("\n   Example: INPUT_CSV_PATH = '/content/drive/MyDrive/company_data.csv'")
        return

    # Check if Google Drive folder is configured
    if "YOUR_OUTPUT_FOLDER_HERE" in GOOGLE_DRIVE_FOLDER:
        print("\n⚠️  ERROR: Please configure GOOGLE_DRIVE_FOLDER at the top of the script!")
        print(f"   Current value: {GOOGLE_DRIVE_FOLDER}")
        print("\n   Example: GOOGLE_DRIVE_FOLDER = '/content/drive/MyDrive/SEC_Filings'")
        return

    # Check if Drive is mounted
    if not os.path.exists('/content/drive/MyDrive'):
        print("\n⚠️  ERROR: Google Drive not mounted!")
        print("   Run this first:")
        print("   from google.colab import drive")
        print("   drive.mount('/content/drive')")
        return

    # Check if input CSV exists
    if not os.path.exists(INPUT_CSV_PATH):
        print(f"\n⚠️  ERROR: Input CSV path not found: {INPUT_CSV_PATH}")
        print("   Please check the file path and make sure Drive is mounted.")
        return

    print(f"\n📂 Reading companies from: {INPUT_CSV_PATH}")
    print(f"📁 Saving CSV to: {GOOGLE_DRIVE_FOLDER}")
    print(f"📅 Downloading filings from last {YEARS_TO_DOWNLOAD} years")
    print(f"👤 User-Agent: {USER_AGENT}")
    print(f"📝 Output: Parsed text (HTML tags removed)\n")

    # Create scraper and run
    scraper = SECFilingScraper(output_dir=GOOGLE_DRIVE_FOLDER)
    df = scraper.scrape_all(csv_path=INPUT_CSV_PATH, years=YEARS_TO_DOWNLOAD)

    if df is not None and len(df) > 0:
        print("\n✅ Done! CSV file saved to your Google Drive.")
        print(f"📊 File: {GOOGLE_DRIVE_FOLDER}/sp500_10k_filings.csv")
        print(f"📈 Total rows: {len(df)}")
        print(f"📏 Columns: {', '.join(df.columns.tolist())}")
    else:
        print("\n⚠️  No filings were successfully downloaded.")


if __name__ == "__main__":
    main()
