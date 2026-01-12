# Refactor Inventory (Chunk 0)
Date: 2026-01-XX
Scope: Initial inventory of pipeline and validation scripts to drive config/schema migration.

This document maps current scripts, inputs/outputs, and hardcoded assumptions to guide the package refactor. It is a working artifact and should be updated as new sources are discovered.

---

## 1) Files Reviewed

- `scripts/merge_all_data.py`
- `scripts/download_external_data.py`
- `scripts/fetch_historical_data.py`
- `scripts/compute_leading_indicators.py`
- `app_regime_analysis.py`
- `combined_fsi_hmm.py`
- `compare_fsi_hmm.py`
- `recursive_realtime_hmm.py`
- `out_of_sample_validation.py`
- `feature_overlap_analysis.py`
- `three_panel_comparison.py`
- `transition_dynamics.py`
- `mercado_fsi.py`
- `hmm_cross_country.py`
- `enhance_cross_country_data.py`
- `cross_country_synthesis.py`
- `validate_cross_country_data.py`
- `stress_test_hmm.py`
- `theory_based_classification.py`
- `test_feature_dimensionality.py`
- `enhanced_validation.py`
- `validation_framework.py`
- `cross_country_framework.py`

---

## 2) Pipeline Scripts Inventory

| Script | Purpose | Inputs | Outputs | Notes |
| --- | --- | --- | --- | --- |
| `scripts/merge_all_data.py` | Build daily + monthly panels and derived features. | `data/processed/*.csv`, `data/external/*.csv` | `data/merged/slfsi_daily_panel.csv`, `data/merged/slfsi_monthly_panel.csv` | Forward-fills monthly data to daily before derived features. Prints a coverage report (no file). |
| `scripts/download_external_data.py` | Download and build external datasets + templates. | yfinance, manual policy-rate list | `data/external/D6_gold_usd.csv`, `data/external/us_treasury_10y.csv`, `data/external/D10_policy_rates_daily.csv`, templates for D12/D13/D17/D18 | Network required; manual data entry for reserves, inflation, tourism, remittances. |
| `scripts/fetch_historical_data.py` | Build 2005-2017 historical extension. | FRED (FX, annual inflation), World Bank (reserves), CBSL AWCMR | `data/external/historical_fx.csv`, `data/external/historical_inflation.csv`, `data/external/historical_reserves.csv`, `data/external/HISTORICAL_DATA_METHODOLOGY.md` | Network required; interpolates annual to monthly for inflation and reserves. |
| `scripts/compute_leading_indicators.py` | Compute early-warning indicators. | `data/merged/slfsi_daily_panel.csv`, `data/merged/slfsi_monthly_panel.csv`, optional `data/external/ndf_rates.csv` | `data/merged/monthly_with_indicators.csv` | Uses hardcoded constants (PBOC swap, imports, equilibrium rate). |
| `enhanced_validation.py` | Event alignment with sustained crossing rule. | `data/merged/hmm_probs_monthly.csv` | `data/merged/enhanced_validation_results.csv` | Assumes probability columns `p_calm/p_stress/p_crisis`. |
| `validation_framework.py` | HMM + z-score baseline validation. | `data/merged/slfsi_daily_panel.csv` | `data/merged/validation_results.csv`, `data/merged/monthly_regimes_validated.csv` | Builds monthly data from daily, uses 4-feature set. |
| `cross_country_framework.py` | Cross-country methodology notes and simulated data. | None (prints only) | `data/cross_country/pakistan_crisis_data.csv`, `data/cross_country/ghana_crisis_data.csv` | Mostly documentation + placeholder data. |

---

## 2b) Modeling, Analysis, and Visualization Scripts

