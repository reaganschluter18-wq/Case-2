"""
Single Company 10-K Scraper for Google Colab
Download any company's 10-K filing by ticker and year
"""

# Install required packages (run this cell first in Colab)
# !pip install pandas requests beautifulsoup4 lxml

import os
import time
import requests
import pandas as pd
from datetime import datetime
from pathlib import Path
from bs4 import BeautifulSoup
import json

# ============================================================================
# CONFIGURATION - MODIFY THESE VALUES
# ============================================================================

# Company ticker symbol (e.g., "AAPL", "MSFT", "TSLA")
TICKER = "AAPL"

# Year of 10-K filing to download (e.g., 2023, 2022, etc.)
YEAR = 2023

# Your Google Drive output folder path (after mounting)
# Example: "/content/drive/MyDrive/SEC_Filings"
GOOGLE_DRIVE_FOLDER = "/content/drive/MyDrive/10K_Filings"

# SEC requires contact info in User-Agent - REPLACE WITH YOUR EMAIL
USER_AGENT = "Your Name your.email@example.com"

# ============================================================================
# MOUNT GOOGLE DRIVE (Run this in Colab)
# ============================================================================
from google.colab import drive
drive.mount('/content/drive')

# ============================================================================
# SEC API Configuration
# ============================================================================
REQUEST_DELAY = 0.1  # 10 requests per second max (SEC requirement)


class Single10KScraper:
    """Scraper for a single company's 10-K filing"""

    def __init__(self, output_dir: str, user_agent: str):
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.user_agent = user_agent
        self.headers = {
            "User-Agent": user_agent,
            "Accept-Encoding": "gzip, deflate"
        }

    def get_cik_from_ticker(self, ticker: str) -> str:
        """Convert ticker symbol to CIK number"""
        print(f"🔍 Looking up CIK for ticker: {ticker}")

        try:
            # SEC maintains a ticker-to-CIK mapping
            url = "https://www.sec.gov/files/company_tickers.json"
            headers = {
                "User-Agent": self.user_agent,
                "Accept-Encoding": "gzip, deflate",
                "Host": "www.sec.gov"
            }

            response = requests.get(url, headers=headers)
            time.sleep(REQUEST_DELAY)

            if response.status_code != 200:
                print(f"❌ Failed to get ticker mapping: {response.status_code}")
                return None

            data = response.json()

            # Search for ticker in the data
            ticker_upper = ticker.upper()
            for key, company in data.items():
                if company.get('ticker', '').upper() == ticker_upper:
                    cik = str(company['cik_str']).zfill(10)
                    print(f"✅ Found CIK: {cik} for {company['title']}")
                    return cik

            print(f"❌ Ticker '{ticker}' not found in SEC database")
            return None

        except Exception as e:
            print(f"❌ Error looking up CIK: {e}")
            return None

    def get_10k_filing_for_year(self, cik: str, ticker: str, year: int) -> dict:
        """Get the 10-K filing for a specific year"""
        print(f"\n📋 Searching for {year} 10-K filing for {ticker} (CIK: {cik})...")

        try:
            url = f"https://data.sec.gov/submissions/CIK{cik}.json"
            headers = {
                "User-Agent": self.user_agent,
                "Accept-Encoding": "gzip, deflate",
                "Host": "data.sec.gov"
            }

            response = requests.get(url, headers=headers)
            time.sleep(REQUEST_DELAY)

            if response.status_code != 200:
                print(f"❌ Failed to get submissions: {response.status_code}")
                return None

            data = response.json()
            company_name = data.get('name', ticker)
            recent_filings = data.get('filings', {}).get('recent', {})

            if not recent_filings:
                print(f"❌ No recent filings found for {ticker}")
                return None

            # Search for 10-K filing from the specified year
            forms = recent_filings.get('form', [])
            filing_dates = recent_filings.get('filingDate', [])
            accession_numbers = recent_filings.get('accessionNumber', [])
            primary_documents = recent_filings.get('primaryDocument', [])

            found_filings = []
            for i in range(len(forms)):
                if forms[i] == '10-K':
                    filing_date = filing_dates[i]
                    filing_year = int(filing_date.split('-')[0])

                    # 10-K filings are usually filed in Q1 of the following year
                    # So a 2023 10-K might be filed in early 2024
                    # We check both the filing year and the previous year
                    if filing_year == year or filing_year == year + 1:
                        accession = accession_numbers[i].replace('-', '')
                        primary_doc = primary_documents[i]

                        # Remove leading zeros from CIK for URL
                        cik_no_zeros = str(int(cik))
                        filing_url = f"https://www.sec.gov/Archives/edgar/data/{cik_no_zeros}/{accession}/{primary_doc}"

                        found_filings.append({
                            'ticker': ticker,
                            'company_name': company_name,
                            'cik': cik,
                            'form': forms[i],
                            'filing_date': filing_date,
                            'accession_number': accession_numbers[i],
                            'url': filing_url,
                            'filename': f"{ticker}_{filing_date}_10K.html"
                        })

            if not found_filings:
                print(f"❌ No 10-K filing found for year {year}")
                print(f"   Tip: 10-K for fiscal year {year} is usually filed in early {year+1}")
                return None

            # If multiple filings found, pick the one closest to the target year
            if len(found_filings) > 1:
                print(f"ℹ️  Found {len(found_filings)} 10-K filings near year {year}:")
                for f in found_filings:
                    print(f"   - Filed on: {f['filing_date']}")
                print(f"   Selecting the first one: {found_filings[0]['filing_date']}")

            filing = found_filings[0]
            print(f"✅ Found 10-K filing dated: {filing['filing_date']}")
            return filing

        except Exception as e:
            print(f"❌ Error getting filings: {e}")
            import traceback
            traceback.print_exc()
            return None

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
            print(f"❌ Error parsing HTML: {e}")
            return ""

    def download_and_parse_filing(self, filing: dict) -> dict:
        """Download filing and parse to text"""
        print(f"\n⬇️  Downloading: {filing['url']}")

        try:
            response = requests.get(filing['url'], headers=self.headers)
            time.sleep(REQUEST_DELAY)

            if response.status_code == 200:
                print(f"✅ Download successful ({len(response.content):,} bytes)")

                # Parse HTML to clean text
                print(f"🔄 Parsing HTML to clean text...")
                text_content = self.parse_html_to_text(response.content)

                if not text_content:
                    print(f"❌ Warning: Parsed text is empty!")
                    return None

                filing['text_content'] = text_content
                filing['text_length'] = len(text_content)

                print(f"✅ Parsed {len(text_content):,} characters")
                return filing
            else:
                print(f"❌ Failed to download: HTTP {response.status_code}")
                return None

        except Exception as e:
            print(f"❌ Error downloading: {e}")
            return None

    def save_to_csv(self, filing: dict) -> pd.DataFrame:
        """Save filing to CSV"""
        print(f"\n💾 Saving to CSV...")

        # Create DataFrame
        df = pd.DataFrame([filing])

        # Reorder columns
        columns = ['ticker', 'company_name', 'cik', 'filing_date', 'accession_number',
                   'url', 'text_length', 'text_content']
        df = df[columns]

        # Generate filename
        csv_filename = f"{filing['ticker']}_{filing['filing_date']}_10K.csv"
        csv_path = self.output_dir / csv_filename

        # Save to CSV
        df.to_csv(csv_path, index=False)

        print(f"✅ Successfully saved to: {csv_path}")
        print(f"   File size: {os.path.getsize(csv_path):,} bytes")

        return df

    def scrape_single_filing(self, ticker: str, year: int) -> pd.DataFrame:
        """Main method to scrape a single 10-K filing"""
        print("="*80)
        print(f"📄 Single Company 10-K Scraper")
        print("="*80)
        print(f"Ticker: {ticker}")
        print(f"Year:   {year}")
        print(f"Output: {self.output_dir}")
        print("="*80)

        # Step 1: Get CIK from ticker
        cik = self.get_cik_from_ticker(ticker)
        if not cik:
            print("\n❌ Failed to find company. Please check the ticker symbol.")
            return None

        # Step 2: Get 10-K filing for the year
        filing = self.get_10k_filing_for_year(cik, ticker, year)
        if not filing:
            print("\n❌ Failed to find 10-K filing for the specified year.")
            print(f"   Tip: Try looking for adjacent years (10-Ks are filed in Q1)")
            return None

        # Step 3: Download and parse the filing
        parsed_filing = self.download_and_parse_filing(filing)
        if not parsed_filing:
            print("\n❌ Failed to download or parse filing.")
            return None

        # Step 4: Save to CSV
        df = self.save_to_csv(parsed_filing)

        print("\n" + "="*80)
        print("✅ SUCCESS! 10-K filing downloaded and saved.")
        print("="*80)
        print(f"📊 Summary:")
        print(f"   Company: {parsed_filing['company_name']}")
        print(f"   Ticker:  {parsed_filing['ticker']}")
        print(f"   Filed:   {parsed_filing['filing_date']}")
        print(f"   Length:  {parsed_filing['text_length']:,} characters")
        print(f"   File:    {self.output_dir}/{parsed_filing['ticker']}_{parsed_filing['filing_date']}_10K.csv")
        print("="*80)

        return df


