#!/usr/bin/env python3
"""
Scrape 10-K filings for all current S&P 500 companies from the last 5 years
and upload them to Google Drive.
"""

import os
import time
import requests
import pandas as pd
from datetime import datetime, timedelta
from pathlib import Path
import json
from typing import List, Dict
from io import BytesIO
from google.oauth2.credentials import Credentials
from google.oauth2 import service_account
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload, MediaIoBaseUpload
from googleapiclient.errors import HttpError

# SEC API Configuration
SEC_API_BASE = "https://data.sec.gov"
EDGAR_ARCHIVES = "https://www.sec.gov/cgi-bin/browse-edgar"
USER_AGENT = "YourName your.email@example.com"  # REQUIRED: Update with your info
HEADERS = {
    "User-Agent": USER_AGENT,
    "Accept-Encoding": "gzip, deflate",
    "Host": "www.sec.gov"
}

# Rate limiting
REQUEST_DELAY = 0.1  # 10 requests per second max per SEC guidelines


class SECFilingScraper:
    """Scraper for SEC 10-K filings"""

    def __init__(self, output_dir: str = "10k_filings"):
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(exist_ok=True)
        self.headers = HEADERS.copy()

    def get_sp500_companies(self) -> pd.DataFrame:
        """Get list of current S&P 500 companies from Wikipedia"""
        print("Fetching S&P 500 companies list...")
        url = "https://en.wikipedia.org/wiki/List_of_S%26P_500_companies"

        try:
            tables = pd.read_html(url)
            df = tables[0]

            # Clean up the dataframe
            df.columns = df.columns.str.strip()

            # Get ticker and company name, handle CIK if available
            companies = df[['Symbol', 'Security']].copy()
            companies.columns = ['ticker', 'company_name']

            # Clean tickers (remove any special characters)
            companies['ticker'] = companies['ticker'].str.replace('.', '-')

            print(f"Found {len(companies)} S&P 500 companies")
            return companies

        except Exception as e:
            print(f"Error fetching S&P 500 list: {e}")
            raise

    def get_cik_for_ticker(self, ticker: str) -> str:
        """Get CIK (Central Index Key) for a ticker symbol"""
        try:
            # Use SEC company tickers JSON
            url = "https://www.sec.gov/files/company_tickers.json"
            headers = {"User-Agent": USER_AGENT}

            response = requests.get(url, headers=headers)
            time.sleep(REQUEST_DELAY)

            if response.status_code == 200:
                data = response.json()

                # Search for ticker
                for entry in data.values():
                    if entry['ticker'].upper() == ticker.upper():
                        # CIK needs to be padded to 10 digits
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
            # Use SEC submissions API
            url = f"https://data.sec.gov/submissions/CIK{cik}.json"
            headers = {"User-Agent": USER_AGENT}

            response = requests.get(url, headers=headers)
            time.sleep(REQUEST_DELAY)

            if response.status_code != 200:
                print(f"  Failed to get submissions for {ticker}: {response.status_code}")
                return []

            data = response.json()

            # Get recent filings
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

                        # Construct filing URL
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
        # Get S&P 500 companies
        companies = self.get_sp500_companies()

        all_filings = []
        failed_companies = []

        for idx, row in companies.iterrows():
            ticker = row['ticker']
            company_name = row['company_name']

            print(f"\n[{idx+1}/{len(companies)}] Processing {ticker} - {company_name}")

            # Get CIK
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


