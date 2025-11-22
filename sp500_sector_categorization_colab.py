"""
=================================================================================
S&P 500 SECTOR CATEGORIZATION - GOOGLE COLAB VERSION
=================================================================================

This notebook fetches S&P 500 companies and categorizes them by GICS sector.

HOW TO USE:
1. Copy this entire code into a Google Colab cell
2. Run the cell
3. Files will be saved and you can download them

Author: Reagan Schluter
=================================================================================
"""

# ============================================================================
# STEP 1: Install Required Packages
# ============================================================================

print("📦 Installing required packages...")
import subprocess
import sys

# Install packages if not already available
packages = ['pandas', 'requests', 'lxml', 'openpyxl']
for package in packages:
    try:
        __import__(package)
    except ImportError:
        print(f"Installing {package}...")
        subprocess.check_call([sys.executable, "-m", "pip", "install", "-q", package])

print("✅ All packages installed!\n")

# ============================================================================
# STEP 2: Import Libraries
# ============================================================================

import pandas as pd
import requests
from pathlib import Path
from typing import Dict, List
import os
from datetime import datetime

# ============================================================================
# STEP 3: Define the Categorizer Class
# ============================================================================

class SP500SectorCategorizer:
    """Categorizes S&P 500 companies by sector"""

    def __init__(self, output_dir: str = None):
        """
        Initialize the categorizer

        Args:
            output_dir: Directory to save output files (optional)
        """
        if output_dir:
            self.output_dir = Path(output_dir)
            self.output_dir.mkdir(parents=True, exist_ok=True)
        else:
            self.output_dir = Path("./sp500_sectors_output")
            self.output_dir.mkdir(parents=True, exist_ok=True)

    def fetch_sp500_sectors_from_wikipedia(self) -> pd.DataFrame:
        """
        Fetch S&P 500 companies with sector information from Wikipedia

        Returns:
            DataFrame with columns: Symbol, Security, GICS Sector, GICS Sub-Industry
        """
        print("🌐 Fetching S&P 500 sector data from Wikipedia...")

        try:
            url = 'https://en.wikipedia.org/wiki/List_of_S%26P_500_companies'
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
            }
            response = requests.get(url, headers=headers)
            response.raise_for_status()

            # Wikipedia has the table as the first table on the page
            tables = pd.read_html(response.text)
            df = tables[0]

            # Clean column names
            df.columns = df.columns.str.strip()

            print(f"✓ Successfully fetched {len(df)} S&P 500 companies with sector data")
            return df

        except Exception as e:
            print(f"✗ Failed to fetch from Wikipedia: {e}")
            raise Exception("Could not fetch S&P 500 sector data from Wikipedia")

    def merge_with_sector_data(self, data_df: pd.DataFrame) -> pd.DataFrame:
        """
        Merge your data with S&P 500 sector information

        Args:
            data_df: Your DataFrame with company data (must have 'ticker' or 'Symbol' column)

        Returns:
            DataFrame with sector information merged in
        """
        # Fetch sector data from Wikipedia
        sector_df = self.fetch_sp500_sectors_from_wikipedia()

        # Identify ticker column in user's data
        ticker_col = None
        for col in data_df.columns:
            if col.lower() in ['ticker', 'symbol']:
                ticker_col = col
                break

        if not ticker_col:
            raise ValueError(f"Could not find ticker/symbol column. Available columns: {', '.join(data_df.columns.tolist())}")

        print(f"\n🔗 Merging data using '{ticker_col}' column...")

        # Standardize ticker column name for merging
        data_df = data_df.copy()
        data_df['Symbol'] = data_df[ticker_col].str.upper()

        # Standardize Wikipedia ticker column
        sector_df['Symbol'] = sector_df['Symbol'].str.upper()

        # Merge the dataframes
        merged_df = data_df.merge(
            sector_df[['Symbol', 'Security', 'GICS Sector', 'GICS Sub-Industry']],
            on='Symbol',
            how='left'
        )

        # Check merge success
        matched = merged_df['GICS Sector'].notna().sum()
        total = len(merged_df)
        print(f"✓ Matched {matched}/{total} records with sector data ({matched/total*100:.1f}%)")

        if matched == 0:
            raise ValueError("No records were matched with sector data. Please check ticker symbols.")

        return merged_df

    def categorize_by_sector(self, df: pd.DataFrame) -> Dict[str, pd.DataFrame]:
        """
        Categorize companies by their GICS Sector

        Args:
            df: DataFrame with company data including sector information

        Returns:
            Dictionary with sector names as keys and DataFrames of companies as values
        """
        # Identify the sector column (it might have different names)
        sector_col = None
        for col in df.columns:
            if 'sector' in col.lower() and 'sub' not in col.lower():
                sector_col = col
                break

        if not sector_col:
            raise ValueError("Could not find sector column in the data. Available columns: " +
                           ", ".join(df.columns.tolist()))

        print(f"\n📊 Categorizing by: {sector_col}")

        # Group by sector
        sectors_dict = {}
        for sector in df[sector_col].unique():
            if pd.notna(sector):  # Skip NaN sectors
                sector_companies = df[df[sector_col] == sector].copy()
                sectors_dict[sector] = sector_companies

        return sectors_dict

    def print_sector_summary(self, sectors_dict: Dict[str, pd.DataFrame]):
        """
        Print a summary of companies by sector

        Args:
            sectors_dict: Dictionary of sectors and their companies
        """
        print("\n" + "="*80)
        print("S&P 500 COMPANIES BY SECTOR")
        print("="*80)

        # Sort sectors by number of companies
        sorted_sectors = sorted(sectors_dict.items(),
                              key=lambda x: len(x[1]),
                              reverse=True)

        total_companies = sum(len(df) for df in sectors_dict.values())

        for sector, companies_df in sorted_sectors:
            count = len(companies_df)
            percentage = (count / total_companies) * 100

            # Find ticker/symbol column for examples
            ticker_col = 'Symbol'
            if ticker_col not in companies_df.columns:
                for col in companies_df.columns:
                    if col.lower() in ['ticker', 'symbol']:
                        ticker_col = col
                        break

            # Get unique companies for examples
            if ticker_col in companies_df.columns:
                unique_tickers = companies_df[ticker_col].unique()[:5]
                examples = ', '.join([str(t) for t in unique_tickers])
            else:
                examples = "N/A"

            print(f"\n{sector}")
            print(f"  Records: {count} ({percentage:.1f}%)")
            print(f"  Examples: {examples}")

        print(f"\n{'='*80}")
        print(f"Total: {total_companies} records across {len(sectors_dict)} sectors")
        print("="*80)

    def save_sectors_to_csv(self, sectors_dict: Dict[str, pd.DataFrame],
                           combined: bool = True, separate: bool = True):
        """
        Save sector data to CSV files

        Args:
            sectors_dict: Dictionary of sectors and their companies
            combined: If True, save all companies with sector labels to one CSV
            separate: If True, save separate CSV files for each sector
        """
        print(f"\n💾 Saving data to: {self.output_dir}")

        # Save combined file with all companies
        if combined:
            all_companies = pd.concat(sectors_dict.values(), ignore_index=True)
            combined_path = self.output_dir / "sp500_all_sectors.csv"
            all_companies.to_csv(combined_path, index=False)
            print(f"  ✓ Combined file: {combined_path}")

        # Save separate files for each sector
        if separate:
            sector_dir = self.output_dir / "by_sector"
            sector_dir.mkdir(exist_ok=True)

            for sector, companies_df in sectors_dict.items():
                # Create safe filename from sector name
                safe_name = sector.replace(' ', '_').replace('&', 'and').lower()
                sector_path = sector_dir / f"{safe_name}.csv"
                companies_df.to_csv(sector_path, index=False)
                print(f"  ✓ {sector}: {sector_path} ({len(companies_df)} companies)")

        print("\n✅ All files saved successfully!")

        return self.output_dir

    def save_to_excel(self, sectors_dict: Dict[str, pd.DataFrame],
                     filename: str = "sp500_sectors.xlsx"):
        """
        Save all sectors to a single Excel file with multiple sheets

        Args:
            sectors_dict: Dictionary of sectors and their companies
            filename: Name of the Excel file
        """
        excel_path = self.output_dir / filename

        print(f"\n📊 Creating Excel file: {excel_path}")

        with pd.ExcelWriter(excel_path, engine='openpyxl') as writer:
            # Create summary sheet
            summary_data = []
            for sector, companies_df in sectors_dict.items():
                summary_data.append({
                    'Sector': sector,
                    'Number of Companies': len(companies_df),
                    'Percentage': f"{(len(companies_df) / sum(len(df) for df in sectors_dict.values()) * 100):.1f}%"
                })

            summary_df = pd.DataFrame(summary_data)
            summary_df.to_excel(writer, sheet_name='Summary', index=False)

            # Create a sheet for each sector
            for sector, companies_df in sectors_dict.items():
                # Excel sheet names can't be longer than 31 characters
                sheet_name = sector[:31]
                companies_df.to_excel(writer, sheet_name=sheet_name, index=False)

        print(f"  ✓ Excel file created with {len(sectors_dict) + 1} sheets")
        return excel_path

    def get_companies_by_sector(self, sectors_dict: Dict[str, pd.DataFrame],
                               sector_name: str) -> pd.DataFrame:
        """
        Get all companies in a specific sector

        Args:
            sectors_dict: Dictionary of sectors and their companies
            sector_name: Name of the sector (case-insensitive)

        Returns:
            DataFrame of companies in that sector
        """
        # Case-insensitive search
        for sector, companies_df in sectors_dict.items():
            if sector.lower() == sector_name.lower():
                return companies_df

        # If exact match not found, try partial match
        for sector, companies_df in sectors_dict.items():
            if sector_name.lower() in sector.lower():
                return companies_df

        available_sectors = list(sectors_dict.keys())
        raise ValueError(f"Sector '{sector_name}' not found. Available sectors: {available_sectors}")

    def create_sector_visualization_data(self, sectors_dict: Dict[str, pd.DataFrame]) -> pd.DataFrame:
        """
        Create a summary DataFrame for visualization

        Args:
            sectors_dict: Dictionary of sectors and their companies

        Returns:
            DataFrame with sector statistics
        """
        total_companies = sum(len(df) for df in sectors_dict.values())

        viz_data = []
        for sector, companies_df in sectors_dict.items():
            count = len(companies_df)
            viz_data.append({
                'Sector': sector,
                'Count': count,
                'Percentage': round((count / total_companies) * 100, 2)
            })

        viz_df = pd.DataFrame(viz_data)
        viz_df = viz_df.sort_values('Count', ascending=False).reset_index(drop=True)

        return viz_df


