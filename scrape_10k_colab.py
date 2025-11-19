"""
S&P 500 10-K Filings Scraper for Google Colab
Scrapes 10-K filings from SEC EDGAR and saves to Google Drive as CSV
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

# Your Google Drive folder path (after mounting)
# Example: "/content/drive/MyDrive/SEC_Filings"
GOOGLE_DRIVE_FOLDER = "/content/drive/MyDrive/YOUR_FOLDER_NAME_HERE"

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

    def get_sp500_companies(self) -> pd.DataFrame:
        """Get list of current S&P 500 companies"""
        print("Fetching S&P 500 companies list...")

        # Try CSV source with CIK data
        urls = [
            "https://raw.githubusercontent.com/datasets/s-and-p-500-companies/master/data/constituents.csv",
            "https://en.wikipedia.org/wiki/List_of_S%26P_500_companies"
        ]

        for url in urls:
            try:
                if url.endswith('.csv'):
                    print(f"Trying CSV source...")
                    df = pd.read_csv(url)

                    # Get columns with CIK if available
                    if 'Symbol' in df.columns and 'Security' in df.columns:
                        if 'CIK' in df.columns:
                            companies = df[['Symbol', 'Security', 'CIK']].copy()
                            companies.columns = ['ticker', 'company_name', 'cik']
                            companies['cik'] = companies['cik'].astype(str).str.zfill(10)
                        else:
                            companies = df[['Symbol', 'Security']].copy()
                            companies.columns = ['ticker', 'company_name']
                            companies['cik'] = None
                    else:
                        companies = df.iloc[:, [0, 1]].copy()
                        companies.columns = ['ticker', 'company_name']
                        companies['cik'] = None

                    companies['ticker'] = companies['ticker'].str.replace('.', '-')
                    print(f"Found {len(companies)} S&P 500 companies")
                    return companies

                else:
                    # Try Wikipedia
                    print(f"Trying Wikipedia source...")
                    headers = {
                        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
                    }
                    response = requests.get(url, headers=headers)
                    response.raise_for_status()

                    tables = pd.read_html(response.text)
                    df = tables[0]
                    df.columns = df.columns.str.strip()
                    companies = df[['Symbol', 'Security']].copy()
                    companies.columns = ['ticker', 'company_name']
                    companies['ticker'] = companies['ticker'].str.replace('.', '-')

                    print(f"Found {len(companies)} S&P 500 companies")
                    return companies

            except Exception as e:
                print(f"  Failed with {url}: {e}")
                continue

        raise Exception("Could not fetch S&P 500 companies list")

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
            print(f"Error getting CIK for {ticker}: {e}")
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

    def scrape_all(self, years: int = 5) -> pd.DataFrame:
        """Scrape all 10-K filings for S&P 500 companies and save to CSV"""
        companies = self.get_sp500_companies()
        all_filings = []
        failed_companies = []

        for idx, row in companies.iterrows():
            ticker = row['ticker']
            company_name = row['company_name']

            print(f"\n[{idx+1}/{len(companies)}] Processing {ticker} - {company_name}")

            # Get CIK from dataframe or API
            cik = row.get('cik', None) if 'cik' in row and pd.notna(row.get('cik')) else None
            if not cik:
                cik = self.get_cik_for_ticker(ticker)

            if not cik:
                print(f"  Could not find CIK for {ticker}")
                failed_companies.append(ticker)
                continue

            # Get filings
            filings = self.get_10k_filings(cik, ticker, years)
            if not filings:
                failed_companies.append(ticker)
                continue

            # Download and parse each filing
            for filing in filings:
                print(f"  Downloading and parsing {filing['filename']}...")
                parsed_filing = self.download_and_parse_filing(filing)

                if parsed_filing and parsed_filing['text_content']:
                    all_filings.append(parsed_filing)
                    print(f"    ✓ Parsed {len(parsed_filing['text_content'])} characters")
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

    # Check if Google Drive folder is configured
    if "YOUR_FOLDER_NAME_HERE" in GOOGLE_DRIVE_FOLDER:
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

    print(f"\n📁 Saving CSV to: {GOOGLE_DRIVE_FOLDER}")
    print(f"📅 Downloading filings from last {YEARS_TO_DOWNLOAD} years")
    print(f"👤 User-Agent: {USER_AGENT}")
    print(f"📝 Output: Parsed text (HTML tags removed)\n")

    # Create scraper and run
    scraper = SECFilingScraper(output_dir=GOOGLE_DRIVE_FOLDER)
    df = scraper.scrape_all(years=YEARS_TO_DOWNLOAD)

    if df is not None and len(df) > 0:
        print("\n✅ Done! CSV file saved to your Google Drive.")
        print(f"📊 File: {GOOGLE_DRIVE_FOLDER}/sp500_10k_filings.csv")
        print(f"📈 Total rows: {len(df)}")
        print(f"📏 Columns: {', '.join(df.columns.tolist())}")
    else:
        print("\n⚠️  No filings were successfully downloaded.")


if __name__ == "__main__":
    main()