class GoogleDriveUploader:
    """Upload files to Google Drive"""

    def __init__(self, credentials_path: str = "credentials.json"):
        """
        Initialize Google Drive uploader

        Args:
            credentials_path: Path to Google service account credentials JSON
                             or OAuth2 credentials file
        """
        self.credentials_path = credentials_path
        self.service = self._authenticate()

    def _authenticate(self):
        """Authenticate with Google Drive API"""
        try:
            # Try service account authentication first
            if os.path.exists(self.credentials_path):
                credentials = service_account.Credentials.from_service_account_file(
                    self.credentials_path,
                    scopes=['https://www.googleapis.com/auth/drive.file']
                )
                service = build('drive', 'v3', credentials=credentials)
                print("Authenticated with Google Drive using service account")
                return service
            else:
                print(f"Credentials file not found: {self.credentials_path}")
                print("Please provide a Google service account credentials JSON file")
                return None

        except Exception as e:
            print(f"Error authenticating with Google Drive: {e}")
            return None

    def create_folder(self, folder_name: str, parent_id: str = None) -> str:
        """Create a folder in Google Drive"""
        if not self.service:
            return None

        try:
            file_metadata = {
                'name': folder_name,
                'mimeType': 'application/vnd.google-apps.folder'
            }

            if parent_id:
                file_metadata['parents'] = [parent_id]

            folder = self.service.files().create(
                body=file_metadata,
                fields='id'
            ).execute()

            print(f"Created folder: {folder_name} (ID: {folder.get('id')})")
            return folder.get('id')

        except HttpError as e:
            print(f"Error creating folder {folder_name}: {e}")
            return None

    def upload_file(self, file_path: str, parent_id: str = None,
                   folder_name: str = None) -> bool:
        """Upload a file to Google Drive"""
        if not self.service:
            print("Google Drive service not authenticated")
            return False

        try:
            file_path = Path(file_path)

            file_metadata = {'name': file_path.name}

            if parent_id:
                file_metadata['parents'] = [parent_id]

            media = MediaFileUpload(
                str(file_path),
                mimetype='text/html',
                resumable=True
            )

            file = self.service.files().create(
                body=file_metadata,
                media_body=media,
                fields='id'
            ).execute()

            return True

        except Exception as e:
            print(f"Error uploading {file_path}: {e}")
            return False

    def upload_directory(self, local_dir: str, drive_folder_name: str = "10K_Filings") -> bool:
        """Upload entire directory to Google Drive"""
        if not self.service:
            print("Cannot upload: Google Drive not authenticated")
            return False

        local_dir = Path(local_dir)

        # Create root folder
        root_folder_id = self.create_folder(drive_folder_name)

        if not root_folder_id:
            print("Failed to create root folder")
            return False

        # Upload all files organized by company
        total_files = 0
        uploaded_files = 0

        for company_dir in local_dir.iterdir():
            if company_dir.is_dir():
                # Create company folder
                company_folder_id = self.create_folder(
                    company_dir.name,
                    parent_id=root_folder_id
                )

                if company_folder_id:
                    # Upload all files in company folder
                    for file_path in company_dir.glob("*.html"):
                        total_files += 1
                        print(f"Uploading {file_path.name}...")

                        if self.upload_file(str(file_path), parent_id=company_folder_id):
                            uploaded_files += 1

                        time.sleep(0.1)  # Rate limiting

        print(f"\n{'='*80}")
        print(f"Upload complete!")
        print(f"Uploaded {uploaded_files}/{total_files} files to Google Drive")
        print(f"Folder ID: {root_folder_id}")

        return True


def main():
    """Main execution function"""
    print("="*80)
    print("S&P 500 10-K Filings Scraper")
    print("="*80)

    # Step 1: Scrape filings
    scraper = SECFilingScraper(output_dir="10k_filings")
    filings = scraper.scrape_all(years=5)

    # Step 2: Upload to Google Drive
    print("\n" + "="*80)
    print("Uploading to Google Drive...")
    print("="*80)

    uploader = GoogleDriveUploader(credentials_path="credentials.json")

    if uploader.service:
        uploader.upload_directory("10k_filings", drive_folder_name="SP500_10K_Filings_Last_5_Years")
    else:
        print("\nSkipping Google Drive upload (no credentials)")
        print("To enable upload:")
        print("1. Create a Google Cloud project")
        print("2. Enable Google Drive API")
        print("3. Create service account and download credentials.json")
        print("4. Place credentials.json in this directory")

    print("\nDone!")


if __name__ == "__main__":
    main()
