"""
S&P 500 10-K Filings Scraper for Google Colab
Scrapes 10-K filings from SEC EDGAR and saves to Google Drive
"""

# Install required packages (run this cell first in Colab)
# !pip install pandas requests

import os
import time
import requests
import pandas as pd
from datetime import datetime, timedelta
from pathlib import Path
import json
from typing import List, Dict

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

    def download_filing(self, filing: Dict, save_path: Path) -> bool:
        """Download a single filing"""
        try:
            response = requests.get(filing['url'], headers=self.headers)
            time.sleep(REQUEST_DELAY)

            if response.status_code == 200:
                save_path.write_bytes(response.content)
                return True
            else:
                print(f"  Failed to download {filing['filename']}: {response.status_code}")
                return False

        except Exception as e:
            print(f"  Error downloading {filing['filename']}: {e}")
            return False

    def scrape_all(self, years: int = 5) -> List[Dict]:
        """Scrape all 10-K filings for S&P 500 companies"""
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

            # Create company directory
            company_dir = self.output_dir / ticker
            company_dir.mkdir(exist_ok=True)

            # Download each filing
            for filing in filings:
                save_path = company_dir / filing['filename']

                if save_path.exists():
                    print(f"  Skipping {filing['filename']} (already exists)")
                    filing['local_path'] = str(save_path)
                    all_filings.append(filing)
                    continue

                print(f"  Downloading {filing['filename']}...")
                if self.download_filing(filing, save_path):
                    filing['local_path'] = str(save_path)
                    all_filings.append(filing)
                else:
                    print(f"  Failed to download {filing['filename']}")

        # Save metadata
        metadata_path = self.output_dir / "filings_metadata.json"
        with open(metadata_path, 'w') as f:
            json.dump(all_filings, f, indent=2)

        print(f"\n{'='*80}")
        print(f"Scraping complete!")
        print(f"Total filings downloaded: {len(all_filings)}")
        print(f"Companies processed: {len(companies) - len(failed_companies)}/{len(companies)}")

        if failed_companies:
            print(f"\nFailed companies ({len(failed_companies)}): {', '.join(failed_companies)}")

        return all_filings


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

    print(f"\n📁 Saving files to: {GOOGLE_DRIVE_FOLDER}")
    print(f"📅 Downloading filings from last {YEARS_TO_DOWNLOAD} years")
    print(f"👤 User-Agent: {USER_AGENT}\n")

    # Create scraper and run
    scraper = SECFilingScraper(output_dir=GOOGLE_DRIVE_FOLDER)
    filings = scraper.scrape_all(years=YEARS_TO_DOWNLOAD)

    print("\n✅ Done! Files saved to your Google Drive.")
    print(f"📊 Metadata saved to: {GOOGLE_DRIVE_FOLDER}/filings_metadata.json")


if __name__ == "__main__":
    main()