| Script | Purpose | Inputs | Outputs | Notes |
| --- | --- | --- | --- | --- |
| `app_regime_analysis.py` | Streamlit dashboard for regime analysis. | `data/merged/slfsi_daily_panel.csv`, `data/merged/slfsi_monthly_panel.csv`, optional `data/merged/monthly_regimes_validated.csv`, `data/merged/validation_results.csv`, `data/merged/mercado_fsi_monthly.csv`, `data/merged/hmm_probs_monthly.csv`, `data/merged/realtime_vs_fullsample_comparison.csv`, `data/merged/combined_fsi_hmm.csv` | None | Hardcoded feature lists and event dates for annotations. |
| `recursive_realtime_hmm.py` | Real-time recursive HMM with probabilities. | `data/merged/slfsi_daily_panel.csv`, `data/merged/hmm_regimes_3state_monthly.csv` | `data/merged/hmm_probs_monthly.csv`, `data/merged/recursive_realtime_results.csv`, `data/merged/realtime_vs_fullsample_comparison.csv` | Interpolates missing monthly values; hardcoded feature list and evaluation start dates. |
| `out_of_sample_validation.py` | Train/test HMM validation (2005-2019 vs 2020-2025). | `data/merged/slfsi_daily_panel.csv` | `data/merged/oos_predictions.csv`, `data/merged/oos_model_params.json` | Hardcoded train/test dates and expected event labels. |
| `validation_framework.py` | HMM + z-score baseline validation. | `data/merged/slfsi_daily_panel.csv` | `data/merged/validation_results.csv`, `data/merged/monthly_regimes_validated.csv` | Uses 4-feature set; window sizes and costs are fixed. |
| `enhanced_validation.py` | Sustained-crossing event alignment. | `data/merged/hmm_probs_monthly.csv` | `data/merged/enhanced_validation_results.csv` | Hardcoded tau/K and event list. |
| `mercado_fsi.py` | Mercado-Park FSI computation (monthly). | `data/merged/slfsi_monthly_panel.csv` | `data/merged/mercado_fsi_monthly.csv`, optional `figures/mercado_fsi.png` | Rolling windows, EMPI lookback, and thresholds are fixed. |
| `combined_fsi_hmm.py` | Combine FSI and HMM probabilities. | `data/merged/mercado_fsi_monthly.csv`, `data/merged/hmm_probs_monthly.csv` | `data/merged/combined_fsi_hmm.csv`, `figures/combined_fsi_hmm.png` | Hardcoded alpha and stress/crisis thresholds. |
| `compare_fsi_hmm.py` | Statistical comparison of FSI vs HMM regimes. | `data/merged/mercado_fsi_monthly.csv`, `data/merged/hmm_regimes_3state_monthly.csv` | None | Hardcoded thresholds and event list. |
| `three_panel_comparison.py` | Generate three-panel visualization of FSI/HMM/combined. | `data/merged/mercado_fsi_monthly.csv`, `data/merged/hmm_probs_monthly.csv`, `data/merged/combined_fsi_hmm.csv` | `figures/three_panel_comparison.png`, `figures/three_panel_comparison_hires.png` | Hardcoded annotation events. |
| `feature_overlap_analysis.py` | Coverage analysis + HMM fit tests across feature sets. | `data/merged/slfsi_daily_panel.csv` | `data/merged/hmm_regimes_working.csv` | Uses crisis window and overlap thresholds from constants. |
| `transition_dynamics.py` | Threshold and transition analysis (STRESS -> CRISIS). | `data/merged/slfsi_daily_panel.csv`, `data/merged/hmm_regimes_3state_monthly.csv` | `data/merged/threshold_breach_timeline.csv`, `data/merged/threshold_summary.csv` | Hardcoded threshold values and key dates. |
| `theory_based_classification.py` | Rule-based regimes from theory thresholds. | `data/merged/monthly_with_indicators.csv` or `data/merged/slfsi_monthly_panel.csv`, optional `data/merged/hmm_probs_monthly.csv` | `data/merged/monthly_with_theory_regimes.csv`, `data/merged/theory_vs_hmm_comparison.csv` | Uses fixed threshold sets (Krugman, Reinhart-Rogoff, Calvo). |
| `test_feature_dimensionality.py` | Tests impact of increasing feature count. | `data/merged/slfsi_daily_panel.csv` | None | Fixed feature sets and coverage thresholds. |
| `stress_test_hmm.py` | Robustness tests on cross-country HMM. | `data/cross_country/pakistan_monthly_enhanced.csv`, `data/cross_country/ghana_monthly_enhanced.csv` | None | Hardcoded seeds and correction factors. |
| `enhance_cross_country_data.py` | Builds monthly PK/GH datasets from confirmed points. | Hardcoded data points | `data/cross_country/pakistan_monthly_enhanced.csv`, `data/cross_country/ghana_monthly_enhanced.csv`, `data/cross_country/combined_monthly_enhanced.csv` | Interpolates to monthly; hardcoded levels and spreads. |
| `hmm_cross_country.py` | Cross-country HMM fit and event validation. | `data/cross_country/pakistan_monthly_enhanced.csv`, `data/cross_country/ghana_monthly_enhanced.csv` | `data/cross_country/pakistan_regimes_3state.csv`, `data/cross_country/ghana_regimes_3state.csv`, `data/cross_country/cross_country_regimes.csv` | Regime mapping based on inflation/real-rate severity. |
| `validate_cross_country_data.py` | Compare estimates to World Bank/FRED annual data. | `data/cross_country/pakistan_monthly_enhanced.csv`, `data/cross_country/ghana_monthly_enhanced.csv` | `data/cross_country/pakistan_validation_vs_worldbank.csv`, `data/cross_country/ghana_validation_vs_worldbank.csv` | Hardcoded annual actuals. |
| `cross_country_synthesis.py` | Cross-country crisis pattern synthesis. | `data/merged/hmm_regimes_3state_monthly.csv`, `data/cross_country/pakistan_regimes_3state.csv`, `data/cross_country/ghana_regimes_3state.csv` | `data/cross_country/crisis_summary_comparison.csv` | Remaps Sri Lanka regime codes. |

