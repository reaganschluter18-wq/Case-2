# Running the 10-K Scraper in Google Colab

## Quick Start

### 1. Open Google Colab
Go to [colab.research.google.com](https://colab.research.google.com/)

### 2. Create New Notebook
Click "New notebook" or "File" > "New notebook"

### 3. Copy the Code
Copy the entire contents of `scrape_10k_colab.py` and paste it into a Colab cell

### 4. Configure Your Settings
At the top of the code, modify these lines:

```python
# Change this to your Google Drive folder path
GOOGLE_DRIVE_FOLDER = "/content/drive/MyDrive/SEC_Filings"

# Your email is already set
USER_AGENT = "Reagan reaganschluter18@gmail.com"

# Number of years (default is 5)
YEARS_TO_DOWNLOAD = 5
```

**Google Drive Folder Path Examples:**
- `/content/drive/MyDrive/SEC_Filings` - Creates folder in root of Drive
- `/content/drive/MyDrive/Documents/SEC_Filings` - Inside Documents folder
- `/content/drive/MyDrive/Projects/10K_Data` - Inside Projects folder

### 5. Run the Script

**Cell 1: Install packages**
```python
!pip install pandas requests beautifulsoup4 lxml
```

**Cell 2: Mount Google Drive**
```python
from google.colab import drive
drive.mount('/content/drive')
```
- A popup will appear asking to connect to Google Drive
- Click "Connect to Google Drive"
- Choose your Google account
- Click "Allow"

**Cell 3: Run the main script**
Paste the entire code and run it!

## What Happens

1. ✅ Script fetches all current S&P 500 companies (~503 companies)
2. ✅ For each company, downloads 10-K filings from the last 5 years
3. ✅ **Parses HTML and extracts clean text** (removes all HTML tags)
4. ✅ Saves everything to a **single CSV file** in your Google Drive
5. ✅ Auto-saves progress after each company (safe from interruptions)

## Output Structure

Your Google Drive will have:
```
Your_Folder_Name/
└── sp500_10k_filings.csv
```

**CSV Columns:**
- `ticker` - Company stock ticker (e.g., AAPL)
- `company_name` - Full company name (e.g., Apple Inc.)
- `cik` - SEC Central Index Key
- `filing_date` - Date of filing (YYYY-MM-DD)
- `accession_number` - SEC accession number
- `url` - Direct URL to original filing
- `text_length` - Number of characters in parsed text
- `text_content` - **Full parsed text content (HTML tags removed)**

## Expected Runtime

- **Total time**: 2-3 hours for all S&P 500 companies
- **Storage**: ~2-5 GB for CSV file (plain text is smaller than HTML)
- **Rate limit**: 10 requests/second (SEC requirement)
- **Progress**: Auto-saves after each company (resumable)

## Tips

- ✅ Colab stays active as long as the browser tab is open
- ✅ You can monitor progress in the output
- ✅ CSV is saved incrementally (won't lose progress if interrupted)
- ✅ Failed companies are logged at the end
- ✅ Can open CSV directly in Google Sheets or Excel

## Troubleshooting

**"Drive not mounted" error:**
- Make sure you ran the `drive.mount()` cell first
- Check that you authorized access to your Google Drive

**"YOUR_FOLDER_NAME_HERE" error:**
- You need to change the `GOOGLE_DRIVE_FOLDER` variable
- Example: `GOOGLE_DRIVE_FOLDER = "/content/drive/MyDrive/SEC_Filings"`

**403 errors from SEC:**
- Normal for a few companies
- Script will continue with others
- May be temporary SEC server issues

**Out of space:**
- Check your Google Drive storage
- All 503 companies need ~5-10 GB
- Consider reducing `YEARS_TO_DOWNLOAD` to 3 or 2

## Alternative: Run Specific Companies Only

If you want to test with just a few companies first, add this after getting companies list:

```python
# Test with just 10 companies
companies = companies.head(10)
```

Add this line in the `scrape_all()` method after `companies = self.get_sp500_companies()`
