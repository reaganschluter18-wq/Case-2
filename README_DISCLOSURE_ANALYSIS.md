# 10-K Corporate Disclosure Analysis

Comprehensive analysis of corporate disclosure practices in 10-K filings, examining document length trends, readability, complexity, and other key metrics.

## Overview

This analysis script provides insights into how corporate disclosures in 10-K filings have evolved over time, addressing critical questions about transparency and accessibility of financial information.

## Key Analyses

### 1. Document Length Trends
- **Are 10-Ks getting longer?** Tracks document length over time
- Calculates growth rates (total and annualized)
- Estimates word count and page increases
- Visualizes trends with charts

### 2. Readability Metrics
- **Flesch Reading Ease**: Measures how easy text is to read (0-100 scale)
- **Flesch-Kincaid Grade Level**: Education level required to understand
- **Gunning Fog Index**: Years of education needed
- **SMOG Index**: Simple Measure of Gobbledygook
- **Average Sentence Length**: Words per sentence
- Tracks readability trends over time

### 3. Text Complexity
- Average word length
- Average sentence length
- Percentage of long words (>6 characters)
- Total word and sentence counts
- Syllables per word

### 4. Technical Jargon Analysis
- Tracks usage of financial and legal terminology
- Measures jargon density (terms per 1,000 words)
- Identifies most frequently used complex terms
- Examples tracked: "amortization", "derivative", "pursuant", "notwithstanding"

### 5. Sentiment Analysis
- **Polarity**: Positive/negative tone (-1 to +1)
- **Subjectivity**: Objective vs subjective language (0 to 1)
- Trends in corporate messaging tone

### 6. Company-Level Analysis
- Individual company disclosure trends
- Companies with biggest increases/decreases
- Year-over-year changes

## Installation

### 1. Install Required Packages

```bash
pip install -r requirements.txt
```

### 2. Additional Setup (Optional)

For sentiment analysis, you may need to download TextBlob corpora:

```bash
python -m textblob.download_corpora
```

## Usage

### Basic Usage

```bash
python analyze_10k_disclosure.py <your_10k_data.csv>
```

### Example

```bash
# After scraping data with scrape_sp500_10k.py
python analyze_10k_disclosure.py sp500_10k_output/sp500_10k_filings.csv
```

### Input Data Format

The script expects a CSV file with the following columns:
- `ticker`: Company ticker symbol
- `company_name`: Company name
- `filing_date`: Date of filing
- `text_content`: Full text of the 10-K filing
- `text_length`: Character count (optional, will be calculated if missing)

## Output Files

The analysis creates a `disclosure_analysis/` directory with:

### CSV Files
- `readability_scores.csv`: Detailed readability metrics for each filing
- `complexity_metrics.csv`: Text complexity measures
- `jargon_analysis.csv`: Technical term usage statistics
- `sentiment_analysis.csv`: Sentiment scores
- `company_trends.csv`: Company-level changes over time

### Visualizations
- `length_trends.png`: Document length over time
- `readability_trends.png`: Readability scores over time

### Reports
- `DISCLOSURE_ANALYSIS_REPORT.txt`: Comprehensive summary of all findings

## Understanding the Results

### Readability Scores

**Flesch Reading Ease** (higher = easier to read):
- 90-100: Very Easy (5th grade)
- 60-70: Standard (8th-9th grade)
- 30-50: Difficult (College level)
- 0-30: Very Difficult (College graduate)

**Flesch-Kincaid Grade Level**:
- Indicates years of education required
- Example: Score of 18 = 18 years of education (graduate level)

### Typical 10-K Findings

Based on research, typical 10-K filings:
- **Reading Ease**: 20-40 (Very Difficult - College level)
- **Grade Level**: 15-20 (College to graduate school)
- **Length Growth**: +3-5% annually over past decades
- **Word Count**: 50,000-80,000 words (200-300 pages)

### Why This Matters