def main():
    """Main execution function"""

    # Validation
    if USER_AGENT == "Your Name your.email@example.com":
        print("\n⚠️  WARNING: Please update USER_AGENT with your name and email!")
        print("   The SEC requires this for tracking purposes.")
        print("   Example: USER_AGENT = 'John Doe john.doe@university.edu'")
        return

    if not TICKER or TICKER == "":
        print("\n❌ ERROR: Please specify a TICKER symbol!")
        print("   Example: TICKER = 'AAPL'")
        return

    if not YEAR or YEAR < 1990 or YEAR > datetime.now().year:
        print("\n❌ ERROR: Please specify a valid YEAR!")
        print(f"   Example: YEAR = 2023")
        return

    # Check if Drive is mounted
    if not os.path.exists('/content/drive/MyDrive'):
        print("\n⚠️  ERROR: Google Drive not mounted!")
        print("   Run this first:")
        print("   from google.colab import drive")
        print("   drive.mount('/content/drive')")
        return

    # Create scraper and run
    scraper = Single10KScraper(output_dir=GOOGLE_DRIVE_FOLDER, user_agent=USER_AGENT)
    df = scraper.scrape_single_filing(ticker=TICKER, year=YEAR)

    if df is not None:
        print("\n✅ Done! You can now access the filing data.")
        print("\nTo view the data in Colab:")
        print("   df = pd.read_csv(f'{GOOGLE_DRIVE_FOLDER}/{TICKER}_{YEAR}_10K.csv')")
        print("   print(df['text_content'][0][:1000])  # View first 1000 characters")


if __name__ == "__main__":
    main()