---

## 3) ETL Input Sources (Current Hardcoded Paths + Column Maps)

### 3.1 Processed (daily/weekly) data: `data/processed/`

| Source ID | File | Columns Used | Canonical Name | Frequency | Notes |
| --- | --- | --- | --- | --- | --- |
| D1 | `D1_usd_lkr.csv` | `USD_Spot_Rate` | `usd_lkr` | Daily | |
| D2 (fallback) | `D2_awcmr.csv` | `Average_Weighted_Call_Money_Rate` | `awcmr` | Daily | Only if external monthly AWCMR missing. |
| D3 | `D3_aspi.csv` | `EQUITY__All_share_price_index` | `aspi` | Daily | |
| D4 | `D4_turnover.csv` | `EQUITY__Daily_Turnover` | `equity_turnover` | Daily | |
| D5 | `D5_market_cap.csv` | `EQUITY_Market_Capitalization` | `market_cap` | Daily | |
| D6/D7 | `D6_D7_sl20_gold.csv` | `EQUITY_S&P_SL20_Index`, `Gold_Price` | `sl20_index`, `gold_lkr` | Daily | |
| D8 | `D8_tbills.csv` | any col with "Primary"/"Secondary" | `tbill_primary`, `tbill_secondary` | Weekly/Daily | Column detection is string-based. |
| D9 | `D9_tbonds.csv` | any col with "Secondary" | `tbond_yield` | Weekly/Daily | Column detection is string-based. |
| D14 | `D14_reer_nfa.csv` | `Real_Effective_Exchange_Rate_Index` | `reer_index` | Monthly | |
| D15 | `D15_isb.csv` | any col with "ISB" | `isb_yield` | Weekly/Daily | |

### 3.2 External (daily/monthly) data: `data/external/`

