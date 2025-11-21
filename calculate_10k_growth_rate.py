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
import matplotlib.pyplot as plt
import seaborn as sns
from pathlib import Path
from datetime import datetime
from typing import Dict, List
import warnings
warnings.filterwarnings('ignore')

# ============================================================================
# CONFIGURATION - PUT YOUR CLEAN DATA PATH HERE
# ============================================================================
# Option 1: For Google Colab - Put your Google Drive path here after mounting
# Example: CLEANED_DATA_PATH = "/content/drive/MyDrive/10K_Data/cleaned_10k_data.csv"
CLEANED_DATA_PATH = "/content/drive/MyDrive/ACC 380K Case 2/Clean/sp500_10k_filings_CLEAN.csv"

# Option 2: For local files - Put your local file path here
# Example: CLEANED_DATA_PATH = "/home/user/Case-2/cleaned_10k_data.csv"
# CLEANED_DATA_PATH = None

# Option 3: For Google Drive shareable links (Colab only)
# If you have a shareable link, use gdown to download it first:
# !pip install gdown
# !gdown --id YOUR_FILE_ID -O /content/cleaned_data.csv
# Then set: CLEANED_DATA_PATH = "/content/cleaned_data.csv"

# Set style for better-looking plots
sns.set_style("whitegrid")
plt.rcParams['figure.figsize'] = (12, 8)
plt.rcParams['font.size'] = 10


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

    def create_visualizations(self, growth_df: pd.DataFrame):
        """Create comprehensive visualizations of growth rate data"""
        if growth_df.empty:
            print("⚠️  No data to visualize.\n")
            return

        print("\n📊 GENERATING VISUALIZATIONS")
        print("="*80)

        # 1. CAGR Distribution Histogram
        self._plot_cagr_distribution(growth_df)

        # 2. Top 20 Companies Bar Chart
        self._plot_top_companies(growth_df)

        # 3. Scatter Plot: Initial Length vs Growth Rate
        self._plot_length_vs_growth(growth_df)

        # 4. Growth Categories Pie Chart
        self._plot_growth_categories(growth_df)

        # 5. Multi-panel Overview
        self._plot_comprehensive_overview(growth_df)

        print(f"\n✓ All visualizations saved to: {self.output_dir}\n")

    def _plot_cagr_distribution(self, growth_df: pd.DataFrame):
        """Plot histogram of CAGR distribution"""
        fig, ax = plt.subplots(figsize=(12, 6))

        # Histogram
        n, bins, patches = ax.hist(growth_df['cagr_pct'], bins=30,
                                     edgecolor='black', alpha=0.7, color='#2E86AB')

        # Color bars based on value
        for i, patch in enumerate(patches):
            if bins[i] < 0:
                patch.set_facecolor('#E63946')  # Red for negative
            elif bins[i] < 5:
                patch.set_facecolor('#F77F00')  # Orange for low
            elif bins[i] < 10:
                patch.set_facecolor('#06AED5')  # Blue for moderate
            else:
                patch.set_facecolor('#06D6A0')  # Green for high

        # Add mean and median lines
        mean_cagr = growth_df['cagr_pct'].mean()
        median_cagr = growth_df['cagr_pct'].median()

        ax.axvline(mean_cagr, color='darkred', linestyle='--', linewidth=2,
                   label=f'Mean: {mean_cagr:.2f}%')
        ax.axvline(median_cagr, color='darkblue', linestyle='--', linewidth=2,
                   label=f'Median: {median_cagr:.2f}%')

        ax.set_xlabel('CAGR (%)', fontsize=12, fontweight='bold')
        ax.set_ylabel('Number of Companies', fontsize=12, fontweight='bold')
        ax.set_title('Distribution of 10-K Document Growth Rates (CAGR)',
                     fontsize=14, fontweight='bold', pad=20)
        ax.legend(fontsize=11)
        ax.grid(True, alpha=0.3)

        plt.tight_layout()
        plt.savefig(self.output_dir / 'cagr_distribution.png', dpi=300, bbox_inches='tight')
        plt.close()
        print(f"  ✓ Saved: cagr_distribution.png")

    def _plot_top_companies(self, growth_df: pd.DataFrame, n: int = 20):
        """Plot top companies by CAGR"""
        fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(16, 8))

        # Top 20 highest CAGR
        top_n = growth_df.head(n)
        colors_top = ['#06D6A0' if x > 0 else '#E63946' for x in top_n['cagr_pct']]

        ax1.barh(range(len(top_n)), top_n['cagr_pct'], color=colors_top, edgecolor='black')
        ax1.set_yticks(range(len(top_n)))
        ax1.set_yticklabels(top_n['ticker'], fontsize=9)
        ax1.set_xlabel('CAGR (%)', fontsize=11, fontweight='bold')
        ax1.set_title(f'Top {n} Companies by Highest CAGR', fontsize=12, fontweight='bold')
        ax1.axvline(0, color='black', linewidth=0.8)
        ax1.grid(True, alpha=0.3, axis='x')
        ax1.invert_yaxis()

        # Bottom 20 (lowest CAGR)
        bottom_n = growth_df.tail(n).sort_values('cagr_pct')
        colors_bottom = ['#E63946' if x < 0 else '#06D6A0' for x in bottom_n['cagr_pct']]

        ax2.barh(range(len(bottom_n)), bottom_n['cagr_pct'], color=colors_bottom, edgecolor='black')
        ax2.set_yticks(range(len(bottom_n)))
        ax2.set_yticklabels(bottom_n['ticker'], fontsize=9)
        ax2.set_xlabel('CAGR (%)', fontsize=11, fontweight='bold')
        ax2.set_title(f'Bottom {n} Companies by Lowest CAGR', fontsize=12, fontweight='bold')
        ax2.axvline(0, color='black', linewidth=0.8)
        ax2.grid(True, alpha=0.3, axis='x')
        ax2.invert_yaxis()

        plt.tight_layout()
        plt.savefig(self.output_dir / 'top_bottom_companies.png', dpi=300, bbox_inches='tight')
        plt.close()
        print(f"  ✓ Saved: top_bottom_companies.png")

    def _plot_length_vs_growth(self, growth_df: pd.DataFrame):
        """Scatter plot of initial document length vs growth rate"""
        fig, ax = plt.subplots(figsize=(12, 8))

        # Create scatter plot with color gradient
        scatter = ax.scatter(growth_df['first_length_chars'],
                            growth_df['cagr_pct'],
                            c=growth_df['cagr_pct'],
                            cmap='RdYlGn',
                            s=100,
                            alpha=0.6,
                            edgecolors='black',
                            linewidth=0.5)

        # Add colorbar
        cbar = plt.colorbar(scatter, ax=ax)
        cbar.set_label('CAGR (%)', fontsize=11, fontweight='bold')

        # Add horizontal line at 0
        ax.axhline(0, color='black', linestyle='--', linewidth=1, alpha=0.5)

        # Labels for outliers
        top_growth = growth_df.nlargest(5, 'cagr_pct')
        for _, row in top_growth.iterrows():
            ax.annotate(row['ticker'],
                       xy=(row['first_length_chars'], row['cagr_pct']),
                       xytext=(10, 10), textcoords='offset points',
                       fontsize=8, fontweight='bold',
                       bbox=dict(boxstyle='round,pad=0.3', facecolor='yellow', alpha=0.7),
                       arrowprops=dict(arrowstyle='->', connectionstyle='arc3,rad=0'))

        ax.set_xlabel('Initial 10-K Length (characters)', fontsize=12, fontweight='bold')
        ax.set_ylabel('CAGR (%)', fontsize=12, fontweight='bold')
        ax.set_title('Relationship: Initial Document Length vs Growth Rate',
                     fontsize=14, fontweight='bold', pad=20)
        ax.grid(True, alpha=0.3)

        # Format x-axis with commas
        ax.ticklabel_format(style='plain', axis='x')

        plt.tight_layout()
        plt.savefig(self.output_dir / 'length_vs_growth.png', dpi=300, bbox_inches='tight')
        plt.close()
        print(f"  ✓ Saved: length_vs_growth.png")

    def _plot_growth_categories(self, growth_df: pd.DataFrame):
        """Pie chart of growth categories"""
        fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(14, 6))

        # Categorize by CAGR
        high_growth = len(growth_df[growth_df['cagr_pct'] > 10])
        moderate_growth = len(growth_df[(growth_df['cagr_pct'] > 0) & (growth_df['cagr_pct'] <= 10)])
        negative_growth = len(growth_df[growth_df['cagr_pct'] <= 0])

        categories = ['High Growth\n(>10%)', 'Moderate Growth\n(0-10%)', 'Negative/No Growth\n(≤0%)']
        sizes = [high_growth, moderate_growth, negative_growth]
        colors = ['#06D6A0', '#06AED5', '#E63946']
        explode = (0.05, 0.05, 0.05)

        ax1.pie(sizes, explode=explode, labels=categories, colors=colors,
                autopct='%1.1f%%', shadow=True, startangle=90,
                textprops={'fontsize': 11, 'fontweight': 'bold'})
        ax1.set_title('Companies by Growth Category', fontsize=13, fontweight='bold', pad=20)

        # Box plot of CAGR distribution
        ax2.boxplot(growth_df['cagr_pct'], vert=True, patch_artist=True,
                   boxprops=dict(facecolor='#2E86AB', alpha=0.7),
                   medianprops=dict(color='red', linewidth=2),
                   whiskerprops=dict(linewidth=1.5),
                   capprops=dict(linewidth=1.5))
        ax2.axhline(0, color='black', linestyle='--', linewidth=1, alpha=0.5)
        ax2.set_ylabel('CAGR (%)', fontsize=12, fontweight='bold')
        ax2.set_title('CAGR Distribution (Box Plot)', fontsize=13, fontweight='bold', pad=20)
        ax2.grid(True, alpha=0.3, axis='y')

        # Add statistics text
        stats_text = f"Mean: {growth_df['cagr_pct'].mean():.2f}%\n"
        stats_text += f"Median: {growth_df['cagr_pct'].median():.2f}%\n"
        stats_text += f"Std Dev: {growth_df['cagr_pct'].std():.2f}%"
        ax2.text(1.15, growth_df['cagr_pct'].mean(), stats_text,
                fontsize=10, bbox=dict(boxstyle='round', facecolor='wheat', alpha=0.7))

        plt.tight_layout()
        plt.savefig(self.output_dir / 'growth_categories.png', dpi=300, bbox_inches='tight')
        plt.close()
        print(f"  ✓ Saved: growth_categories.png")

    def _plot_comprehensive_overview(self, growth_df: pd.DataFrame):
        """Create comprehensive multi-panel overview"""
        fig = plt.figure(figsize=(16, 10))
        gs = fig.add_gridspec(3, 2, hspace=0.3, wspace=0.3)

        # Panel 1: CAGR histogram
        ax1 = fig.add_subplot(gs[0, :])
        ax1.hist(growth_df['cagr_pct'], bins=40, edgecolor='black',
                alpha=0.7, color='#2E86AB')
        ax1.axvline(growth_df['cagr_pct'].mean(), color='red',
                   linestyle='--', linewidth=2, label=f"Mean: {growth_df['cagr_pct'].mean():.2f}%")
        ax1.set_xlabel('CAGR (%)', fontweight='bold')
        ax1.set_ylabel('Count', fontweight='bold')
        ax1.set_title('Overall CAGR Distribution', fontweight='bold', fontsize=12)
        ax1.legend()
        ax1.grid(True, alpha=0.3)

        # Panel 2: Total growth vs CAGR
        ax2 = fig.add_subplot(gs[1, 0])
        scatter2 = ax2.scatter(growth_df['total_growth_pct'], growth_df['cagr_pct'],
                              alpha=0.5, c=growth_df['years_span'], cmap='viridis', s=50)
        ax2.set_xlabel('Total Growth (%)', fontweight='bold')
        ax2.set_ylabel('CAGR (%)', fontweight='bold')
        ax2.set_title('Total Growth vs CAGR', fontweight='bold', fontsize=11)
        ax2.grid(True, alpha=0.3)
        plt.colorbar(scatter2, ax=ax2, label='Years Span')

        # Panel 3: Years span distribution
        ax3 = fig.add_subplot(gs[1, 1])
        ax3.hist(growth_df['years_span'], bins=20, edgecolor='black',
                alpha=0.7, color='#F77F00')
        ax3.set_xlabel('Time Span (Years)', fontweight='bold')
        ax3.set_ylabel('Count', fontweight='bold')
        ax3.set_title('Distribution of Analysis Time Spans', fontweight='bold', fontsize=11)
        ax3.grid(True, alpha=0.3)

        # Panel 4: First vs Last length
        ax4 = fig.add_subplot(gs[2, 0])
        ax4.scatter(growth_df['first_length_chars'], growth_df['last_length_chars'],
                   alpha=0.5, c=growth_df['cagr_pct'], cmap='RdYlGn', s=50)
        # Add diagonal line (no change)
        max_val = max(growth_df['first_length_chars'].max(), growth_df['last_length_chars'].max())
        ax4.plot([0, max_val], [0, max_val], 'k--', alpha=0.5, label='No Change')
        ax4.set_xlabel('First Filing Length (chars)', fontweight='bold')
        ax4.set_ylabel('Last Filing Length (chars)', fontweight='bold')
        ax4.set_title('First vs Last Filing Length', fontweight='bold', fontsize=11)
        ax4.legend()
        ax4.grid(True, alpha=0.3)
        ax4.ticklabel_format(style='plain')

        # Panel 5: Number of filings
        ax5 = fig.add_subplot(gs[2, 1])
        filing_counts = growth_df['num_filings'].value_counts().sort_index()
        ax5.bar(filing_counts.index, filing_counts.values, edgecolor='black',
               alpha=0.7, color='#06AED5')
        ax5.set_xlabel('Number of Filings', fontweight='bold')
        ax5.set_ylabel('Count', fontweight='bold')
        ax5.set_title('Distribution of Filing Counts', fontweight='bold', fontsize=11)
        ax5.grid(True, alpha=0.3, axis='y')

        # Main title
        fig.suptitle('10-K Document Growth Rate Analysis - Comprehensive Overview',
                    fontsize=16, fontweight='bold', y=0.995)

        plt.savefig(self.output_dir / 'comprehensive_overview.png', dpi=300, bbox_inches='tight')
        plt.close()
        print(f"  ✓ Saved: comprehensive_overview.png")

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

            # Create visualizations
            self.create_visualizations(growth_df)

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

    # Check for input CSV - Priority order:
    # 1. CLEANED_DATA_PATH configuration
    # 2. Command line argument
    # 3. Auto-detect CSV in current directory

    if CLEANED_DATA_PATH is not None:
        input_csv = CLEANED_DATA_PATH
        print(f"Using configured data path: {input_csv}\n")
    elif len(sys.argv) > 1:
        input_csv = sys.argv[1]
    else:
        # Try to find CSV in current directory
        csv_files = list(Path('.').glob('*10k*.csv'))
        if csv_files:
            input_csv = str(csv_files[0])
            print(f"Found CSV file: {input_csv}\n")
        else:
            print("Usage: python calculate_10k_growth_rate.py <input_csv>")
            print("\nOR set CLEANED_DATA_PATH in the configuration section at the top of this file.")
            print("\nNo 10-K CSV files found in current directory.")
            print("Please provide path to your 10-K data CSV file.")
            return

    # Check if file exists
    if not Path(input_csv).exists():
        print(f"Error: File not found: {input_csv}")
        print("\nMake sure to:")
        print("1. Set CLEANED_DATA_PATH at the top of this file, OR")
        print("2. Provide the correct file path as a command line argument")
        return

    # Run analysis
    calculator = TenKGrowthRateCalculator(input_csv)
    growth_df = calculator.run_analysis()

    return growth_df


if __name__ == "__main__":
    main()