**For Investors:**
- Complex, lengthy disclosures may obscure important information
- Decreased readability can signal risk obfuscation
- Sudden length increases may indicate new risks or complexity

**For Regulators:**
- Tracks compliance with plain English requirements
- Identifies trends in disclosure quality
- Helps assess information accessibility

**For Researchers:**
- Documents evolution of corporate reporting
- Examines relationship between complexity and firm characteristics
- Studies impact of regulatory changes

## Performance Notes

### Large Datasets
- For datasets >500 filings, readability analysis samples 500 random filings
- Sentiment analysis samples 200 filings
- This balances accuracy with computational efficiency

### Processing Time
- Small dataset (50 filings): ~2-5 minutes
- Medium dataset (500 filings): ~15-30 minutes
- Large dataset (2000+ filings): ~1-2 hours

### Memory Usage
- Each 10-K filing is ~500KB-2MB of text
- Analysis loads data in chunks when possible
- Recommended: 8GB+ RAM for large datasets

## Workflow Example

### Complete Analysis Pipeline

```bash
# Step 1: Scrape 10-K filings
python scrape_sp500_10k.py

# Step 2: Clean the data (optional but recommended)
python clean_10k_data.py

# Step 3: Analyze disclosures
python analyze_10k_disclosure.py sp500_10k_output/sp500_10k_filings_CLEAN.csv

# Results will be in: disclosure_analysis/
```

## Research Applications

### Academic Research
- Corporate governance studies
- Financial reporting quality
- Regulatory compliance research
- Investor protection studies

### Investment Analysis
- Risk assessment through disclosure complexity
- Management quality indicators
- Red flags in sudden complexity changes

### Regulatory Analysis
- Effectiveness of plain English requirements
- Industry-wide disclosure trends
- Impact of new reporting standards

## Key Research Questions Answered

1. **Are 10-Ks getting longer?**
   - Measures exact growth in characters, words, and pages
   - Calculates annual growth rates
   - Compares companies and industries

2. **Are 10-Ks getting harder to read?**
   - Tracks multiple readability metrics over time
   - Compares to grade-level standards
   - Identifies complexity drivers

3. **What's driving the changes?**
   - Increased jargon usage
   - Longer sentences and words
   - More risk disclosures
   - Greater operational complexity

4. **Do some companies write clearer disclosures?**
   - Company-level comparisons
   - Best and worst performers
   - Changes within companies over time

## Limitations

- Readability metrics are heuristic-based approximations
- Sentiment analysis on financial text can be noisy
- Results sensitive to text preprocessing quality
- Does not analyze tables, exhibits, or financial statements
- Sampling used for large datasets may miss outliers

## References

### Academic Papers
- Li, F. (2008). "Annual report readability, current earnings, and earnings persistence"
- Loughran, T. & McDonald, B. (2014). "Measuring readability in financial disclosures"
- SEC (1998). "A Plain English Handbook"

### Regulatory Guidance
- SEC Plain English Rules (1998)
- SEC Fast Act Disclosure Simplification (2018)

## Troubleshooting

### Missing Dependencies
```bash
# Install specific package
pip install textstat
pip install textblob

# Or reinstall all
pip install -r requirements.txt
```

### Memory Errors
- Reduce sample size in the script
- Process data in smaller batches
- Use a machine with more RAM

### Slow Performance
- Analysis automatically samples large datasets
- Consider using cleaned data (clean_10k_data.py first)
- Run on subset of companies for testing

## Contributing

Suggestions for additional analyses:
- Industry-specific benchmarking
- Section-by-section analysis (MD&A, Risk Factors, etc.)
- Comparison with peer companies
- Time-series forecasting
- Machine learning for disclosure quality

## License

This analysis script is provided for research and educational purposes.

## Contact

For questions or issues, please open an issue in the repository.

---

**Last Updated**: November 21, 2025
**Version**: 1.0