| Source ID | File | Columns Used | Canonical Name | Frequency | Notes |
| --- | --- | --- | --- | --- | --- |
| D2 (preferred) | `awcmr_monthly_cbsl.csv` | `awcmr_monthly` | `awcmr` | Monthly | Preferred over processed daily AWCMR. |
| D6 | `D6_gold_usd.csv` | `gold_usd_oz` | `gold_usd` | Daily | From yfinance. |
| D10 | `D10_policy_rates_daily.csv` | `sdfr`, `slfr`, `opr`, `policy_ceiling` | same | Daily | Built by `scripts/download_external_data.py`. |
| D12 | `D12_reserves_compiled.csv` | `gross_reserves_usd_m` | same | Monthly | Manual compilation. |
| D13 | `D13_inflation_monthly_compiled.csv` | `ncpi_yoy_pct` | same | Monthly | Manual compilation. |
| D17 | `D17_tourism.csv` | `tourism_earnings_usd_m` | same | Monthly | Manual compilation. |
| D18 | `D18_remittances.csv` | `remittances_usd_m` | same | Monthly | Manual compilation. |
| D16 helper | `us_treasury_10y.csv` | `us_10y_yield_pct` | `us_10y_yield` | Daily | From yfinance. |

### 3.3 Historical extension (2005-2017): `data/external/`

| Source ID | File | Columns Used | Canonical Name | Frequency | Notes |
| --- | --- | --- | --- | --- | --- |
| Hist FX | `historical_fx.csv` | `usd_lkr` | `usd_lkr` | Monthly | FRED EXSLUS. |
| Hist inflation | `historical_inflation.csv` | `ncpi_yoy_pct` | `ncpi_yoy_pct` | Monthly | Interpolated from annual FRED. |
| Hist reserves | `historical_reserves.csv` | `gross_reserves_usd_m` | same | Monthly | Interpolated from World Bank annual. |
| Hist policy | `historical_policy_rates.csv` | `policy_ceiling` | `policy_ceiling` | Monthly | Used to backfill D10 policy data. |

---

## 4) Derived Features and Frequency Rules (Current)

### Daily features (computed in `scripts/merge_all_data.py`)
- `r_fx`, `vol_fx_20d`
- `r_eq`, `vol_eq_20d`
- `r_eq_real`
- `implied_fx`, `gold_premium_pct`
- `reserve_slope_3m`
- `import_cover_months`, `net_usable_reserves_usd_m`, `net_import_cover_months`
- `interbank_spread`
- `real_policy_rate`
- `yield_curve_slope`
- `turnover_ratio`
- `embi_spread_approx`

### Monthly aggregation rules (computed in `scripts/merge_all_data.py`)
- Prices/rates: last-of-month
- Turnover: sum
- Volatility: mean of daily vol series
- Macro: last-of-month
- Derived: last-of-month

### Frequency discipline risk
Monthly series are forward-filled into the daily panel before derived features are calculated. This will be re-ordered in the refactor to compute monthly features first, then upsample if needed.

---

## 5) Outputs and Artifacts

