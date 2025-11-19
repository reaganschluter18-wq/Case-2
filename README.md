# S&P 500 10-K Filings Scraper

Python script to scrape all 10-K filings from the last 5 years for each current S&P 500 company and save them to Google Drive.

## Features

- Fetches current S&P 500 companies list from Wikipedia
- Retrieves 10-K filings from SEC EDGAR database for the last 5 years
- Downloads filings in HTML format
- Organizes files by company ticker
- Uploads all filings to Google Drive with folder structure
- Respects SEC rate limits (10 requests/second)
- Saves metadata JSON with all filing information

## Prerequisites

1. Python 3.8 or higher
2. Google Cloud Project with Drive API enabled (for upload functionality)

## Installation

```bash
pip install -r requirements.txt
```

## Google Drive Setup

To enable Google Drive upload:

1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. Create a new project or select existing one
3. Enable Google Drive API
4. Create a Service Account:
   - Go to IAM & Admin > Service Accounts
   - Create Service Account
   - Download JSON credentials
5. Save credentials as `credentials.json` in the project directory
6. Share your target Google Drive folder with the service account email

## Configuration

Before running, update the `USER_AGENT` in `scrape_10k.py`:

```python
USER_AGENT = "YourName your.email@example.com"
```

SEC requires a valid User-Agent with contact information.

## Usage

Run the script:

```bash
python scrape_10k.py
```

The script will:
1. Fetch all current S&P 500 companies (~500 companies)
2. For each company, retrieve 10-K filings from the last 5 years
3. Download filings to `10k_filings/` directory organized by ticker
4. Upload all files to Google Drive in folder `SP500_10K_Filings_Last_5_Years/`

## Output Structure

Local directory structure:
```
10k_filings/
├── AAPL/
│   ├── AAPL_2024-11-01_10K.html
│   ├── AAPL_2023-11-03_10K.html
│   └── ...
├── MSFT/
│   └── ...
└── filings_metadata.json
```

Google Drive structure:
```
SP500_10K_Filings_Last_5_Years/
├── AAPL/
│   ├── AAPL_2024-11-01_10K.html
│   └── ...
└── MSFT/
    └── ...
```

## Metadata

The script generates `filings_metadata.json` containing:
- Ticker symbol
- CIK (Central Index Key)
- Filing date
- Accession number
- Download URL
- Local file path

## Rate Limiting

The script respects SEC's rate limit of 10 requests per second with a 0.1s delay between requests.

## Notes

- Runtime: Approximately 2-3 hours for all S&P 500 companies
- Storage: Approximately 5-10 GB for all filings
- The script skips already downloaded files on re-run
- Failed downloads are logged and can be retried

## Troubleshooting

**No CIK found for ticker:**
- Some tickers may have changed; the script will skip these

**Google Drive authentication failed:**
- Ensure `credentials.json` is in the correct location
- Verify service account has necessary permissions

**SEC download errors:**
- SEC servers may be slow; the script will continue with other filings
- Check your User-Agent is properly configured

## License

MIT
