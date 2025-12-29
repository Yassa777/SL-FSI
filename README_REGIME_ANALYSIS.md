# Sri Lanka FSI - Regime Analysis App

This Streamlit application provides comprehensive analysis of the Sri Lanka Financial Stress Index using Hidden Markov Models (HMM) and Bayesian Change Point Detection.

## Features

### 📊 Data Explorer
- Visualize all 18 core data streams
- Explore 12+ derived features (volatility, returns, spreads)
- Correlation matrix for all features
- Interactive time series charts with crisis markers
- Summary statistics for each indicator

### 🔄 HMM Regime Detection
- Detects hidden market regimes using Gaussian HMM
- Configurable number of regimes (2-5)
- Multi-feature analysis
- Regime transition matrix
- Visual regime identification with color-coding
- Regime statistics and characteristics

### 📍 Bayesian Change Point Detection
- Identifies structural breaks in time series
- Based on Adams & MacKay (2007) algorithm
- Detects changes in mean and variance
- Configurable detection threshold
- Before/after statistics for each change point
- Probability-based detection

### 📈 Combined View
- Overlay HMM regimes and change points
- Comprehensive regime visualization
- Cross-analysis of different methods
- Crisis event markers

## Installation

1. Install dependencies:
```bash
pip install -r requirements_regime.txt
```

2. Ensure your data files are in place:
```
data/merged/slfsi_daily_panel.csv
data/merged/slfsi_monthly_panel.csv
```

## Usage

Run the Streamlit app:
```bash
streamlit run app_regime_analysis.py
```

The app will open in your browser at `http://localhost:8501`

## Data Streams (18 Core + Derived)

### Core Data Streams:
1. **D1** - USD/LKR Exchange Rate
2. **D2** - AWCMR (Interbank Rate)
3. **D3** - ASPI (Equity Index)
4. **D4** - Equity Daily Turnover
5. **D5** - Market Capitalization
6. **D6** - S&P SL20 Index
7. **D7** - Local Gold Price
8. **D6 Global** - Gold Price USD
9. **D8** - T-Bill Yields
10. **D9** - T-Bond Yields
11. **D10** - Policy Rate (SDFR)
12. **D12** - FX Reserves
13. **D13** - NCPI Inflation
14. **D14** - REER Index
15. **D15** - ISB Yields
16. **D17** - Tourism Earnings
17. **D18** - Worker Remittances
18. **Helper** - US 10Y Yield

### Derived Features:
- FX Return & Volatility (20d)
- Equity Return & Volatility (20d)
- Real Equity Return
- Gold Premium %
- Interbank Spread
- Real Policy Rate
- Import Cover (months)
- Reserve Slope (3m)
- Turnover Ratio
- EMBI Spread (approx)

## How to Use

### Step 1: Explore Data
- Select "📊 Data Explorer" from sidebar
- Choose between Daily or Monthly frequency
- Browse through all data streams and derived features
- View correlation matrix

### Step 2: Run HMM Analysis
- Select "🔄 HMM Regime Detection"
- Configure number of regimes (recommended: 3)
- Select features for analysis (e.g., r_fx, vol_fx_20d, awcmr)
- Click "Run HMM"
- Examine regime assignments and transition probabilities

### Step 3: Detect Change Points
- Select "📍 Bayesian Change Points"
- Choose a feature to analyze
- Adjust prior probability and threshold
- Click "Detect Change Points"
- Review detected structural breaks

### Step 4: Combined Analysis
- Select "📈 Combined View"
- See HMM regimes and change points overlaid
- Compare different detection methods
- Validate against known crisis events

## Crisis Markers

The app automatically marks key crisis events:
- **2022-03-07**: FX Float / De facto depegging
- **2022-04-12**: Sovereign Default
- **2022-09-15**: Peak Inflation (69.8% YoY)
- **2023-03-20**: IMF EFF Approval

## Technical Details

### HMM Implementation
- Uses `hmmlearn` library
- Gaussian HMM with full covariance
- Features are standardized before fitting
- Supports 2-5 hidden states
- Viterbi algorithm for state inference

### Bayesian Change Point Detection
- Online algorithm (Adams & MacKay 2007)
- Detects changes in mean and variance
- Hazard rate controls sensitivity
- Returns probability distribution over change points

## Tips

1. **Feature Selection for HMM**: Use features that capture different aspects of stress (FX, rates, volatility)
2. **Regime Interpretation**: Lower regime numbers don't imply severity - check statistics
3. **Change Point Threshold**: Higher threshold = fewer but more confident detections
4. **Frequency Choice**: Daily for market data, Monthly for macro indicators

## Files Created

- `app_regime_analysis.py` - Main Streamlit application
- `requirements_regime.txt` - Python dependencies
- `README_REGIME_ANALYSIS.md` - This file

## Next Steps

Potential enhancements:
- Export regime assignments to CSV
- Add regime prediction capabilities
- Include additional change point algorithms (PELT, CUSUM)
- Add financial stress index construction from regimes
- Implement regime-conditional correlations
- Add statistical tests for regime differences

## References

- Adams, R. P., & MacKay, D. J. (2007). Bayesian online changepoint detection. arXiv preprint arXiv:0710.3742.
- Rabiner, L. R. (1989). A tutorial on hidden Markov models and selected applications in speech recognition. Proceedings of the IEEE, 77(2), 257-286.