| Output | Producer | Notes |
| --- | --- | --- |
| `data/merged/slfsi_daily_panel.csv` | `scripts/merge_all_data.py` | Daily panel with forward-filled monthly series and daily derived features. |
| `data/merged/slfsi_monthly_panel.csv` | `scripts/merge_all_data.py` | Monthly aggregation of daily panel. |
| `data/merged/monthly_with_indicators.csv` | `scripts/compute_leading_indicators.py` | Monthly panel with early-warning indicators. |
| `data/merged/mercado_fsi_monthly.csv` | `mercado_fsi.py` | Mercado-Park FSI components and index. |
| `figures/mercado_fsi.png` | `mercado_fsi.py` | FSI visualization (if matplotlib available). |
| `data/merged/hmm_probs_monthly.csv` | `recursive_realtime_hmm.py` | Real-time regime probabilities. |
| `data/merged/recursive_realtime_results.csv` | `recursive_realtime_hmm.py` | Full recursive results. |
| `data/merged/realtime_vs_fullsample_comparison.csv` | `recursive_realtime_hmm.py` | Real-time vs full-sample comparison. |
| `data/merged/combined_fsi_hmm.csv` | `combined_fsi_hmm.py` | Combined FSI-HMM score. |
| `data/merged/oos_predictions.csv` | `out_of_sample_validation.py` | Out-of-sample regime probabilities. |
| `data/merged/oos_model_params.json` | `out_of_sample_validation.py` | Training scaler + model metadata. |
| `data/merged/hmm_regimes_working.csv` | `feature_overlap_analysis.py` | Regimes for best-coverage feature set. |
| `data/merged/threshold_breach_timeline.csv` | `transition_dynamics.py` | Threshold breach timeline. |
| `data/merged/threshold_summary.csv` | `transition_dynamics.py` | Summary table of thresholds. |
| `data/merged/validation_results.csv` | `validation_framework.py` | Event alignment results. |
| `data/merged/monthly_regimes_validated.csv` | `validation_framework.py` | Monthly regimes + labels. |
| `data/merged/enhanced_validation_results.csv` | `enhanced_validation.py` | Sustained crossing results. |
| `data/merged/monthly_with_theory_regimes.csv` | `theory_based_classification.py` | Theory-based regimes appended to monthly panel. |
| `data/merged/theory_vs_hmm_comparison.csv` | `theory_based_classification.py` | Theory vs HMM comparison table. |
| `data/cross_country/pakistan_monthly_enhanced.csv` | `enhance_cross_country_data.py` | Monthly Pakistan estimates. |
| `data/cross_country/ghana_monthly_enhanced.csv` | `enhance_cross_country_data.py` | Monthly Ghana estimates. |
| `data/cross_country/combined_monthly_enhanced.csv` | `enhance_cross_country_data.py` | Combined PK/GH monthly panel. |
| `data/cross_country/pakistan_regimes_3state.csv` | `hmm_cross_country.py` | Pakistan regime output. |
| `data/cross_country/ghana_regimes_3state.csv` | `hmm_cross_country.py` | Ghana regime output. |
| `data/cross_country/cross_country_regimes.csv` | `hmm_cross_country.py` | Combined cross-country regimes. |
| `data/cross_country/pakistan_validation_vs_worldbank.csv` | `validate_cross_country_data.py` | PK validation vs World Bank. |
| `data/cross_country/ghana_validation_vs_worldbank.csv` | `validate_cross_country_data.py` | GH validation vs World Bank. |
| `data/cross_country/crisis_summary_comparison.csv` | `cross_country_synthesis.py` | Cross-country crisis summary. |
| `data/cross_country/pakistan_crisis_data.csv` | `cross_country_framework.py` | Simulated Pakistan crisis data. |
| `data/cross_country/ghana_crisis_data.csv` | `cross_country_framework.py` | Simulated Ghana crisis data. |
| `figures/combined_fsi_hmm.png` | `combined_fsi_hmm.py` | Combined score visualization. |
| `figures/three_panel_comparison.png` | `three_panel_comparison.py` | Main three-panel figure. |
| `figures/three_panel_comparison_hires.png` | `three_panel_comparison.py` | High-res three-panel figure. |
| `data/external/HISTORICAL_DATA_METHODOLOGY.md` | `scripts/fetch_historical_data.py` | Historical data method doc. |

---

## 6) Hardcoded Assumptions to Migrate Into Config

