# SL-FSI Data Inventory

**Last Updated:** December 2024  
**Status:** ✅ Data Acquisition Complete

---

## Summary

| Category | Streams | Coverage | Notes |
|----------|---------|----------|-------|
| CBSL Market Data | 9 | Good | Equity, FX, Rates |
| External Data | 6 | Excellent | Gold, Policy, Macro |
| Derived Features | 12 | Complete | HMM-ready |
| **Total** | **37 columns** | **2018-2025** | Ready for modeling |

---

## Data Streams

### CBSL Processed Data (`data/processed/`)

| ID | Stream | File | Rows | Range | Quality |
|----|--------|------|------|-------|---------|
| D1 | USD/LKR Exchange Rate | `D1_usd_lkr.csv` | 1,169 | 2021-2025 | ✅ Good |
| D2 | AWCMR (Interbank Rate) | `D2_awcmr.csv` | 2,587 | 2010-2020 | ⚠️ Ends 2020 |
| D3 | ASPI (Equity Index) | `D3_aspi.csv` | 3,066 | 2012-2024 | ✅ Good |
| D4 | Equity Turnover | `D4_turnover.csv` | 3,066 | 2012-2024 | ✅ Good |
| D5 | Market Capitalization | `D5_market_cap.csv` | 3,066 | 2012-2024 | ✅ Good |
| D6 | S&P SL20 Index | `D6_D7_sl20_gold.csv` | 3,078 | 2012-2024 | ✅ Good |
| D7 | Local Gold (LKR) | `D6_D7_sl20_gold.csv` | 3,078 | 2012-2024 | ✅ Good |
| D8 | T-Bill Yields | `D8_tbills.csv` | 822 | 2010-2025 | ⚠️ Sparse |
| D9 | T-Bond Yields | `D9_tbonds.csv` | 134 | 2010-2024 | ⚠️ Sparse |
| D14 | REER Index | `D14_reer_nfa.csv` | 187 | 2010-2025 | ✅ Good (monthly) |
| D15 | ISB Yields | `D15_isb.csv` | 200 | 2014-2025 | ✅ Good (monthly) |

### External Data (`data/external/`)

| ID | Stream | File | Rows | Range | Accuracy | Source |
|----|--------|------|------|-------|----------|--------|
| D6 | Global Gold (USD/oz) | `D6_gold_usd.csv` | 4,018 | 2010-2025 | 99%+ | Yahoo Finance |
| D10 | Policy Rates | `D10_policy_rates_daily.csv` | 2,557 | 2019-2025 | 99%+ | CBSL |
| D12 | Official Reserves | `D12_reserves_compiled.csv` | 83 | 2018-2024 | 95-99% | CBSL/IMF |
| D13 | NCPI Inflation | `D13_inflation_monthly_compiled.csv` | 71 | 2019-2024 | 95-99% | CBSL/DCS |
| D17 | Tourism Earnings | `D17_tourism.csv` | 194 | 2009-2025 | 99%+ | CBSL |
| D18 | Remittances | `D18_remittances.csv` | 202 | 2009-2025 | 99%+ | CBSL |
| — | US Treasury 10Y | `us_treasury_10y.csv` | 4,016 | 2010-2025 | 99%+ | Yahoo Finance |

### Merged Panels (`data/merged/`)

| File | Rows | Columns | Frequency | Description |
|------|------|---------|-----------|-------------|
| `slfsi_daily_panel.csv` | 2,922 | 37 | Daily | Full panel, monthly data forward-filled |
| `slfsi_monthly_panel.csv` | 96 | 34 | Monthly | Aggregated for macro analysis |

---

## Derived Features (HMM-Ready)

| Feature | Formula | Description | Coverage |
|---------|---------|-------------|----------|
| `r_fx` | log(FX_t / FX_{t-1}) | FX log return | 36% |
| `vol_fx_20d` | 20d rolling std(r_fx) | FX volatility | 47% |
| `r_eq` | log(ASPI_t / ASPI_{t-1}) | Equity log return | 47% |
| `vol_eq_20d` | 20d rolling std(r_eq) | Equity volatility | 58% |
| `r_eq_real` | r_eq - r_fx | FX-adjusted equity return | 35% |
| `gold_premium_pct` | (gold_lkr/gold_usd)/usd_lkr - 1 | Shadow FX indicator | 36% |
| `interbank_spread` | awcmr - policy_ceiling | Interbank stress | 12% |
| `real_policy_rate` | policy_ceiling - ncpi_yoy_pct | Real interest rate | 100% |
| `import_cover_months` | reserves / 1500 | Import coverage | 100% |
| `reserve_slope_3m` | 3-month regression slope | Reserve drain rate | 100% |
| `turnover_ratio` | turnover / market_cap | Liquidity indicator | 63% |
| `embi_spread_approx` | isb_yield - us_10y | Sovereign risk proxy | 10% |
| `yield_curve_slope` | long_rate - short_rate | Term structure | Low |

---

## Crisis Period Snapshot

Key indicators at critical moments:

| Date | Event | USD/LKR | Reserves ($M) | Inflation | Real Rate |
|------|-------|---------|---------------|-----------|-----------|
| 2021-01-01 | Pre-crisis | ~189 | 5,034 | 4.2% | +1.3% |
| 2022-03-01 | FX float | ~230 | 1,932 | 18.7% | -12.7% |
| 2022-04-12 | Default | 314 | 1,892 | 29.8% | -15.3% |
| 2022-09-15 | Peak inflation | 362 | 1,769 | 69.8% | **-54.3%** |
| 2023-03-01 | IMF deal | 358 | 2,692 | 50.3% | -34.8% |

---

## Known Data Gaps

1. **AWCMR ends 2020** - Need updated interbank rates from CBSL
2. **T-Bill/T-Bond sparse** - Weekly auction data, not daily
3. **ISB yields monthly** - Limited daily coverage
4. **Pre-2021 FX gaps** - Managed float period less documented

---

## Next Steps

1. ✅ Data collection complete
2. ⏳ Feature engineering for HMM
3. ⏳ Fit 2-state and 3-state HMM
4. ⏳ Validate against known crisis dates
5. ⏳ Build Streamlit dashboard
