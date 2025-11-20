"""
S&P 500 10-K Filings Data Cleaning Script
==========================================

This script performs comprehensive data cleaning on scraped 10-K filings including:
- Data quality validation
- Text content cleaning
- Duplicate removal
- Outlier detection
- Section extraction
- Data quality reporting
"""

import pandas as pd
import numpy as np
import re
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Tuple
import warnings
warnings.filterwarnings('ignore')


class TenKDataCleaner:
    """Comprehensive data cleaner for 10-K filings"""

    def __init__(self, input_csv: str, output_csv: str):
        self.input_csv = Path(input_csv)
        self.output_csv = Path(output_csv)
        self.report = []
        self.cleaning_stats = {}

    def log(self, message: str):
        """Log message to report and print"""
        print(message)
        self.report.append(message)

    def load_data(self) -> pd.DataFrame:
        """Load CSV data"""
        self.log("="*80)
        self.log("LOADING DATA")
        self.log("="*80)

        if not self.input_csv.exists():
            raise FileNotFoundError(f"Input file not found: {self.input_csv}")

        df = pd.read_csv(self.input_csv)
        self.log(f"✓ Loaded {len(df):,} rows from {self.input_csv}")
        self.log(f"✓ Columns: {', '.join(df.columns.tolist())}")
        self.log(f"✓ Memory usage: {df.memory_usage(deep=True).sum() / 1024**2:.2f} MB\n")

        self.cleaning_stats['original_rows'] = len(df)
        return df

    def basic_quality_checks(self, df: pd.DataFrame) -> pd.DataFrame:
        """Perform basic data quality checks and cleaning"""
        self.log("="*80)
        self.log("STEP 1: BASIC DATA QUALITY CHECKS")
        self.log("="*80)

        initial_rows = len(df)

        # Check for missing values
        self.log("\n1.1 Missing Values Check:")
        missing = df.isnull().sum()
        if missing.any():
            for col, count in missing[missing > 0].items():
                pct = (count / len(df)) * 100
                self.log(f"  - {col}: {count:,} ({pct:.2f}%)")
        else:
            self.log("  ✓ No missing values found")

        # Remove rows with missing critical fields
        self.log("\n1.2 Removing rows with missing critical fields...")
        critical_fields = ['ticker', 'filing_date', 'text_content']
        before = len(df)
        df = df.dropna(subset=critical_fields)
        removed = before - len(df)
        if removed > 0:
            self.log(f"  ✗ Removed {removed:,} rows with missing critical fields")
        else:
            self.log(f"  ✓ All rows have critical fields")

        # Remove duplicates
        self.log("\n1.3 Removing duplicate filings...")
        before = len(df)
        df = df.drop_duplicates(subset=['ticker', 'filing_date', 'accession_number'], keep='first')
        removed = before - len(df)
        if removed > 0:
            self.log(f"  ✗ Removed {removed:,} duplicate filings")
        else:
            self.log(f"  ✓ No duplicates found")

        # Remove rows with empty or very short text content
        self.log("\n1.4 Removing rows with insufficient text content...")
        before = len(df)
        min_length = 1000  # Minimum characters for valid 10-K
        df['text_length'] = df['text_content'].str.len()
        df = df[df['text_length'] >= min_length]
        removed = before - len(df)
        if removed > 0:
            self.log(f"  ✗ Removed {removed:,} rows with text_content < {min_length:,} chars")
        else:
            self.log(f"  ✓ All filings have sufficient text content")

        # Validate filing dates
        self.log("\n1.5 Validating filing dates...")
        before = len(df)
        df['filing_date'] = pd.to_datetime(df['filing_date'], errors='coerce')
        df = df.dropna(subset=['filing_date'])
        removed = before - len(df)
        if removed > 0:
            self.log(f"  ✗ Removed {removed:,} rows with invalid dates")
        else:
            self.log(f"  ✓ All dates valid")

        # Remove future dates
        today = datetime.now()
        before = len(df)
        df = df[df['filing_date'] <= today]
        removed = before - len(df)
        if removed > 0:
            self.log(f"  ✗ Removed {removed:,} rows with future dates")

        # Date range
        min_date = df['filing_date'].min()
        max_date = df['filing_date'].max()
        self.log(f"  ✓ Date range: {min_date.date()} to {max_date.date()}")

        rows_removed = initial_rows - len(df)
        self.log(f"\n✓ Basic Quality Checks Complete: {rows_removed:,} rows removed\n")
        self.cleaning_stats['basic_quality_removed'] = rows_removed

        return df

    def clean_company_info(self, df: pd.DataFrame) -> pd.DataFrame:
        """Clean and standardize company information"""
        self.log("="*80)
        self.log("STEP 2: COMPANY INFORMATION CLEANING")
        self.log("="*80)

        # Clean ticker symbols
        self.log("\n2.1 Standardizing ticker symbols...")
        df['ticker'] = df['ticker'].str.strip().str.upper()
        df['ticker'] = df['ticker'].str.replace('.', '-', regex=False)
        self.log(f"  ✓ Standardized {df['ticker'].nunique()} unique tickers")

        # Clean company names
        self.log("\n2.2 Cleaning company names...")
        df['company_name'] = df['company_name'].str.strip()
        df['company_name'] = df['company_name'].str.replace(r'\s+', ' ', regex=True)
        self.log(f"  ✓ Cleaned {df['company_name'].nunique()} unique company names")

        # Verify CIK format
        self.log("\n2.3 Verifying CIK format...")
        if 'cik' in df.columns:
            df['cik'] = df['cik'].astype(str).str.zfill(10)
            self.log(f"  ✓ Standardized {df['cik'].nunique()} unique CIKs")

        self.log("\n✓ Company Information Cleaning Complete\n")
        return df

    def clean_text_content(self, df: pd.DataFrame) -> pd.DataFrame:
        """Clean text content from 10-K filings"""
        self.log("="*80)
        self.log("STEP 3: TEXT CONTENT CLEANING")
        self.log("="*80)
        self.log("This may take several minutes for large datasets...\n")

        def clean_text(text: str) -> str:
            """Apply comprehensive text cleaning"""
            if pd.isna(text) or not text:
                return ""

            # Remove HTML entities
            text = re.sub(r'&nbsp;', ' ', text)
            text = re.sub(r'&[a-zA-Z]+;', ' ', text)
            text = re.sub(r'&#\d+;', ' ', text)

            # Remove HTML tags (in case some remain)
            text = re.sub(r'<[^>]+>', ' ', text)

            # Remove XBRL/XML tags
            text = re.sub(r'<\?xml[^>]*\?>', ' ', text)
            text = re.sub(r'xmlns[^>]*>', ' ', text)

            # Remove table formatting artifacts
            text = re.sub(r'[\|│]{2,}', ' ', text)
            text = re.sub(r'[-─]{5,}', ' ', text)
            text = re.sub(r'[=]{5,}', ' ', text)

            # Remove excessive underscores
            text = re.sub(r'_{3,}', ' ', text)

            # Remove page numbers and headers (common patterns)
            text = re.sub(r'\bPage\s+\d+\s+of\s+\d+\b', ' ', text, flags=re.IGNORECASE)
            text = re.sub(r'\bTable\s+of\s+Contents\b', ' ', text, flags=re.IGNORECASE)

            # Normalize whitespace
            text = re.sub(r'\s+', ' ', text)
            text = re.sub(r'\n\s*\n\s*\n+', '\n\n', text)

            # Remove leading/trailing whitespace
            text = text.strip()

            return text

        self.log("3.1 Cleaning text content...")
        total_rows = len(df)

        # Apply cleaning with progress indicator
        cleaned_texts = []
        for idx, text in enumerate(df['text_content']):
            if (idx + 1) % 100 == 0:
                print(f"  Progress: {idx + 1:,}/{total_rows:,} ({(idx+1)/total_rows*100:.1f}%)", end='\r')
            cleaned_texts.append(clean_text(text))

        df['text_content'] = cleaned_texts
        print()  # New line after progress

        # Update text lengths
        df['text_length'] = df['text_content'].str.len()

        avg_length = df['text_length'].mean()
        median_length = df['text_length'].median()

        self.log(f"  ✓ Text cleaning complete")
        self.log(f"  ✓ Average text length: {avg_length:,.0f} characters")
        self.log(f"  ✓ Median text length: {median_length:,.0f} characters")

        self.log("\n✓ Text Content Cleaning Complete\n")
        return df

    def detect_outliers(self, df: pd.DataFrame) -> pd.DataFrame:
        """Detect and flag outliers in the dataset"""
        self.log("="*80)
        self.log("STEP 4: OUTLIER DETECTION")
        self.log("="*80)

        # Text length outliers using IQR method
        self.log("\n4.1 Detecting text length outliers...")
        Q1 = df['text_length'].quantile(0.25)
        Q3 = df['text_length'].quantile(0.75)
        IQR = Q3 - Q1
        lower_bound = Q1 - 3 * IQR  # Using 3*IQR for extreme outliers
        upper_bound = Q3 + 3 * IQR

        outliers = df[(df['text_length'] < lower_bound) | (df['text_length'] > upper_bound)]
        self.log(f"  ℹ Found {len(outliers):,} extreme outliers ({len(outliers)/len(df)*100:.2f}%)")

        if len(outliers) > 0:
            self.log(f"  ℹ Outlier range: {outliers['text_length'].min():,} - {outliers['text_length'].max():,} chars")
            self.log(f"  ℹ Normal range: {lower_bound:,.0f} - {upper_bound:,.0f} chars")
            # Don't remove them, just flag
            df['is_outlier'] = ((df['text_length'] < lower_bound) | (df['text_length'] > upper_bound))
        else:
            df['is_outlier'] = False

        # Check filings per company
        self.log("\n4.2 Analyzing filings per company...")
        filings_per_company = df.groupby('ticker').size()
        avg_filings = filings_per_company.mean()
        median_filings = filings_per_company.median()

        self.log(f"  ✓ Average filings per company: {avg_filings:.1f}")
        self.log(f"  ✓ Median filings per company: {median_filings:.0f}")

        # Companies with fewer than expected filings
        expected_filings = 5  # 5 years of data
        few_filings = filings_per_company[filings_per_company < expected_filings]
        if len(few_filings) > 0:
            self.log(f"  ℹ {len(few_filings):,} companies have < {expected_filings} filings")
            self.log(f"    Top 10 examples: {', '.join(few_filings.head(10).index.tolist())}")

        self.log("\n✓ Outlier Detection Complete\n")
        self.cleaning_stats['outliers_flagged'] = len(outliers)

        return df

    def extract_sections(self, df: pd.DataFrame) -> pd.DataFrame:
        """Extract key sections from 10-K filings"""
        self.log("="*80)
        self.log("STEP 5: SECTION EXTRACTION (OPTIONAL)")
        self.log("="*80)
        self.log("Extracting key 10-K sections...\n")

        def extract_item(text: str, item_num: str, item_name: str) -> str:
            """Extract a specific item from 10-K"""
            if pd.isna(text) or not text:
                return ""

            # Common patterns for items
            patterns = [
                rf'Item\s+{item_num}[.\s]+{item_name}(.*?)Item\s+\d+[A-Z]?[.\s]+',
                rf'ITEM\s+{item_num}[.\s]+{item_name.upper()}(.*?)ITEM\s+\d+[A-Z]?[.\s]+',
                rf'Item\s+{item_num}[.\s]+(.*?)Item\s+\d+[A-Z]?[.\s]+',
            ]

            for pattern in patterns:
                match = re.search(pattern, text, re.IGNORECASE | re.DOTALL)
                if match:
                    section_text = match.group(1).strip()
                    # Limit to reasonable length (not too long, not too short)
                    if 1000 < len(section_text) < 500000:
                        return section_text[:100000]  # Cap at 100k chars

            return ""

        # Extract key sections
        self.log("5.1 Extracting Item 1 (Business Description)...")
        df['item_1_business'] = df['text_content'].apply(
            lambda x: extract_item(x, '1', 'Business')
        )
        extracted = (df['item_1_business'].str.len() > 0).sum()
        self.log(f"  ✓ Extracted from {extracted:,}/{len(df):,} filings ({extracted/len(df)*100:.1f}%)")

        self.log("\n5.2 Extracting Item 1A (Risk Factors)...")
        df['item_1a_risk'] = df['text_content'].apply(
            lambda x: extract_item(x, '1A', 'Risk Factors')
        )
        extracted = (df['item_1a_risk'].str.len() > 0).sum()
        self.log(f"  ✓ Extracted from {extracted:,}/{len(df):,} filings ({extracted/len(df)*100:.1f}%)")

        self.log("\n5.3 Extracting Item 7 (MD&A)...")
        df['item_7_mda'] = df['text_content'].apply(
            lambda x: extract_item(x, '7', "Management's Discussion and Analysis")
        )
        extracted = (df['item_7_mda'].str.len() > 0).sum()
        self.log(f"  ✓ Extracted from {extracted:,}/{len(df):,} filings ({extracted/len(df)*100:.1f}%)")

        self.log("\n✓ Section Extraction Complete\n")
        return df

    def temporal_validation(self, df: pd.DataFrame) -> pd.DataFrame:
        """Validate temporal aspects of the data"""
        self.log("="*80)
        self.log("STEP 6: TEMPORAL VALIDATION")
        self.log("="*80)

        # Sort by ticker and date
        self.log("\n6.1 Sorting data by ticker and filing date...")
        df = df.sort_values(['ticker', 'filing_date']).reset_index(drop=True)
        self.log("  ✓ Data sorted chronologically")

        # Analyze filing patterns
        self.log("\n6.2 Analyzing filing patterns...")
        df['filing_year'] = df['filing_date'].dt.year
        df['filing_month'] = df['filing_date'].dt.month

        years = df['filing_year'].value_counts().sort_index()
        self.log(f"  ✓ Filings by year:")
        for year, count in years.items():
            self.log(f"    - {year}: {count:,} filings")

        # Most common filing months
        months = df['filing_month'].value_counts().sort_index()
        month_names = {1: 'Jan', 2: 'Feb', 3: 'Mar', 4: 'Apr', 5: 'May', 6: 'Jun',
                      7: 'Jul', 8: 'Aug', 9: 'Sep', 10: 'Oct', 11: 'Nov', 12: 'Dec'}
        self.log(f"\n  ✓ Filings by month (top 5):")
        for month, count in months.head(5).items():
            self.log(f"    - {month_names[month]}: {count:,} filings")

        self.log("\n✓ Temporal Validation Complete\n")
        return df

    def generate_summary_stats(self, df: pd.DataFrame):
        """Generate summary statistics for the cleaned dataset"""
        self.log("="*80)
        self.log("STEP 7: SUMMARY STATISTICS")
        self.log("="*80)

        self.log(f"\n📊 Dataset Overview:")
        self.log(f"  - Total filings: {len(df):,}")
        self.log(f"  - Unique companies: {df['ticker'].nunique():,}")
        self.log(f"  - Date range: {df['filing_date'].min().date()} to {df['filing_date'].max().date()}")
        self.log(f"  - Average filings per company: {len(df) / df['ticker'].nunique():.1f}")

        self.log(f"\n📝 Text Statistics:")
        self.log(f"  - Average text length: {df['text_length'].mean():,.0f} chars")
        self.log(f"  - Median text length: {df['text_length'].median():,.0f} chars")
        self.log(f"  - Min text length: {df['text_length'].min():,} chars")
        self.log(f"  - Max text length: {df['text_length'].max():,} chars")
        self.log(f"  - Total text data: {df['text_length'].sum() / 1024**2:,.1f} MB")

        if 'is_outlier' in df.columns:
            self.log(f"\n⚠️  Outliers:")
            self.log(f"  - Flagged as outliers: {df['is_outlier'].sum():,} ({df['is_outlier'].sum()/len(df)*100:.2f}%)")

        # Section extraction success rates
        section_cols = [col for col in df.columns if col.startswith('item_')]
        if section_cols:
            self.log(f"\n📑 Section Extraction:")
            for col in section_cols:
                extracted = (df[col].str.len() > 0).sum()
                pct = extracted / len(df) * 100
                self.log(f"  - {col}: {extracted:,}/{len(df):,} ({pct:.1f}%)")

        self.log(f"\n📉 Cleaning Summary:")
        self.log(f"  - Original rows: {self.cleaning_stats.get('original_rows', 0):,}")
        self.log(f"  - Rows removed: {self.cleaning_stats.get('basic_quality_removed', 0):,}")
        self.log(f"  - Final rows: {len(df):,}")
        self.log(f"  - Data retention: {len(df) / self.cleaning_stats.get('original_rows', 1) * 100:.1f}%")

        self.log("")

    def save_cleaned_data(self, df: pd.DataFrame):
        """Save cleaned data to CSV"""
        self.log("="*80)
        self.log("SAVING CLEANED DATA")
        self.log("="*80)

        # Reorder columns for better readability
        base_cols = ['ticker', 'company_name', 'cik', 'filing_date', 'filing_year',
                     'filing_month', 'accession_number', 'url', 'text_length', 'is_outlier']
        section_cols = [col for col in df.columns if col.startswith('item_')]
        other_cols = [col for col in df.columns if col not in base_cols + section_cols + ['text_content']]

        # Put text_content last (it's huge)
        column_order = [col for col in base_cols if col in df.columns] + \
                      [col for col in section_cols if col in df.columns] + \
                      [col for col in other_cols if col in df.columns] + \
                      ['text_content']

        df = df[column_order]

        self.log(f"\nSaving to: {self.output_csv}")
        df.to_csv(self.output_csv, index=False, encoding='utf-8')

        file_size = self.output_csv.stat().st_size / 1024**2
        self.log(f"✓ Saved {len(df):,} rows to {self.output_csv}")
        self.log(f"✓ File size: {file_size:.2f} MB")
        self.log(f"✓ Columns: {len(df.columns)}\n")

    def save_report(self):
        """Save cleaning report to text file"""
        report_path = self.output_csv.parent / f"{self.output_csv.stem}_REPORT.txt"

        with open(report_path, 'w', encoding='utf-8') as f:
            f.write(f"Data Cleaning Report\n")
            f.write(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
            f.write(f"{'='*80}\n\n")
            f.write('\n'.join(self.report))

        self.log(f"📄 Cleaning report saved to: {report_path}\n")

    def run(self) -> pd.DataFrame:
        """Run complete cleaning pipeline"""
        start_time = datetime.now()

        self.log("\n" + "="*80)
        self.log("S&P 500 10-K DATA CLEANING PIPELINE")
        self.log("="*80)
        self.log(f"Started: {start_time.strftime('%Y-%m-%d %H:%M:%S')}\n")

        # Load data
        df = self.load_data()

        # Run cleaning steps
        df = self.basic_quality_checks(df)
        df = self.clean_company_info(df)
        df = self.clean_text_content(df)
        df = self.detect_outliers(df)
        df = self.extract_sections(df)
        df = self.temporal_validation(df)

        # Generate summary
        self.generate_summary_stats(df)

        # Save outputs
        self.save_cleaned_data(df)
        self.save_report()

        end_time = datetime.now()
        duration = end_time - start_time

        self.log("="*80)
        self.log("✅ DATA CLEANING COMPLETE!")
        self.log("="*80)
        self.log(f"Duration: {duration}")
        self.log(f"Output: {self.output_csv}")
        self.log("="*80 + "\n")

        return df


def main():
    """Main execution function"""
    # Configuration
    INPUT_CSV = "sp500_10k_filings2.csv"
    OUTPUT_CSV = "sp500_10k_filings_CLEAN.csv"

    # Run cleaning
    cleaner = TenKDataCleaner(INPUT_CSV, OUTPUT_CSV)
    df_clean = cleaner.run()

    return df_clean


if __name__ == "__main__":
    df = main()