- Paths: `data/processed`, `data/external`, `data/merged`
- Column name mappings (string-matched in D8/D9/D15)
- Constants:
  - `PBOC_SWAP_USD_M = 1500`
  - `PBOC_SWAP_START = 2021-03-01`
  - `MONTHLY_IMPORTS_USD_M = 1500`
  - `EQUILIBRIUM_REAL_RATE = 2.0`
  - HMM features: `['awcmr', 'real_policy_rate', 'gross_reserves_usd_m', 'ncpi_yoy_pct']`
  - HMM hyperparameters (components, window sizes, thresholds)
  - Mercado FSI windows: `ROLLING_WINDOW`, `EMPI_LOOKBACK`, `MIN_PERIODS`
  - FSI-HMM combination: `ALPHA`, `STRESS_THRESHOLD`, `CRISIS_THRESHOLD`
  - Validation windows/thresholds: `TAU`, `K`, `TACTICAL_WINDOW`, `STRATEGIC_WINDOW`
  - Transition thresholds: reserves/inflation/real-rate/AWCMR levels in `transition_dynamics.py`
  - Cross-country assumptions: interpolated monthly points, interbank spreads, World Bank annual actuals
- Date ranges:
  - `START_DATE = 2005-01-01`
  - `END_DATE = 2025-12-31`
  - Train/test splits (`TRAIN_START`, `TRAIN_END`, `TEST_START`, `TEST_END`)
  - Recursive HMM windows (`START_DATE`, `EVAL_START`)

---

## 7) Immediate Refactor Risks

- Monthly series are forward-filled before feature generation (risk of mixed-frequency artifacts).
- Quality checks are printed only (no structured output for automated gating).
- Validation scripts assume specific file names and columns without schema checks.
- Event lists are embedded in multiple scripts (risk of divergence).
 - Regime labeling differs across scripts (e.g., cross-country remaps Sri Lanka regime codes).

---

## 8) Migration Map + Order (Tracking)

### Script -> Module Map

| Script | Target module(s) | Status |
| --- | --- | --- |
| `scripts/merge_all_data.py` | `slfsi/pipelines/build_panel.py`, `slfsi/etl/*` | removed; use CLI |
| `scripts/download_external_data.py` | `slfsi/pipelines/download_external.py`, `slfsi/io/readers.py` | removed; use CLI |
| `scripts/fetch_historical_data.py` | `slfsi/pipelines/fetch_historical.py`, `slfsi/io/readers.py` | removed; use CLI |
| `scripts/compute_leading_indicators.py` | `slfsi/pipelines/leading_indicators.py` | removed; use CLI |
| `validation_framework.py` | `slfsi/validation/framework.py`, `slfsi/pipelines/validate.py` | removed; use CLI |
| `enhanced_validation.py` | `slfsi/validation/enhanced.py`, `slfsi/pipelines/validate.py` | removed; use CLI |
| `recursive_realtime_hmm.py` | `slfsi/models/hmm/realtime.py`, `slfsi/pipelines/train_hmm.py` | removed; use CLI |
| `out_of_sample_validation.py` | `slfsi/models/hmm/oos.py`, `slfsi/pipelines/train_hmm.py` | removed; use CLI |
| `mercado_fsi.py` | `slfsi/models/mercado.py`, `slfsi/pipelines/mercado.py` | removed; use CLI |
| `combined_fsi_hmm.py` | `slfsi/models/combine.py`, `slfsi/pipelines/combine.py` | removed; use CLI |
| `compare_fsi_hmm.py` | `slfsi/validation/compare.py` | removed; use CLI |
| `three_panel_comparison.py` | `slfsi/plots/three_panel.py` | removed; use CLI |
| `feature_overlap_analysis.py` | `slfsi/validation/feature_overlap.py` | removed; use CLI |
| `transition_dynamics.py` | `slfsi/validation/transitions.py` | removed; use CLI |
| `theory_based_classification.py` | `slfsi/models/theory.py` | removed; use CLI |
| `app_regime_analysis.py` | keep as app; read from `slfsi` modules/configs | updated to use config |

### Ordered Migration Sequence

1) Core IO + external data pipelines  
2) Deprecate legacy ETL entrypoint  
3) Feature modules + Mercado FSI  
4) HMM model pipelines  
5) Validation utilities  
6) Visualization + app  
7) Final cleanup  