# ============================================================================
# STEP 4: Main Execution Function
# ============================================================================

def run_sector_categorization(csv_path: str,
                             save_excel: bool = True,
                             save_csv: bool = True):
    """
    Main function to categorize S&P 500 companies by sector

    Args:
        csv_path: Path to your CSV file with company data (must have 'ticker' or 'Symbol' column)
        save_excel: Whether to save as Excel file (default: True)
        save_csv: Whether to save as CSV files (default: True)

    Returns:
        Dictionary of sectors with their companies
    """
    print("="*80)
    print("🚀 S&P 500 SECTOR CATEGORIZATION")
    print("="*80)
    print(f"⏰ Started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")

    # Initialize categorizer
    categorizer = SP500SectorCategorizer(output_dir="sp500_sectors_output")

    # Read your data file
    if not os.path.exists(csv_path):
        raise FileNotFoundError(f"CSV file not found: {csv_path}")

    print(f"📂 Reading data from: {csv_path}")
    data_df = pd.read_csv(csv_path)
    print(f"✓ Loaded {len(data_df)} records from file")

    # Merge with sector data
    df = categorizer.merge_with_sector_data(data_df)

    # Categorize by sector
    sectors_dict = categorizer.categorize_by_sector(df)

    # Print summary
    categorizer.print_sector_summary(sectors_dict)

    # Create visualization data
    viz_data = categorizer.create_sector_visualization_data(sectors_dict)
    print("\n📈 Sector Distribution:")
    print(viz_data.to_string(index=False))

    # Save to files
    if save_csv:
        output_dir = categorizer.save_sectors_to_csv(sectors_dict, combined=True, separate=True)

    if save_excel:
        excel_path = categorizer.save_to_excel(sectors_dict)

    print(f"\n⏰ Completed at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("="*80)

    return sectors_dict, categorizer


# ============================================================================
# STEP 5: RUN THE CODE
# ============================================================================

if __name__ == "__main__":
    # ========================================
    # OPTION 1: Use CSV file from Google Drive
    # ========================================
    # Mount Google Drive
    from google.colab import drive
    drive.mount('/content/drive')

    # Path to your CSV file
    CSV_PATH = "/content/drive/MyDrive/ACC 380K Case 2/Clean/sp500_10k_filings_CLEAN.csv"

    sectors_dict, categorizer = run_sector_categorization(csv_path=CSV_PATH)

    # ========================================
    # BONUS: Get records from specific sectors
    # ========================================
    print("\n" + "="*80)
    print("💡 EXAMPLE: Getting records from specific sectors")
    print("="*80)

    # Example: Get all technology records
    try:
        tech_records = categorizer.get_companies_by_sector(sectors_dict, "Information Technology")
        print(f"\n🖥️  Information Technology Records: {len(tech_records)}")

        # Show available columns
        display_cols = []
        for col in ['ticker', 'Symbol', 'company_name', 'Security', 'filing_date']:
            if col in tech_records.columns:
                display_cols.append(col)

        if display_cols:
            print(tech_records[display_cols].head(10).to_string(index=False))
    except Exception as e:
        print(f"Note: {e}")

    # Example: Get all healthcare records
    try:
        healthcare = categorizer.get_companies_by_sector(sectors_dict, "Health Care")
        print(f"\n🏥 Health Care Records: {len(healthcare)}")

        # Show available columns
        display_cols = []
        for col in ['ticker', 'Symbol', 'company_name', 'Security', 'filing_date']:
            if col in healthcare.columns:
                display_cols.append(col)

        if display_cols:
            print(healthcare[display_cols].head(10).to_string(index=False))
    except Exception as e:
        print(f"Note: {e}")

    # ========================================
    # Download Files
    # ========================================
    print("\n" + "="*80)
    print("📥 TO DOWNLOAD FILES IN COLAB:")
    print("="*80)
    print("1. Click the folder icon (📁) on the left sidebar")
    print("2. Navigate to 'sp500_sectors_output' folder")
    print("3. Right-click on any file and select 'Download'")
    print("\nFiles created:")
    print("  - sp500_all_sectors.csv (all companies)")
    print("  - sp500_sectors.xlsx (Excel with all sectors)")
    print("  - by_sector/*.csv (individual sector files)")
    print("="*80)

    print("\n✅ ALL DONE! You can now download the files or use the sectors_dict variable for further analysis.")
