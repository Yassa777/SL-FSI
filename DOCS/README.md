# SL-FSI Regime Analysis

A Streamlit application for exploring the Sri Lanka Financial Stress Index (SL-FSI) data and detecting regimes using Hidden Markov Models (HMM) and Bayesian change point detection.

## Project Overview

This repo provides:
- An interactive Streamlit dashboard (`app_regime_analysis.py`) to explore 18 core data streams plus derived features.
- HMM-based regime detection for configurable feature sets.
- Bayesian online change point detection to identify structural breaks.
- Data preparation scripts for downloading external series and merging datasets.

If you are looking for a feature-by-feature walkthrough of the app, see `README_REGIME_ANALYSIS.md`.

## Quick Start

### 1) Create a virtual environment (optional but recommended)
```bash
python -m venv .venv
source .venv/bin/activate
```

### 2) Install dependencies
```bash
pip install -r requirements_regime.txt
```

### 3) Ensure data is available
The app expects merged datasets at:
```
data/merged/slfsi_daily_panel.csv
data/merged/slfsi_monthly_panel.csv
```

If those are not present, use the data pipeline described below.

### 4) Run the app
```bash
streamlit run app_regime_analysis.py
```

The app will open at: `http://localhost:8501`.

## Application Features

### 📊 Data Explorer
- Interactive charts for 18 core series and derived features.
- Crisis/event markers for key SL macro events.
- Summary statistics and optional raw table view.
- Correlation matrix across features.

### 🔄 HMM Regime Detection
- Gaussian HMM with configurable 2–5 regimes.
- Multi-feature selection with standardization.
- Regime transition matrix and regime statistics.

### 📍 Bayesian Change Point Detection
- Bayesian online change point detection (Adams & MacKay, 2007).
- Detects changes in mean/variance with configurable thresholds.
- Before/after statistics for each detected change.

### 📈 Combined View
- HMM regime overlay plus change points.
- Crisis event markers for cross-referencing.

## Data Pipeline

### Data layout
```
data/
  external/   # downloaded/templated source data
  merged/     # merged panels consumed by the app
  processed/  # intermediate data (if produced by scripts)
```

### External data downloads
The script below uses `yfinance` to download global gold prices and US 10Y yields, and generates templates for manual data entry.
```bash
python scripts/download_external_data.py
```

This creates:
- `data/external/D6_gold_usd.csv`
- `data/external/us_treasury_10y.csv`
- `data/external/D10_policy_rates_daily.csv`
- `data/external/D10_policy_rates_changes.csv`
- Manual entry templates (e.g., `D12_reserves_TEMPLATE.csv`)

### Merging all data
Once external data and manual templates are completed, merge all sources:
```bash
python scripts/merge_all_data.py
```

This script is expected to output the merged panels used by the app:
- `data/merged/slfsi_daily_panel.csv`
- `data/merged/slfsi_monthly_panel.csv`

## Core Data Streams
The dashboard visualizes 18 core series plus derived features. Core series include:
- FX: USD/LKR exchange rate
- Rates: AWCMR, T-bill, T-bond, policy rates
- Equities: ASPI, S&P SL20, turnover, market cap
- External sector: reserves, REER, ISB yields, tourism earnings, remittances
- Global: gold (USD), US 10Y yield

Derived features include FX returns/volatility, equity returns/volatility, real rates, spreads, and reserve metrics.

## Project Structure
```
.
├── app_regime_analysis.py      # Streamlit application
├── README.md                   # This file
├── README_REGIME_ANALYSIS.md   # Feature walkthrough
├── requirements_regime.txt     # Python dependencies
├── data/                       # Data (external, processed, merged)
└── scripts/                    # Data ingestion/merge utilities
```

## Configuration Notes
- The Streamlit app uses caching for data loading (`st.cache_data`).
- Crisis marker dates are defined in `app_regime_analysis.py` in `CRISIS_DATES`.
- HMM and change-point settings are controlled from the sidebar UI.

## Troubleshooting

### Missing data files
If you see warnings about missing columns or files, confirm the merged panels exist and contain the expected column names. Re-run `scripts/merge_all_data.py` after updating inputs.

### Dependency issues
If `hmmlearn` or `streamlit` are missing, reinstall dependencies:
```bash
pip install -r requirements_regime.txt
```

### yfinance not installed
The external data download script relies on `yfinance`:
```bash
pip install yfinance
```

## References
- Adams, R. P., & MacKay, D. J. (2007). Bayesian online changepoint detection.
- Rabiner, L. R. (1989). A tutorial on hidden Markov models and selected applications in speech recognition.

## License
No license file is included. If you plan to redistribute this project, add a license that matches your usage requirements.
