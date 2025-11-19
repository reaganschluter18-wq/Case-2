# S&P 500 10-K Filings Scraper

This script automatically downloads 10-K filings for all S&P 500 companies from the last 5 years from SEC EDGAR.

## Features

- **Automatic S&P 500 List**: Fetches current S&P 500 companies from Wikipedia
- **Only 10-K Forms**: Filters for only 10-K annual reports (excludes amendments)
- **Last 5 Years**: Downloads filings from the past 5 years only
- **Parsed Text**: Extracts clean text from HTML filings
- **Resume Capability**: Can resume interrupted downloads without re-downloading
- **CSV Output**: Saves all data to a single CSV file

## Requirements

```bash
pip install requests pandas beautifulsoup4 lxml
```

## Usage

### Basic Usage (All S&P 500 Companies)

```python
from scrape_sp500_10k import main

# Scrape all S&P 500 companies (will take several hours)
df = main()
```

### Test with Limited Companies

```python
from scrape_sp500_10k import main

# Test with just 5 companies first
df = main(max_companies=5)
```

### Command Line

```bash
# Edit the script and uncomment/modify the last line:
# main(max_companies=5)  # Test with 5 companies
# OR
# main()  # Run all companies

python3 scrape_sp500_10k.py
```

## Output

The script creates:
- **Directory**: `/home/user/Case-2/sp500_10k_output/`
- **CSV File**: `sp500_10k_output/sp500_10k_filings.csv`

### CSV Columns

| Column | Description |
|--------|-------------|
| ticker | Stock ticker symbol |
| company_name | Company name |
| cik | SEC Central Index Key (10 digits) |
| filing_date | Date the 10-K was filed |
| accession_number | SEC accession number |
| url | URL to the original filing |
| text_length | Length of parsed text (characters) |
| text_content | Full parsed text of the 10-K filing |

## How It Works

1. **Fetch S&P 500 List**: Gets current S&P 500 companies from Wikipedia (with GitHub fallback)
2. **Get CIKs**: Looks up SEC CIK for each company using SEC's company tickers API
3. **Find 10-K Filings**: Uses SEC EDGAR API to find 10-K filings from last 5 years
4. **Download & Parse**: Downloads each filing and extracts clean text
5. **Save to CSV**: Saves everything to a CSV file with incremental progress saves

## SEC Rate Limiting

The script automatically:
- Respects SEC's 10 requests/second limit (0.1s delay between requests)
- Uses proper User-Agent with contact email as required by SEC
- Handles network errors gracefully

## Resume Capability

If the script is interrupted:
1. It will load the existing CSV file
2. Skip already-downloaded filings
3. Continue from where it left off

## Estimated Runtime

- **5 companies**: ~2-5 minutes
- **50 companies**: ~20-40 minutes
- **All 500+ companies**: ~3-6 hours

(Depends on network speed and number of filings per company)

## Troubleshooting

### 403 Errors from SEC

If you get 403 errors:
- Make sure you're running from your **local machine** (not cloud/VPS)
- SEC blocks many cloud provider IPs
- Verify your User-Agent includes your email

### Empty Text Content

If text_content is empty:
- The filing might be an image-based PDF
- Check the URL manually to verify the filing format

### No Companies Found

If Wikipedia fails:
- Script will automatically try GitHub CSV source
- Check your internet connection

## Example

```python
from scrape_sp500_10k import SP500_10K_Scraper

# Create scraper
scraper = SP500_10K_Scraper(output_dir='./my_output')

# Run for last 3 years instead of 5
df = scraper.scrape_all(years=3, max_companies=10)

# View results
print(f"Downloaded {len(df)} filings")
print(df[['ticker', 'company_name', 'filing_date', 'text_length']])
```

## Notes

- **10-K vs 10-K/A**: Script only downloads original 10-K filings, not amendments (10-K/A)
- **Text Parsing**: HTML tags, scripts, and styles are removed, leaving clean text
- **Progress**: Progress is saved after each company, so you can stop/resume anytime
- **Duplicates**: Automatically avoids downloading duplicates using ticker+date+accession key

## License

This script is for educational and research purposes. Always comply with SEC's terms of use and rate limiting requirements.
