# Single Company 10-K Scraper for Google Colab

Download any company's 10-K filing by simply entering a ticker symbol and year!

## Quick Start Guide

### 1. Open in Google Colab

1. Upload `scrape_single_10k_colab.py` to your Google Drive
2. Open it in Google Colab (right-click → Open with → Google Colaboratory)

### 2. Configure Your Settings

At the top of the file, modify these three variables:

```python
# Company ticker symbol (e.g., "AAPL", "MSFT", "TSLA")
TICKER = "AAPL"

# Year of 10-K filing to download (e.g., 2023, 2022, etc.)
YEAR = 2023

# Your Google Drive output folder path (after mounting)
GOOGLE_DRIVE_FOLDER = "/content/drive/MyDrive/10K_Filings"

# SEC requires contact info - REPLACE WITH YOUR EMAIL
USER_AGENT = "Your Name your.email@example.com"
```

**Important:**
- Replace `USER_AGENT` with your actual name and email (SEC requirement)
- The ticker must be a valid US stock ticker (e.g., AAPL, MSFT, GOOGL, TSLA)
- The year is the fiscal year (note: 10-Ks are usually filed in Q1 of the following year)

### 3. Run the Script

In Google Colab, run all cells:
1. First cell will install required packages
2. Second cell will mount your Google Drive (you'll need to authorize)
3. Script will run and download the 10-K filing

### 4. Access Your Data

The script saves a CSV file to your Google Drive with the following structure:

**Filename:** `{TICKER}_{filing_date}_10K.csv`

**Columns:**
- `ticker` - Company stock ticker
- `company_name` - Full company name
- `cik` - SEC CIK number
- `filing_date` - Date the 10-K was filed
- `accession_number` - SEC accession number
- `url` - URL to the original filing
- `text_length` - Character count of parsed text
- `text_content` - Full text content of the 10-K (HTML tags removed)

## Examples

### Example 1: Download Apple's 2023 10-K

```python
TICKER = "AAPL"
YEAR = 2023
GOOGLE_DRIVE_FOLDER = "/content/drive/MyDrive/10K_Filings"
USER_AGENT = "Student Name student@university.edu"
```

### Example 2: Download Tesla's 2022 10-K

```python
TICKER = "TSLA"
YEAR = 2022
GOOGLE_DRIVE_FOLDER = "/content/drive/MyDrive/10K_Filings"
USER_AGENT = "Student Name student@university.edu"
```

### Example 3: Download Microsoft's 2021 10-K

```python
TICKER = "MSFT"
YEAR = 2021
GOOGLE_DRIVE_FOLDER = "/content/drive/MyDrive/10K_Filings"
USER_AGENT = "Student Name student@university.edu"
```

## Viewing the Data in Colab

After the script completes, you can read and analyze the data:

```python
import pandas as pd

# Load the CSV
df = pd.read_csv('/content/drive/MyDrive/10K_Filings/AAPL_2023-11-03_10K.csv')

# View basic info
print(f"Company: {df['company_name'][0]}")
print(f"Filed: {df['filing_date'][0]}")
print(f"Text length: {df['text_length'][0]:,} characters")

# View first 1000 characters of the filing
print("\nFirst 1000 characters:")
print(df['text_content'][0][:1000])

# Search for specific content
text = df['text_content'][0]
if 'revenue' in text.lower():
    print("\n✅ The word 'revenue' appears in this filing")
```

## Tips and Troubleshooting

### Understanding Fiscal Years

- A company's fiscal year 2023 10-K is typically filed in **early 2024** (Q1)
- For example, Apple's fiscal 2023 10-K was filed in November 2023
- If you don't find a filing for year X, try year X+1 or X-1

### Common Issues

**"Ticker not found"**
- Make sure you're using the correct ticker symbol
- Check that it's a US-listed company
- Try searching on sec.gov to verify the ticker

**"No 10-K filing found for year X"**
- Try the year before or after (fiscal year vs calendar year confusion)
- Some companies may not have filed that year (IPOs, mergers, etc.)

**"Google Drive not mounted"**
- Make sure you run the drive.mount() cell and authorize access
- Check that the output folder path is correct

### Rate Limiting

The script respects SEC's rate limiting requirements:
- Maximum 10 requests per second
- Includes User-Agent header with contact info
- Adds delays between requests

## Batch Processing Multiple Companies

Want to download multiple companies? Simply change the ticker and run again:

```python
# Download multiple companies one at a time
tickers = ['AAPL', 'MSFT', 'GOOGL', 'TSLA', 'AMZN']

for ticker in tickers:
    TICKER = ticker
    main()  # Run the scraper
    print(f"\n{'='*80}\n")
```

## Output Format

Each filing is saved as a separate CSV file:

```
10K_Filings/
├── AAPL_2023-11-03_10K.csv
├── MSFT_2023-07-27_10K.csv
├── TSLA_2024-01-29_10K.csv
└── ...
```

## What Gets Downloaded

The script:
1. Looks up the company's CIK (SEC identifier) from the ticker
2. Searches SEC's EDGAR database for the 10-K filing
3. Downloads the full HTML filing
4. Parses and cleans the text (removes HTML tags)
5. Saves everything to a CSV file in your Google Drive

## Requirements

- Google Colab (free)
- Google Drive (for storage)
- Internet connection
- Valid email address (for SEC User-Agent)

## Legal & Ethical Use

- This script complies with SEC's fair access guidelines
- Always provide accurate contact information in USER_AGENT
- Don't abuse the SEC's servers (the script includes rate limiting)
- Data is public and free to use for research and analysis

## Questions or Issues?

If you encounter any problems:
1. Check that all configuration variables are set correctly
2. Verify your Google Drive is mounted
3. Make sure you have internet connectivity
4. Check the SEC website isn't down: https://www.sec.gov

---

**Happy researching! 📊**
