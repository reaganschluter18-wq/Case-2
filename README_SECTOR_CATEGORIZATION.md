# S&P 500 Sector Categorization

This script divides all S&P 500 companies into their different sectors based on GICS (Global Industry Classification Standard) sectors.

## Features

- ✅ Fetches current S&P 500 company list with sector information
- ✅ Categorizes companies by GICS Sector
- ✅ Supports both online fetching (Wikipedia) and local CSV files
- ✅ Generates summary statistics by sector
- ✅ Exports data to CSV files (combined and by sector)

## Quick Start

### Option 1: Fetch from Wikipedia (automatic)

```python
python categorize_sp500_by_sector.py
```

This will:
1. Fetch the latest S&P 500 list from Wikipedia
2. Categorize companies by sector
3. Print a summary
4. Save files to `sp500_sectors_output/`

### Option 2: Use your own CSV file

```python
from categorize_sp500_by_sector import main

# Use your CSV file
sectors = main(csv_path="/path/to/your/sp500_data.csv")
```

## Usage Examples

### Basic Usage

```python
from categorize_sp500_by_sector import SP500SectorCategorizer

# Initialize
categorizer = SP500SectorCategorizer(output_dir="./my_output")

# Fetch data
df = categorizer.fetch_sp500_with_sectors()

# Categorize by sector
sectors_dict = categorizer.categorize_by_sector(df)

# Print summary
categorizer.print_sector_summary(sectors_dict)

# Save to files
categorizer.save_sectors_to_csv(sectors_dict)
```

### Get Companies from a Specific Sector

```python
# Get all technology companies
tech_companies = categorizer.get_companies_by_sector(sectors_dict, "Information Technology")
print(tech_companies[['Symbol', 'Security']])

# Get healthcare companies
healthcare = categorizer.get_companies_by_sector(sectors_dict, "Health Care")
```

### Use Your Own CSV

If you have a CSV file with S&P 500 data, it should have at least these columns:
- `Symbol` (or `Ticker`)
- `Security` (or `Company Name`)
- `GICS Sector` (or similar sector column)

```python
sectors = main(csv_path="/path/to/your/data.csv")
```

## Output Files

The script creates the following structure:

```
sp500_sectors_output/
├── sp500_all_sectors.csv           # All companies with sector labels
└── by_sector/                      # Individual CSV files per sector
    ├── information_technology.csv
    ├── health_care.csv
    ├── financials.csv
    ├── consumer_discretionary.csv
    └── ... (one file per sector)
```

## Typical S&P 500 Sectors

The GICS classification includes 11 sectors:

1. **Information Technology**
2. **Health Care**
3. **Financials**
4. **Consumer Discretionary**
5. **Industrials**
6. **Communication Services**
7. **Consumer Staples**
8. **Energy**
9. **Utilities**
10. **Real Estate**
11. **Materials**

## Requirements

```bash
pip install pandas requests
```

## CSV File Format

If you're providing your own CSV, here's the expected format:

```csv
Symbol,Security,GICS Sector,GICS Sub-Industry
AAPL,Apple Inc.,Information Technology,Technology Hardware Storage & Peripherals
MSFT,Microsoft Corporation,Information Technology,Systems Software
JPM,JPMorgan Chase & Co.,Financials,Diversified Banks
...
```

## Example Output

```
================================================================================
S&P 500 COMPANIES BY SECTOR
================================================================================

Information Technology
  Companies: 75 (15.0%)
  Examples: AAPL, MSFT, NVDA, AVGO, CRM

Health Care
  Companies: 63 (12.6%)
  Examples: UNH, LLY, JNJ, ABBV, MRK

Financials
  Companies: 71 (14.2%)
  Examples: BRK.B, JPM, V, MA, BAC
...
```
