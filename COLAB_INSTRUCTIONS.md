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
!pip install pandas requests
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
3. ✅ Saves files directly to your Google Drive folder
4. ✅ Organizes by company ticker (e.g., `AAPL/`, `MSFT/`)
5. ✅ Creates metadata JSON with all filing info

## Output Structure

Your Google Drive will have:
```
Your_Folder_Name/
├── AAPL/
│   ├── AAPL_2024-11-01_10K.html
│   ├── AAPL_2023-11-03_10K.html
│   └── ...
├── MSFT/
│   ├── MSFT_2024-07-30_10K.html
│   └── ...
├── ... (500+ company folders)
└── filings_metadata.json
```

## Expected Runtime

- **Total time**: 2-3 hours for all S&P 500 companies
- **Storage**: 5-10 GB of files
- **Rate limit**: 10 requests/second (SEC requirement)

## Tips

- ✅ Colab stays active as long as the browser tab is open
- ✅ You can monitor progress in the output
- ✅ Script skips already downloaded files (safe to re-run)
- ✅ Failed companies are logged at the end

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
