#!/usr/bin/env python3
"""
10-K Corporate Disclosure Analysis
===================================

Comprehensive analysis of corporate disclosure practices in 10-K filings:
1. Document length trends over time
2. Readability metrics (Flesch Reading Ease, Flesch-Kincaid Grade Level, etc.)
3. Complexity metrics (sentence length, word length, syllables per word)
4. Technical jargon and financial terminology usage
5. Section-specific analysis
6. Sentiment analysis
7. Industry comparisons
8. Year-over-year changes

Author: Analysis script for Case-2
Date: 2025-11-21
"""

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Tuple
import re
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

# Try to import optional libraries
try:
    import textstat
    TEXTSTAT_AVAILABLE = True
except ImportError:
    TEXTSTAT_AVAILABLE = False
    print("⚠️  Warning: textstat not installed. Install with: pip install textstat")

try:
    from textblob import TextBlob
    TEXTBLOB_AVAILABLE = True
except ImportError:
    TEXTBLOB_AVAILABLE = False
    print("⚠️  Warning: textblob not installed. Install with: pip install textblob")


class TenKDisclosureAnalyzer:
    """Comprehensive analyzer for 10-K disclosure practices"""

    def __init__(self, input_csv: str, output_dir: str = None):
        self.input_csv = Path(input_csv)

        if output_dir:
            self.output_dir = Path(output_dir)
        else:
            self.output_dir = self.input_csv.parent / "disclosure_analysis"

        self.output_dir.mkdir(parents=True, exist_ok=True)

        self.df = None
        self.results = {}

        # Financial/technical terms to track
        self.financial_terms = [
            'amortization', 'depreciation', 'ebitda', 'derivative', 'hedging',
            'liquidity', 'covenant', 'impairment', 'goodwill', 'contingent',
            'material', 'significant', 'substantial', 'approximately',
            'pursuant', 'thereof', 'herein', 'aforementioned', 'notwithstanding'
        ]

        print(f"📁 Output directory: {self.output_dir}")
        print(f"📊 Analysis results will be saved here\n")

    def load_data(self) -> pd.DataFrame:
        """Load and prepare 10-K data"""
        print("="*80)
        print("LOADING DATA")
        print("="*80)

        if not self.input_csv.exists():
            raise FileNotFoundError(f"Input file not found: {self.input_csv}")

        df = pd.read_csv(self.input_csv)
        print(f"✓ Loaded {len(df):,} filings from {self.input_csv}")

        # Parse dates
        df['filing_date'] = pd.to_datetime(df['filing_date'])
        df['filing_year'] = df['filing_date'].dt.year

        # Ensure text_length is present
        if 'text_length' not in df.columns and 'text_content' in df.columns:
            print("  Calculating text lengths...")
            df['text_length'] = df['text_content'].str.len()

        # Basic info
        print(f"✓ Date range: {df['filing_date'].min().date()} to {df['filing_date'].max().date()}")
        print(f"✓ Companies: {df['ticker'].nunique():,}")
        print(f"✓ Years covered: {df['filing_year'].nunique()}")
        print()

        self.df = df
        return df

    def analyze_length_trends(self):
        """Analyze document length trends over time"""
        print("="*80)
        print("ANALYSIS 1: DOCUMENT LENGTH TRENDS")
        print("="*80)

        # Group by year
        yearly_stats = self.df.groupby('filing_year').agg({
            'text_length': ['mean', 'median', 'std', 'count']
        }).round(0)

        yearly_stats.columns = ['Mean Length', 'Median Length', 'Std Dev', 'Count']

        print("\n📈 Document Length by Year:")
        print(yearly_stats.to_string())

        # Calculate growth rates
        first_year = yearly_stats.index.min()
        last_year = yearly_stats.index.max()
        first_mean = yearly_stats.loc[first_year, 'Mean Length']
        last_mean = yearly_stats.loc[last_year, 'Mean Length']

        total_growth = ((last_mean - first_mean) / first_mean) * 100
        years_span = last_year - first_year
        annual_growth = (((last_mean / first_mean) ** (1/years_span)) - 1) * 100 if years_span > 0 else 0

        print(f"\n📊 Growth Analysis:")
        print(f"  - Total growth ({first_year} to {last_year}): {total_growth:+.1f}%")
        print(f"  - Annual growth rate: {annual_growth:+.1f}% per year")
        print(f"  - Absolute increase: {last_mean - first_mean:,.0f} characters")

        # Convert to word count estimate (avg 5 chars per word)
        words_increase = (last_mean - first_mean) / 5
        print(f"  - Approximate word increase: {words_increase:,.0f} words")

        # Convert to page estimate (250 words per page)
        pages_increase = words_increase / 250
        print(f"  - Approximate page increase: {pages_increase:.1f} pages")

        # Save results
        self.results['length_trends'] = {
            'yearly_stats': yearly_stats,
            'total_growth_pct': total_growth,
            'annual_growth_pct': annual_growth,
            'char_increase': last_mean - first_mean,
            'word_increase': words_increase,
            'page_increase': pages_increase
        }

        # Plot
        self._plot_length_trends(yearly_stats)
        print()

    def _plot_length_trends(self, yearly_stats):
        """Create visualization of length trends"""
        fig, axes = plt.subplots(2, 1, figsize=(12, 8))

        # Plot 1: Mean and Median
        ax1 = axes[0]
        ax1.plot(yearly_stats.index, yearly_stats['Mean Length'],
                marker='o', linewidth=2, label='Mean', color='#2E86AB')
        ax1.plot(yearly_stats.index, yearly_stats['Median Length'],
                marker='s', linewidth=2, label='Median', color='#A23B72')
        ax1.set_xlabel('Filing Year', fontsize=11)
        ax1.set_ylabel('Document Length (characters)', fontsize=11)
        ax1.set_title('10-K Document Length Over Time', fontsize=13, fontweight='bold')
        ax1.legend()
        ax1.grid(True, alpha=0.3)
        ax1.ticklabel_format(style='plain', axis='y')

        # Plot 2: Sample size
        ax2 = axes[1]
        ax2.bar(yearly_stats.index, yearly_stats['Count'], color='#F18F01', alpha=0.7)
        ax2.set_xlabel('Filing Year', fontsize=11)
        ax2.set_ylabel('Number of Filings', fontsize=11)
        ax2.set_title('Sample Size by Year', fontsize=13, fontweight='bold')
        ax2.grid(True, alpha=0.3, axis='y')

        plt.tight_layout()
        plt.savefig(self.output_dir / 'length_trends.png', dpi=300, bbox_inches='tight')
        print(f"  ✓ Saved plot: {self.output_dir / 'length_trends.png'}")

    def analyze_readability(self):
        """Calculate readability scores for 10-K filings"""
        print("="*80)
        print("ANALYSIS 2: READABILITY METRICS")
        print("="*80)

        if not TEXTSTAT_AVAILABLE:
            print("⚠️  Skipping readability analysis (textstat not installed)")
            print("   Install with: pip install textstat\n")
            return

        print("Calculating readability scores (this may take a while)...\n")

        # Sample for speed (or use all if dataset is small)
        if len(self.df) > 500:
            print(f"⚠️  Large dataset detected. Sampling 500 random filings for readability analysis.")
            sample_df = self.df.sample(n=500, random_state=42)
        else:
            sample_df = self.df

        readability_scores = []

        for idx, row in sample_df.iterrows():
            if idx % 50 == 0:
                print(f"  Progress: {idx}/{len(sample_df)}", end='\r')

            text = row.get('text_content', '')
            if not text or len(text) < 100:
                continue

            # Limit text length to avoid memory issues
            text_sample = text[:100000]  # First 100k characters

            try:
                scores = {
                    'ticker': row['ticker'],
                    'filing_year': row['filing_year'],
                    'text_length': row['text_length'],
                    'flesch_reading_ease': textstat.flesch_reading_ease(text_sample),
                    'flesch_kincaid_grade': textstat.flesch_kincaid_grade(text_sample),
                    'gunning_fog': textstat.gunning_fog(text_sample),
                    'smog_index': textstat.smog_index(text_sample),
                    'coleman_liau_index': textstat.coleman_liau_index(text_sample),
                    'automated_readability_index': textstat.automated_readability_index(text_sample),
                    'avg_sentence_length': textstat.avg_sentence_length(text_sample),
                    'avg_syllables_per_word': textstat.avg_syllables_per_word(text_sample),
                    'difficult_words': textstat.difficult_words(text_sample),
                }
                readability_scores.append(scores)
            except Exception as e:
                continue

        print()  # New line after progress

        if not readability_scores:
            print("⚠️  No readability scores calculated\n")
            return

        readability_df = pd.DataFrame(readability_scores)

        # Overall statistics
        print("\n📊 Overall Readability Statistics:")
        stats = readability_df[['flesch_reading_ease', 'flesch_kincaid_grade',
                                'gunning_fog', 'avg_sentence_length']].describe()
        print(stats.round(2).to_string())

        # Interpretation of scores
        print("\n📖 Readability Score Interpretation:")
        avg_flesch = readability_df['flesch_reading_ease'].mean()
        avg_fk_grade = readability_df['flesch_kincaid_grade'].mean()

        print(f"  Flesch Reading Ease: {avg_flesch:.1f}")
        if avg_flesch < 30:
            print("    → Very Difficult (College graduate level)")
        elif avg_flesch < 50:
            print("    → Difficult (College level)")
        elif avg_flesch < 60:
            print("    → Fairly Difficult (High school senior level)")
        else:
            print("    → Standard (High school junior level or easier)")

        print(f"\n  Flesch-Kincaid Grade: {avg_fk_grade:.1f}")
        print(f"    → Requires {avg_fk_grade:.0f} years of education to understand")

        print(f"\n  Average Sentence Length: {readability_df['avg_sentence_length'].mean():.1f} words")
        print(f"  Average Syllables per Word: {readability_df['avg_syllables_per_word'].mean():.2f}")

        # Trends over time
        if readability_df['filing_year'].nunique() > 1:
            print("\n📈 Readability Trends Over Time:")
            yearly_readability = readability_df.groupby('filing_year')[
                ['flesch_reading_ease', 'flesch_kincaid_grade', 'avg_sentence_length']
            ].mean()
            print(yearly_readability.round(2).to_string())

            # Plot readability trends
            self._plot_readability_trends(yearly_readability)

        # Save results
        self.results['readability'] = readability_df
        readability_df.to_csv(self.output_dir / 'readability_scores.csv', index=False)
        print(f"\n  ✓ Saved: {self.output_dir / 'readability_scores.csv'}")
        print()

    def _plot_readability_trends(self, yearly_readability):
        """Create visualization of readability trends"""
        fig, axes = plt.subplots(2, 1, figsize=(12, 8))

        # Plot 1: Flesch Reading Ease (higher = easier)
        ax1 = axes[0]
        ax1.plot(yearly_readability.index, yearly_readability['flesch_reading_ease'],
                marker='o', linewidth=2, color='#2E86AB')
        ax1.set_xlabel('Filing Year', fontsize=11)
        ax1.set_ylabel('Flesch Reading Ease', fontsize=11)
        ax1.set_title('10-K Readability Over Time (Higher = Easier)', fontsize=13, fontweight='bold')
        ax1.grid(True, alpha=0.3)
        ax1.axhline(y=30, color='red', linestyle='--', alpha=0.5, label='Very Difficult threshold')
        ax1.legend()

        # Plot 2: Grade Level (lower = easier)
        ax2 = axes[1]
        ax2.plot(yearly_readability.index, yearly_readability['flesch_kincaid_grade'],
                marker='s', linewidth=2, color='#A23B72')
        ax2.set_xlabel('Filing Year', fontsize=11)
        ax2.set_ylabel('Grade Level', fontsize=11)
        ax2.set_title('10-K Required Education Level (Lower = Easier)', fontsize=13, fontweight='bold')
        ax2.grid(True, alpha=0.3)

        plt.tight_layout()
        plt.savefig(self.output_dir / 'readability_trends.png', dpi=300, bbox_inches='tight')
        print(f"  ✓ Saved plot: {self.output_dir / 'readability_trends.png'}")

    def analyze_complexity(self):
        """Analyze text complexity metrics"""
        print("="*80)
        print("ANALYSIS 3: TEXT COMPLEXITY METRICS")
        print("="*80)

        print("Calculating complexity metrics...\n")

        # Use sample for large datasets
        if len(self.df) > 500:
            print(f"⚠️  Sampling 500 random filings for complexity analysis.")
            sample_df = self.df.sample(n=500, random_state=42)
        else:
            sample_df = self.df

        complexity_metrics = []

        for idx, row in sample_df.iterrows():
            if idx % 50 == 0:
                print(f"  Progress: {idx}/{len(sample_df)}", end='\r')

            text = row.get('text_content', '')
            if not text or len(text) < 100:
                continue

            # Sample text for analysis
            text_sample = text[:100000]

            # Calculate metrics
            sentences = re.split(r'[.!?]+', text_sample)
            sentences = [s.strip() for s in sentences if len(s.strip()) > 10]

            words = re.findall(r'\b\w+\b', text_sample.lower())

            metrics = {
                'ticker': row['ticker'],
                'filing_year': row['filing_year'],
                'total_characters': len(text),
                'total_words': len(words),
                'total_sentences': len(sentences),
                'avg_word_length': np.mean([len(w) for w in words]) if words else 0,
                'avg_sentence_length_words': len(words) / len(sentences) if sentences else 0,
                'long_words_pct': sum(1 for w in words if len(w) > 6) / len(words) * 100 if words else 0,
            }

            complexity_metrics.append(metrics)

        print()  # New line after progress

        complexity_df = pd.DataFrame(complexity_metrics)

        # Overall statistics
        print("\n📊 Complexity Statistics:")
        print(f"  Average words per document: {complexity_df['total_words'].mean():,.0f}")
        print(f"  Average sentences per document: {complexity_df['total_sentences'].mean():,.0f}")
        print(f"  Average word length: {complexity_df['avg_word_length'].mean():.2f} characters")
        print(f"  Average sentence length: {complexity_df['avg_sentence_length_words'].mean():.1f} words")
        print(f"  Long words (>6 chars): {complexity_df['long_words_pct'].mean():.1f}%")

        # Trends over time
        if complexity_df['filing_year'].nunique() > 1:
            print("\n📈 Complexity Trends Over Time:")
            yearly_complexity = complexity_df.groupby('filing_year')[
                ['avg_word_length', 'avg_sentence_length_words', 'long_words_pct']
            ].mean()
            print(yearly_complexity.round(2).to_string())

        # Save results
        self.results['complexity'] = complexity_df
        complexity_df.to_csv(self.output_dir / 'complexity_metrics.csv', index=False)
        print(f"\n  ✓ Saved: {self.output_dir / 'complexity_metrics.csv'}")
        print()

    def analyze_jargon(self):
        """Analyze usage of technical and financial jargon"""
        print("="*80)
        print("ANALYSIS 4: TECHNICAL JARGON USAGE")
        print("="*80)

        print("Analyzing financial terminology usage...\n")

        # Use sample for large datasets
        if len(self.df) > 500:
            print(f"⚠️  Sampling 500 random filings for jargon analysis.")
            sample_df = self.df.sample(n=500, random_state=42)
        else:
            sample_df = self.df

        jargon_results = []

        for idx, row in sample_df.iterrows():
            if idx % 50 == 0:
                print(f"  Progress: {idx}/{len(sample_df)}", end='\r')

            text = row.get('text_content', '')
            if not text:
                continue

            text_lower = text.lower()
            text_words = len(re.findall(r'\b\w+\b', text_lower))

            # Count occurrences of each term
            term_counts = {}
            for term in self.financial_terms:
                count = len(re.findall(r'\b' + term + r'\b', text_lower))
                term_counts[f'term_{term}'] = count

            # Total jargon count
            total_jargon = sum(term_counts.values())
            jargon_density = (total_jargon / text_words * 1000) if text_words > 0 else 0

            result = {
                'ticker': row['ticker'],
                'filing_year': row['filing_year'],
                'total_words': text_words,
                'total_jargon_count': total_jargon,
                'jargon_per_1000_words': jargon_density,
            }
            result.update(term_counts)
            jargon_results.append(result)

        print()  # New line after progress

        jargon_df = pd.DataFrame(jargon_results)

        # Overall statistics
        print("\n📊 Jargon Usage Statistics:")
        print(f"  Average jargon terms per document: {jargon_df['total_jargon_count'].mean():.0f}")
        print(f"  Jargon density: {jargon_df['jargon_per_1000_words'].mean():.2f} terms per 1,000 words")

        # Most common terms
        print("\n  Most Frequently Used Terms:")
        term_cols = [col for col in jargon_df.columns if col.startswith('term_')]
        term_totals = jargon_df[term_cols].sum().sort_values(ascending=False)

        for i, (term_col, count) in enumerate(term_totals.head(10).items(), 1):
            term = term_col.replace('term_', '')
            avg_per_doc = count / len(jargon_df)
            print(f"    {i:2d}. '{term}': {count:,} total ({avg_per_doc:.1f} per document)")

        # Trends over time
        if jargon_df['filing_year'].nunique() > 1:
            print("\n📈 Jargon Usage Trends Over Time:")
            yearly_jargon = jargon_df.groupby('filing_year')['jargon_per_1000_words'].mean()
            for year, density in yearly_jargon.items():
                print(f"    {year}: {density:.2f} terms per 1,000 words")

        # Save results
        self.results['jargon'] = jargon_df
        jargon_df.to_csv(self.output_dir / 'jargon_analysis.csv', index=False)
        print(f"\n  ✓ Saved: {self.output_dir / 'jargon_analysis.csv'}")
        print()

    def analyze_sentiment(self):
        """Analyze sentiment and tone of 10-K filings"""
        print("="*80)
        print("ANALYSIS 5: SENTIMENT ANALYSIS")
        print("="*80)

        if not TEXTBLOB_AVAILABLE:
            print("⚠️  Skipping sentiment analysis (textblob not installed)")
            print("   Install with: pip install textblob\n")
            return

        print("Analyzing sentiment (this may take a while)...\n")

        # Use sample for large datasets
        if len(self.df) > 200:
            print(f"⚠️  Sampling 200 random filings for sentiment analysis.")
            sample_df = self.df.sample(n=200, random_state=42)
        else:
            sample_df = self.df

        sentiment_results = []

        for idx, row in sample_df.iterrows():
            if idx % 25 == 0:
                print(f"  Progress: {idx}/{len(sample_df)}", end='\r')

            text = row.get('text_content', '')
            if not text or len(text) < 100:
                continue

            # Sample text for analysis (sentiment on first 50k chars)
            text_sample = text[:50000]

            try:
                blob = TextBlob(text_sample)

                result = {
                    'ticker': row['ticker'],
                    'filing_year': row['filing_year'],
                    'polarity': blob.sentiment.polarity,  # -1 to 1 (negative to positive)
                    'subjectivity': blob.sentiment.subjectivity,  # 0 to 1 (objective to subjective)
                }
                sentiment_results.append(result)
            except Exception as e:
                continue

        print()  # New line after progress

        if not sentiment_results:
            print("⚠️  No sentiment scores calculated\n")
            return

        sentiment_df = pd.DataFrame(sentiment_results)

        # Overall statistics
        print("\n📊 Sentiment Statistics:")
        print(f"  Average polarity: {sentiment_df['polarity'].mean():.3f} (range: -1 to +1)")
        print(f"  Average subjectivity: {sentiment_df['subjectivity'].mean():.3f} (range: 0 to 1)")

        print("\n  Interpretation:")
        avg_polarity = sentiment_df['polarity'].mean()
        if avg_polarity > 0.1:
            print(f"    → Positive tone (polarity: {avg_polarity:.3f})")
        elif avg_polarity < -0.1:
            print(f"    → Negative tone (polarity: {avg_polarity:.3f})")
        else:
            print(f"    → Neutral tone (polarity: {avg_polarity:.3f})")

        avg_subj = sentiment_df['subjectivity'].mean()
        if avg_subj > 0.5:
            print(f"    → Subjective language (subjectivity: {avg_subj:.3f})")
        else:
            print(f"    → Objective language (subjectivity: {avg_subj:.3f})")

        # Trends over time
        if sentiment_df['filing_year'].nunique() > 1:
            print("\n📈 Sentiment Trends Over Time:")
            yearly_sentiment = sentiment_df.groupby('filing_year')[['polarity', 'subjectivity']].mean()
            print(yearly_sentiment.round(3).to_string())

        # Save results
        self.results['sentiment'] = sentiment_df
        sentiment_df.to_csv(self.output_dir / 'sentiment_analysis.csv', index=False)
        print(f"\n  ✓ Saved: {self.output_dir / 'sentiment_analysis.csv'}")
        print()

    def analyze_by_company(self):
        """Analyze disclosure trends by company"""
        print("="*80)
        print("ANALYSIS 6: COMPANY-LEVEL ANALYSIS")
        print("="*80)

        # Companies with multiple filings
        company_counts = self.df['ticker'].value_counts()
        multi_filing_companies = company_counts[company_counts >= 2]

        if len(multi_filing_companies) == 0:
            print("⚠️  Not enough companies with multiple filings for trend analysis\n")
            return

        print(f"\nAnalyzing {len(multi_filing_companies)} companies with 2+ filings...\n")

        company_trends = []

        for ticker in multi_filing_companies.index:
            company_df = self.df[self.df['ticker'] == ticker].sort_values('filing_date')

            if len(company_df) < 2:
                continue

            # Calculate trends
            first_filing = company_df.iloc[0]
            last_filing = company_df.iloc[-1]

            years_diff = (last_filing['filing_date'] - first_filing['filing_date']).days / 365.25
            length_change = last_filing['text_length'] - first_filing['text_length']
            length_change_pct = (length_change / first_filing['text_length']) * 100 if first_filing['text_length'] > 0 else 0

            trend = {
                'ticker': ticker,
                'company_name': first_filing.get('company_name', ''),
                'num_filings': len(company_df),
                'first_year': first_filing['filing_year'],
                'last_year': last_filing['filing_year'],
                'years_span': years_diff,
                'first_length': first_filing['text_length'],
                'last_length': last_filing['text_length'],
                'length_change': length_change,
                'length_change_pct': length_change_pct,
            }
            company_trends.append(trend)

        trends_df = pd.DataFrame(company_trends)

        # Statistics
        print("📊 Company-Level Disclosure Changes:")
        print(f"  Average length change: {trends_df['length_change'].mean():+,.0f} characters ({trends_df['length_change_pct'].mean():+.1f}%)")
        print(f"  Median length change: {trends_df['length_change'].median():+,.0f} characters ({trends_df['length_change_pct'].median():+.1f}%)")

        # Companies with biggest increases
        print("\n  Top 10 Companies by Length Increase:")
        top_increases = trends_df.nlargest(10, 'length_change_pct')
        for i, row in top_increases.iterrows():
            print(f"    {row['ticker']:6s}: {row['length_change_pct']:+6.1f}% ({row['first_year']}-{row['last_year']})")

        # Companies with biggest decreases
        decreases = trends_df[trends_df['length_change'] < 0]
        if len(decreases) > 0:
            print("\n  Top 10 Companies by Length Decrease:")
            top_decreases = trends_df.nsmallest(10, 'length_change_pct')
            for i, row in top_decreases.iterrows():
                print(f"    {row['ticker']:6s}: {row['length_change_pct']:+6.1f}% ({row['first_year']}-{row['last_year']})")

        # Save results
        trends_df.to_csv(self.output_dir / 'company_trends.csv', index=False)
        print(f"\n  ✓ Saved: {self.output_dir / 'company_trends.csv'}")
        print()

    def generate_summary_report(self):
        """Generate comprehensive summary report"""
        print("="*80)
        print("GENERATING SUMMARY REPORT")
        print("="*80)

        report_path = self.output_dir / 'DISCLOSURE_ANALYSIS_REPORT.txt'

        with open(report_path, 'w', encoding='utf-8') as f:
            f.write("="*80 + "\n")
            f.write("10-K CORPORATE DISCLOSURE ANALYSIS REPORT\n")
            f.write("="*80 + "\n")
            f.write(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
            f.write(f"Input file: {self.input_csv}\n")
            f.write(f"Total filings analyzed: {len(self.df):,}\n")
            f.write(f"Companies: {self.df['ticker'].nunique():,}\n")
            f.write(f"Date range: {self.df['filing_date'].min().date()} to {self.df['filing_date'].max().date()}\n")
            f.write("="*80 + "\n\n")

            # Key findings
            f.write("KEY FINDINGS\n")
            f.write("-"*80 + "\n\n")

            # 1. Length trends
            if 'length_trends' in self.results:
                lt = self.results['length_trends']
                f.write("1. DOCUMENT LENGTH TRENDS\n")
                f.write(f"   - Total growth: {lt['total_growth_pct']:+.1f}%\n")
                f.write(f"   - Annual growth rate: {lt['annual_growth_pct']:+.1f}% per year\n")
                f.write(f"   - Character increase: {lt['char_increase']:,.0f}\n")
                f.write(f"   - Estimated word increase: {lt['word_increase']:,.0f} words\n")
                f.write(f"   - Estimated page increase: {lt['page_increase']:.1f} pages\n\n")

            # 2. Readability
            if 'readability' in self.results:
                rd = self.results['readability']
                f.write("2. READABILITY\n")
                f.write(f"   - Flesch Reading Ease: {rd['flesch_reading_ease'].mean():.1f}\n")
                f.write(f"   - Flesch-Kincaid Grade: {rd['flesch_kincaid_grade'].mean():.1f}\n")
                f.write(f"   - Average sentence length: {rd['avg_sentence_length'].mean():.1f} words\n\n")

            # 3. Complexity
            if 'complexity' in self.results:
                cx = self.results['complexity']
                f.write("3. TEXT COMPLEXITY\n")
                f.write(f"   - Average words per document: {cx['total_words'].mean():,.0f}\n")
                f.write(f"   - Average word length: {cx['avg_word_length'].mean():.2f} characters\n")
                f.write(f"   - Long words (>6 chars): {cx['long_words_pct'].mean():.1f}%\n\n")

            # 4. Jargon
            if 'jargon' in self.results:
                jg = self.results['jargon']
                f.write("4. TECHNICAL JARGON\n")
                f.write(f"   - Jargon density: {jg['jargon_per_1000_words'].mean():.2f} terms per 1,000 words\n")
                f.write(f"   - Average jargon count: {jg['total_jargon_count'].mean():.0f} terms per document\n\n")

            # 5. Sentiment
            if 'sentiment' in self.results:
                st = self.results['sentiment']
                f.write("5. SENTIMENT\n")
                f.write(f"   - Average polarity: {st['polarity'].mean():.3f} (-1 to +1)\n")
                f.write(f"   - Average subjectivity: {st['subjectivity'].mean():.3f} (0 to 1)\n\n")

            f.write("="*80 + "\n")
            f.write("For detailed results, see individual CSV files in the output directory.\n")
            f.write("="*80 + "\n")

        print(f"✓ Summary report saved: {report_path}\n")

    def run_all_analyses(self):
        """Run complete analysis pipeline"""
        start_time = datetime.now()

        print("\n" + "="*80)
        print("10-K CORPORATE DISCLOSURE ANALYSIS")
        print("="*80)
        print(f"Started: {start_time.strftime('%Y-%m-%d %H:%M:%S')}\n")

        # Load data
        self.load_data()

        # Run analyses
        self.analyze_length_trends()
        self.analyze_readability()
        self.analyze_complexity()
        self.analyze_jargon()
        self.analyze_sentiment()
        self.analyze_by_company()

        # Generate summary
        self.generate_summary_report()

        end_time = datetime.now()
        duration = end_time - start_time

        print("="*80)
        print("✅ ANALYSIS COMPLETE!")
        print("="*80)
        print(f"Duration: {duration}")
        print(f"Output directory: {self.output_dir}")
        print(f"\nGenerated files:")
        for file in sorted(self.output_dir.glob('*')):
            print(f"  - {file.name}")
        print("="*80 + "\n")


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
            print(f"Found CSV file: {input_csv}")
        else:
            print("Usage: python analyze_10k_disclosure.py <input_csv>")
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
    analyzer = TenKDisclosureAnalyzer(input_csv)
    analyzer.run_all_analyses()


if __name__ == "__main__":
    main()
