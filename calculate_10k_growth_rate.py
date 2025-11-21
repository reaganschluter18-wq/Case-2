#!/usr/bin/env python3
"""
10-K Document Growth Rate Calculator
=====================================

Calculates the average growth rate of each company's 10-K filing length
over a 5-year span. Uses Compound Annual Growth Rate (CAGR) formula.

Usage:
    python calculate_10k_growth_rate.py <input_csv>

Author: Analysis script for Case-2
Date: 2025-11-21
"""

import pandas as pd
import numpy as np
from pathlib import Path
from datetime import datetime
from typing import Dict, List
import warnings
warnings.filterwarnings('ignore')


class TenKGrowthRateCalculator:
    """Calculate average growth rates for 10-K document lengths"""

    def __init__(self, input_csv: str, output_dir: str = None):
        self.input_csv = Path(input_csv)

        if output_dir:
            self.output_dir = Path(output_dir)
        else:
            self.output_dir = self.input_csv.parent / "growth_rate_analysis"

        self.output_dir.mkdir(parents=True, exist_ok=True)

        self.df = None
        print(f"📁 Output directory: {self.output_dir}\n")

    def load_data(self) -> pd.DataFrame:
        """Load 10-K data from CSV"""
        print("="*80)
        print("LOADING 10-K DATA")
        print("="*80)

        if not self.input_csv.exists():
            raise FileNotFoundError(f"Input file not found: {self.input_csv}")

        df = pd.read_csv(self.input_csv)
        print(f"✓ Loaded {len(df):,} filings from {self.input_csv}")

        # Parse dates and add year column
        df['filing_date'] = pd.to_datetime(df['filing_date'])
        df['filing_year'] = df['filing_date'].dt.year

        # Ensure text_length exists
        if 'text_length' not in df.columns and 'text_content' in df.columns:
            print("  Calculating text lengths...")
            df['text_length'] = df['text_content'].str.len()

        print(f"✓ Date range: {df['filing_date'].min().date()} to {df['filing_date'].max().date()}")
        print(f"✓ Unique companies: {df['ticker'].nunique():,}")
        print(f"✓ Years covered: {sorted(df['filing_year'].unique())}\n")

        self.df = df
        return df

    def calculate_cagr(self, beginning_value: float, ending_value: float,
                       num_years: float) -> float:
        """
        Calculate Compound Annual Growth Rate (CAGR)

        Formula: CAGR = ((Ending Value / Beginning Value) ^ (1 / Number of Years)) - 1

        Args:
            beginning_value: Initial value
            ending_value: Final value
            num_years: Number of years between measurements

        Returns:
            CAGR as a percentage
        """
        if beginning_value <= 0 or num_years <= 0:
            return 0.0

        cagr = ((ending_value / beginning_value) ** (1 / num_years)) - 1
        return cagr * 100  # Convert to percentage

    def calculate_simple_growth_rate(self, beginning_value: float,
                                     ending_value: float,
                                     num_years: float) -> float:
        """
        Calculate simple average annual growth rate

        Formula: Simple Growth Rate = ((Ending - Beginning) / Beginning / Years) * 100

        Args:
            beginning_value: Initial value
            ending_value: Final value
            num_years: Number of years between measurements

        Returns:
            Simple annual growth rate as a percentage
        """
        if beginning_value <= 0 or num_years <= 0:
            return 0.0

        total_growth = ((ending_value - beginning_value) / beginning_value) * 100
        avg_annual_growth = total_growth / num_years
        return avg_annual_growth

    def analyze_company_growth_rates(self) -> pd.DataFrame:
        """Calculate growth rates for each company with multiple filings"""
        print("="*80)
        print("CALCULATING COMPANY GROWTH RATES")
        print("="*80)

        # Group by company
        company_counts = self.df['ticker'].value_counts()
        multi_filing_companies = company_counts[company_counts >= 2]

        if len(multi_filing_companies) == 0:
            print("⚠️  No companies found with 2+ filings. Cannot calculate growth rates.\n")
            return pd.DataFrame()

        print(f"\nAnalyzing {len(multi_filing_companies)} companies with 2+ filings...\n")

        growth_data = []

        for ticker in multi_filing_companies.index:
            # Get company's filings sorted by date
            company_df = self.df[self.df['ticker'] == ticker].sort_values('filing_date')

            if len(company_df) < 2:
                continue

            # Get first and last filings
            first_filing = company_df.iloc[0]
            last_filing = company_df.iloc[-1]

            # Calculate time span
            time_delta = last_filing['filing_date'] - first_filing['filing_date']
            years_span = time_delta.days / 365.25

            # Get document lengths
            beginning_length = first_filing['text_length']
            ending_length = last_filing['text_length']

            # Calculate growth metrics
            absolute_change = ending_length - beginning_length
            total_growth_pct = ((ending_length - beginning_length) / beginning_length * 100) if beginning_length > 0 else 0

            # Calculate CAGR (Compound Annual Growth Rate)
            cagr = self.calculate_cagr(beginning_length, ending_length, years_span)

            # Calculate simple average annual growth rate
            simple_avg_growth = self.calculate_simple_growth_rate(
                beginning_length, ending_length, years_span
            )

            # Store results
            result = {
                'ticker': ticker,
                'company_name': first_filing.get('company_name', ''),
                'num_filings': len(company_df),
                'first_year': first_filing['filing_year'],
                'last_year': last_filing['filing_year'],
                'years_span': round(years_span, 2),
                'first_length_chars': int(beginning_length),
                'last_length_chars': int(ending_length),
                'absolute_change_chars': int(absolute_change),
                'total_growth_pct': round(total_growth_pct, 2),
                'cagr_pct': round(cagr, 2),
                'avg_annual_growth_pct': round(simple_avg_growth, 2),
            }

            # Calculate average length across all filings
            result['avg_length_chars'] = int(company_df['text_length'].mean())
            result['median_length_chars'] = int(company_df['text_length'].median())

            growth_data.append(result)

        # Create DataFrame
        growth_df = pd.DataFrame(growth_data)

        # Sort by CAGR descending
        growth_df = growth_df.sort_values('cagr_pct', ascending=False)

        return growth_df

    def display_summary_statistics(self, growth_df: pd.DataFrame):
        """Display summary statistics of growth rates"""
        print("\n📊 SUMMARY STATISTICS")
        print("="*80)

        print(f"\nCompanies analyzed: {len(growth_df):,}")
        print(f"\nAverage Growth Metrics (across all companies):")
        print(f"  - Average CAGR: {growth_df['cagr_pct'].mean():+.2f}% per year")
        print(f"  - Median CAGR: {growth_df['cagr_pct'].median():+.2f}% per year")
        print(f"  - Average simple growth rate: {growth_df['avg_annual_growth_pct'].mean():+.2f}% per year")
        print(f"  - Average total growth: {growth_df['total_growth_pct'].mean():+.2f}%")

        print(f"\nGrowth Rate Distribution:")
        print(f"  - Min CAGR: {growth_df['cagr_pct'].min():+.2f}%")
        print(f"  - 25th percentile: {growth_df['cagr_pct'].quantile(0.25):+.2f}%")
        print(f"  - 50th percentile (median): {growth_df['cagr_pct'].quantile(0.50):+.2f}%")
        print(f"  - 75th percentile: {growth_df['cagr_pct'].quantile(0.75):+.2f}%")
        print(f"  - Max CAGR: {growth_df['cagr_pct'].max():+.2f}%")

        # Count companies by growth category
        high_growth = len(growth_df[growth_df['cagr_pct'] > 10])
        moderate_growth = len(growth_df[(growth_df['cagr_pct'] > 0) & (growth_df['cagr_pct'] <= 10)])
        negative_growth = len(growth_df[growth_df['cagr_pct'] <= 0])

        print(f"\nGrowth Categories:")
        print(f"  - High growth (>10% CAGR): {high_growth} companies ({high_growth/len(growth_df)*100:.1f}%)")
        print(f"  - Moderate growth (0-10% CAGR): {moderate_growth} companies ({moderate_growth/len(growth_df)*100:.1f}%)")
        print(f"  - Negative/No growth (≤0% CAGR): {negative_growth} companies ({negative_growth/len(growth_df)*100:.1f}%)")

    def display_top_companies(self, growth_df: pd.DataFrame, n: int = 10):
        """Display top companies by growth rate"""
        print("\n\n📈 TOP COMPANIES BY GROWTH RATE")
        print("="*80)

        print(f"\nTop {n} Highest CAGR:")
        top_growth = growth_df.head(n)
        for idx, row in top_growth.iterrows():
            print(f"  {row['ticker']:6s} - {row['company_name'][:40]:40s}")
            print(f"          CAGR: {row['cagr_pct']:+6.2f}% | Total Growth: {row['total_growth_pct']:+6.1f}% | {row['first_year']}-{row['last_year']} ({row['years_span']:.1f} years)")
            print(f"          {row['first_length_chars']:,} → {row['last_length_chars']:,} chars ({row['absolute_change_chars']:+,} chars)")

        print(f"\n\nTop {n} Lowest CAGR (Shrinking 10-Ks):")
        bottom_growth = growth_df.tail(n).sort_values('cagr_pct')
        for idx, row in bottom_growth.iterrows():
            print(f"  {row['ticker']:6s} - {row['company_name'][:40]:40s}")
            print(f"          CAGR: {row['cagr_pct']:+6.2f}% | Total Growth: {row['total_growth_pct']:+6.1f}% | {row['first_year']}-{row['last_year']} ({row['years_span']:.1f} years)")
            print(f"          {row['first_length_chars']:,} → {row['last_length_chars']:,} chars ({row['absolute_change_chars']:+,} chars)")

    def save_results(self, growth_df: pd.DataFrame):
        """Save results to CSV"""
        if growth_df.empty:
            print("\n⚠️  No results to save.\n")
            return

        output_csv = self.output_dir / "company_growth_rates.csv"
        growth_df.to_csv(output_csv, index=False)

        print("\n\n💾 SAVED RESULTS")
        print("="*80)
        print(f"✓ Growth rates saved to: {output_csv}")
        print(f"✓ Total companies: {len(growth_df):,}")
        print(f"✓ Columns: {', '.join(growth_df.columns.tolist())}\n")

    def run_analysis(self):
        """Run complete growth rate analysis"""
        start_time = datetime.now()

        print("\n" + "="*80)
        print("10-K DOCUMENT GROWTH RATE ANALYSIS")
        print("="*80)
        print(f"Started: {start_time.strftime('%Y-%m-%d %H:%M:%S')}\n")

        # Load data
        self.load_data()

        # Calculate growth rates
        growth_df = self.analyze_company_growth_rates()

        if not growth_df.empty:
            # Display results
            self.display_summary_statistics(growth_df)
            self.display_top_companies(growth_df)

            # Save results
            self.save_results(growth_df)

        end_time = datetime.now()
        duration = end_time - start_time

        print("\n" + "="*80)
        print("✅ ANALYSIS COMPLETE!")
        print("="*80)
        print(f"Duration: {duration}")
        print(f"Output directory: {self.output_dir}")
        print("="*80 + "\n")

        return growth_df


def main():
    """Main execution function"""
    import sys

    # Check for input CSV
    if len(sys.argv) > 1:
        input_csv = sys.argv[1]
    else:
        # Try to find CSV in current directory
        csv_files = list(Path('.').glob('*10k*.csv'))
        if csv_files:
            input_csv = str(csv_files[0])
            print(f"Found CSV file: {input_csv}\n")
        else:
            print("Usage: python calculate_10k_growth_rate.py <input_csv>")
            print("\nNo 10-K CSV files found in current directory.")
            print("Please provide path to your 10-K data CSV file.")
            return

    # Check if file exists
    if not Path(input_csv).exists():
        print(f"Error: File not found: {input_csv}")
        return

    # Run analysis
    calculator = TenKGrowthRateCalculator(input_csv)
    growth_df = calculator.run_analysis()

    return growth_df


if __name__ == "__main__":
    main()
