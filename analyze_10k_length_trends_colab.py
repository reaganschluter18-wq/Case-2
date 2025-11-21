#!/usr/bin/env python3
"""
10-K Length Trend Analysis for Google Colab
============================================

Analyzes how 10-K document lengths have changed over the last 5 years
for S&P 500 companies and creates visualizations.

Perfect for Google Colab - just run this script!

Author: Analysis script for Case-2
Date: 2025-11-21
"""

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from datetime import datetime
import warnings
warnings.filterwarnings('ignore')

# ============================================================================
# CONFIGURATION - Your Data Path
# ============================================================================
DATA_PATH = "/content/drive/MyDrive/ACC 380K Case 2/Clean/sp500_10k_filings_CLEAN.csv"

# Set plotting style
sns.set_style("whitegrid")
plt.rcParams['figure.figsize'] = (14, 8)
plt.rcParams['font.size'] = 11


class TenKLengthTrendAnalyzer:
    """Analyze 10-K document length trends over time"""

    def __init__(self, data_path: str):
        self.data_path = data_path
        self.df = None

    def load_and_prepare_data(self):
        """Load and prepare the 10-K data"""
        print("="*80)
        print("📂 LOADING DATA")
        print("="*80)

        # Load data
        self.df = pd.read_csv(self.data_path)
        print(f"✓ Loaded {len(self.df):,} filings")

        # Parse dates and extract year
        self.df['filing_date'] = pd.to_datetime(self.df['filing_date'])
        self.df['filing_year'] = self.df['filing_date'].dt.year

        # Calculate text length if not present
        if 'text_length' not in self.df.columns and 'text_content' in self.df.columns:
            print("  Calculating text lengths...")
            self.df['text_length'] = self.df['text_content'].str.len()

        # Convert to word count (approximate: 5 chars per word)
        self.df['word_count'] = self.df['text_length'] / 5

        # Convert to page count (approximate: 300 words per page)
        self.df['page_count'] = self.df['word_count'] / 300

        print(f"✓ Date range: {self.df['filing_date'].min().date()} to {self.df['filing_date'].max().date()}")
        print(f"✓ Companies: {self.df['ticker'].nunique():,}")
        print(f"✓ Years: {sorted(self.df['filing_year'].unique())}")
        print(f"✓ Average 10-K length: {self.df['text_length'].mean():,.0f} characters")
        print(f"✓ Average 10-K pages: {self.df['page_count'].mean():.0f} pages\n")

    def analyze_yearly_trends(self):
        """Analyze how average 10-K length has changed by year"""
        print("="*80)
        print("📊 ANALYZING YEARLY TRENDS")
        print("="*80)

        # Group by year and calculate statistics
        yearly_stats = self.df.groupby('filing_year').agg({
            'text_length': ['mean', 'median', 'std', 'count'],
            'word_count': ['mean', 'median'],
            'page_count': ['mean', 'median']
        }).round(0)

        # Flatten column names
        yearly_stats.columns = ['_'.join(col).strip() for col in yearly_stats.columns.values]
        yearly_stats = yearly_stats.reset_index()

        # Calculate year-over-year growth
        yearly_stats['yoy_growth_pct'] = yearly_stats['text_length_mean'].pct_change() * 100
        yearly_stats['yoy_growth_chars'] = yearly_stats['text_length_mean'].diff()

        print("\nYear-by-Year Statistics:")
        print("-" * 80)
        for _, row in yearly_stats.iterrows():
            year = int(row['filing_year'])
            avg_chars = int(row['text_length_mean'])
            avg_pages = int(row['page_count_mean'])
            count = int(row['text_length_count'])

            print(f"\n{year}:")
            print(f"  • Filings: {count:,}")
            print(f"  • Avg length: {avg_chars:,} characters ({avg_pages:,} pages)")

            if not pd.isna(row['yoy_growth_pct']):
                growth_pct = row['yoy_growth_pct']
                growth_chars = int(row['yoy_growth_chars'])
                direction = "📈" if growth_pct > 0 else "📉" if growth_pct < 0 else "➡️"
                print(f"  • YoY change: {direction} {growth_pct:+.1f}% ({growth_chars:+,} chars)")

        # Overall trend
        first_year_avg = yearly_stats.iloc[0]['text_length_mean']
        last_year_avg = yearly_stats.iloc[-1]['text_length_mean']
        total_change_pct = ((last_year_avg - first_year_avg) / first_year_avg) * 100
        total_change_chars = last_year_avg - first_year_avg

        num_years = yearly_stats.iloc[-1]['filing_year'] - yearly_stats.iloc[0]['filing_year']

        print("\n" + "="*80)
        print("📈 OVERALL TREND SUMMARY")
        print("="*80)
        print(f"First year ({int(yearly_stats.iloc[0]['filing_year'])}): {first_year_avg:,.0f} characters")
        print(f"Last year ({int(yearly_stats.iloc[-1]['filing_year'])}): {last_year_avg:,.0f} characters")
        print(f"\nTotal change: {total_change_pct:+.1f}% ({total_change_chars:+,.0f} characters)")
        print(f"Average annual change: {total_change_pct/num_years:+.1f}% per year")

        if total_change_pct > 0:
            print(f"\n💡 10-K documents have GROWN by an average of {total_change_chars:,.0f} characters")
            print(f"   ({int(total_change_chars/5):,} words, or ~{int(total_change_chars/1500):.0f} pages)")
        else:
            print(f"\n💡 10-K documents have SHRUNK by an average of {abs(total_change_chars):,.0f} characters")

        return yearly_stats

    def create_visualizations(self, yearly_stats):
        """Create comprehensive visualizations"""
        print("\n" + "="*80)
        print("📊 CREATING VISUALIZATIONS")
        print("="*80)

        # Create figure with multiple subplots
        fig = plt.figure(figsize=(16, 12))
        gs = fig.add_gridspec(3, 2, hspace=0.3, wspace=0.3)

        # 1. Average Length Over Time (Line Plot)
        ax1 = fig.add_subplot(gs[0, :])
        years = yearly_stats['filing_year']
        avg_length = yearly_stats['text_length_mean']

        ax1.plot(years, avg_length, marker='o', linewidth=3,
                markersize=10, color='#2E86AB', label='Mean Length')
        ax1.fill_between(years, avg_length, alpha=0.3, color='#2E86AB')

        # Add trend line
        z = np.polyfit(years, avg_length, 1)
        p = np.poly1d(z)
        ax1.plot(years, p(years), "--", color='red', linewidth=2,
                label=f'Trend Line ({"+" if z[0] > 0 else ""}{z[0]:,.0f} chars/year)')

        ax1.set_xlabel('Year', fontsize=13, fontweight='bold')
        ax1.set_ylabel('Average 10-K Length (characters)', fontsize=13, fontweight='bold')
        ax1.set_title('📈 Average 10-K Document Length Over Time',
                     fontsize=15, fontweight='bold', pad=20)
        ax1.legend(fontsize=11)
        ax1.grid(True, alpha=0.4)
        ax1.ticklabel_format(style='plain', axis='y')

        # Format y-axis with commas
        ax1.yaxis.set_major_formatter(plt.FuncFormatter(lambda x, p: f'{int(x):,}'))

        # 2. Page Count Over Time
        ax2 = fig.add_subplot(gs[1, 0])
        avg_pages = yearly_stats['page_count_mean']

        bars = ax2.bar(years, avg_pages, color='#06AED5', edgecolor='black', linewidth=1.5)

        # Color bars by trend
        for i, bar in enumerate(bars):
            if i > 0:
                if avg_pages.iloc[i] > avg_pages.iloc[i-1]:
                    bar.set_color('#06D6A0')  # Green for increase
                elif avg_pages.iloc[i] < avg_pages.iloc[i-1]:
                    bar.set_color('#E63946')  # Red for decrease

        ax2.set_xlabel('Year', fontsize=12, fontweight='bold')
        ax2.set_ylabel('Average Pages', fontsize=12, fontweight='bold')
        ax2.set_title('📄 Average Page Count per Year', fontsize=13, fontweight='bold')
        ax2.grid(True, alpha=0.3, axis='y')

        # Add value labels on bars
        for i, (year, pages) in enumerate(zip(years, avg_pages)):
            ax2.text(year, pages + 5, f'{int(pages)}',
                    ha='center', va='bottom', fontweight='bold', fontsize=9)

        # 3. Year-over-Year Growth Rate
        ax3 = fig.add_subplot(gs[1, 1])
        yoy_growth = yearly_stats['yoy_growth_pct'].dropna()
        yoy_years = yearly_stats['filing_year'][1:]

        colors = ['#06D6A0' if x > 0 else '#E63946' for x in yoy_growth]
        bars = ax3.bar(yoy_years, yoy_growth, color=colors, edgecolor='black', linewidth=1.5)

        ax3.axhline(0, color='black', linewidth=2)
        ax3.set_xlabel('Year', fontsize=12, fontweight='bold')
        ax3.set_ylabel('Growth Rate (%)', fontsize=12, fontweight='bold')
        ax3.set_title('📊 Year-over-Year Growth Rate', fontsize=13, fontweight='bold')
        ax3.grid(True, alpha=0.3, axis='y')

        # Add value labels
        for year, growth in zip(yoy_years, yoy_growth):
            va = 'bottom' if growth > 0 else 'top'
            offset = 0.2 if growth > 0 else -0.2
            ax3.text(year, growth + offset, f'{growth:+.1f}%',
                    ha='center', va=va, fontweight='bold', fontsize=9)

        # 4. Distribution of Lengths by Year (Violin Plot)
        ax4 = fig.add_subplot(gs[2, 0])

        # Prepare data for violin plot
        violin_data = []
        violin_labels = []
        for year in sorted(self.df['filing_year'].unique()):
            year_data = self.df[self.df['filing_year'] == year]['text_length']
            violin_data.append(year_data)
            violin_labels.append(str(int(year)))

        parts = ax4.violinplot(violin_data, positions=range(len(violin_data)),
                              showmeans=True, showmedians=True)

        # Color the violins
        for pc in parts['bodies']:
            pc.set_facecolor('#2E86AB')
            pc.set_alpha(0.7)

        ax4.set_xticks(range(len(violin_labels)))
        ax4.set_xticklabels(violin_labels)
        ax4.set_xlabel('Year', fontsize=12, fontweight='bold')
        ax4.set_ylabel('10-K Length (characters)', fontsize=12, fontweight='bold')
        ax4.set_title('📊 Length Distribution by Year', fontsize=13, fontweight='bold')
        ax4.grid(True, alpha=0.3, axis='y')
        ax4.ticklabel_format(style='plain', axis='y')
        ax4.yaxis.set_major_formatter(plt.FuncFormatter(lambda x, p: f'{int(x):,}'))

        # 5. Number of Filings per Year
        ax5 = fig.add_subplot(gs[2, 1])
        filing_counts = yearly_stats['text_length_count']

        bars = ax5.bar(years, filing_counts, color='#F77F00', edgecolor='black', linewidth=1.5)

        ax5.set_xlabel('Year', fontsize=12, fontweight='bold')
        ax5.set_ylabel('Number of Filings', fontsize=12, fontweight='bold')
        ax5.set_title('📋 Number of 10-K Filings per Year', fontsize=13, fontweight='bold')
        ax5.grid(True, alpha=0.3, axis='y')

        # Add value labels
        for year, count in zip(years, filing_counts):
            ax5.text(year, count + 2, f'{int(count)}',
                    ha='center', va='bottom', fontweight='bold', fontsize=9)

        # Overall title
        fig.suptitle('S&P 500 10-K Document Length Analysis: 5-Year Trends',
                    fontsize=18, fontweight='bold', y=0.995)

        print("\n✓ Visualization created successfully!")
        plt.tight_layout()
        plt.show()

        print("\n💡 TIP: In Google Colab, the graph will appear above.")
        print("   Right-click on it to save or download.\n")

    def analyze_company_level_trends(self):
        """Analyze individual company trends"""
        print("="*80)
        print("🏢 COMPANY-LEVEL ANALYSIS")
        print("="*80)

        # Find companies with data across multiple years
        company_year_counts = self.df.groupby('ticker')['filing_year'].nunique()
        multi_year_companies = company_year_counts[company_year_counts >= 3]

        print(f"\nCompanies with 3+ years of data: {len(multi_year_companies)}")

        # Calculate growth for companies with multiple years
        growth_data = []

        for ticker in multi_year_companies.index:
            company_data = self.df[self.df['ticker'] == ticker].sort_values('filing_year')

            if len(company_data) < 2:
                continue

            first_length = company_data.iloc[0]['text_length']
            last_length = company_data.iloc[-1]['text_length']
            first_year = company_data.iloc[0]['filing_year']
            last_year = company_data.iloc[-1]['filing_year']

            total_change = last_length - first_length
            pct_change = (total_change / first_length) * 100 if first_length > 0 else 0

            growth_data.append({
                'ticker': ticker,
                'first_year': first_year,
                'last_year': last_year,
                'first_length': first_length,
                'last_length': last_length,
                'change_chars': total_change,
                'change_pct': pct_change
            })

        growth_df = pd.DataFrame(growth_data).sort_values('change_pct', ascending=False)

        # Show top growers and shrinkers
        print("\n🚀 TOP 10 COMPANIES WITH BIGGEST GROWTH:")
        print("-" * 80)
        for i, row in growth_df.head(10).iterrows():
            print(f"{row['ticker']:6s}: {row['change_pct']:+6.1f}% "
                  f"({int(row['first_length']):,} → {int(row['last_length']):,} chars)")

        print("\n📉 TOP 10 COMPANIES WITH BIGGEST DECREASE:")
        print("-" * 80)
        for i, row in growth_df.tail(10).iterrows():
            print(f"{row['ticker']:6s}: {row['change_pct']:+6.1f}% "
                  f"({int(row['first_length']):,} → {int(row['last_length']):,} chars)")

        # Summary stats
        growing = len(growth_df[growth_df['change_pct'] > 0])
        shrinking = len(growth_df[growth_df['change_pct'] < 0])

        print(f"\n📊 SUMMARY:")
        print(f"  • Companies with growing 10-Ks: {growing} ({growing/len(growth_df)*100:.1f}%)")
        print(f"  • Companies with shrinking 10-Ks: {shrinking} ({shrinking/len(growth_df)*100:.1f}%)")
        print(f"  • Average change: {growth_df['change_pct'].mean():+.1f}%")
        print(f"  • Median change: {growth_df['change_pct'].median():+.1f}%\n")

        return growth_df

    def run_full_analysis(self):
        """Run complete analysis pipeline"""
        print("\n" + "="*80)
        print("🚀 STARTING 10-K LENGTH TREND ANALYSIS")
        print("="*80)
        print(f"Data source: {self.data_path}")
        print(f"Started: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")

        # Load data
        self.load_and_prepare_data()

        # Analyze yearly trends
        yearly_stats = self.analyze_yearly_trends()

        # Analyze company-level trends
        growth_df = self.analyze_company_level_trends()

        # Create visualizations
        self.create_visualizations(yearly_stats)

        print("="*80)
        print("✅ ANALYSIS COMPLETE!")
        print("="*80)

        return yearly_stats, growth_df


# ============================================================================
# MAIN EXECUTION
# ============================================================================

def main():
    """Main function to run the analysis"""

    # Create analyzer
    analyzer = TenKLengthTrendAnalyzer(DATA_PATH)

    # Run analysis
    yearly_stats, company_growth = analyzer.run_full_analysis()

    return analyzer, yearly_stats, company_growth


# Run the analysis
if __name__ == "__main__":
    analyzer, yearly_stats, company_growth = main()

    # Display instructions for Google Colab
    print("\n" + "="*80)
    print("📝 GOOGLE COLAB INSTRUCTIONS")
    print("="*80)
    print("\nTo use this script in Google Colab:")
    print("\n1. Mount your Google Drive:")
    print("   from google.colab import drive")
    print("   drive.mount('/content/drive')")
    print("\n2. Run this script:")
    print("   !python analyze_10k_length_trends_colab.py")
    print("\n   OR run it directly in a cell:")
    print("   exec(open('analyze_10k_length_trends_colab.py').read())")
    print("\n3. The graphs will appear above in the output!")
    print("\n4. To save the graph as an image, right-click and select 'Save image as...'")
    print("\nThe data will be automatically loaded from:")
    print(f"  {DATA_PATH}")
    print("\n" + "="*80 + "\n")
