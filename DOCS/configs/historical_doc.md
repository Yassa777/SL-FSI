# Historical Data Sources Documentation

## Summary

This document describes the data sources and methodology used for the
2005-2017 historical extension of the SL-FSI dataset.

## Data Sources

### 1. Exchange Rate (USD/LKR)
- **Source**: FRED EXSLUS
- **Frequency**: Monthly
- **Coverage**: 2000-2024
- **Type**: REAL DATA (no interpolation)
- **Notes**: Official exchange rate from Federal Reserve

### 2. Inflation (NCPI YoY %)
- **Source**: FRED Annual (FPCPITOTLZGLKA) + CBSL Monthly (2019+)
- **Frequency**: Monthly (interpolated from annual for 2005-2018)
- **Coverage**: 2005-2024
- **Type**: INTERPOLATED
- **Method**: Annual values spread across months with seasonal adjustment
  derived from 2019-2024 monthly data
- **Caveats**:
  - CCPI rebased in 2002, 2006, 2013, 2021
  - Monthly seasonality may differ in historical periods

### 3. Foreign Reserves (USD millions)
- **Source**: World Bank (FI.RES.TOTL.CD)
- **Frequency**: Monthly (interpolated from annual)
- **Coverage**: 2005-2024
- **Type**: INTERPOLATED
- **Method**: Linear interpolation between year-end values
- **Caveats**:
  - Original data is end-of-year stock
  - Intra-year movements approximated

### 4. Interbank Rate (AWCMR)
- **Source**: CBSL (awcmr_monthly_cbsl.csv)
- **Frequency**: Monthly
- **Coverage**: 2003-2025
- **Type**: REAL DATA
- **Notes**: Average Weighted Call Money Rate from CBSL

### 5. Policy Rates
- **Source**: CBSL (2019+), interpolated (2005-2018)
- **Frequency**: Monthly
- **Coverage**: 2005-2025
- **Type**: MIXED (real 2019+, approximated 2005-2018)
- **Caveats**: Policy rate corridor changed in 2014

## Structural Breaks

| Date | Event | Affected Series |
|------|-------|-----------------|
| 2006-01 | CCPI rebase (2002=100) | Inflation |
| 2013-01 | CCPI rebase (2006/07=100) | Inflation |
| 2014-01 | Policy corridor change | Policy rates |
| 2021-01 | CCPI rebase (2013=100) | Inflation |
| 2022-03 | Float exchange rate | USD/LKR |

## Recommendations

1. **For rigorous research**: Use only 2019+ data where monthly series are real
2. **For indicative analysis**: 2005-2025 with interpolation caveats noted
3. **Alternative**: Use annual data directly for 2005-2018 period

## Generated

Date: {date}
Pipeline: {pipeline}
