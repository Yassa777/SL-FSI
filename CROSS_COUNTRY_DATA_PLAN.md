# Cross-Country Data Collection & Extension Plan

**Created**: January 3, 2026
**Status**: Data gathering phase

---

## Current Status

### What We Have ✓
1. **Framework**: cross_country_framework.py with crisis timeline comparisons
2. **Simulated quarterly data**: Pakistan and Ghana (2021-2024) based on public reports
3. **Threshold analysis**: Basic regime detection working
4. **Sri Lanka baseline**: Complete 3-state HMM model with validated regimes

### What We Need
1. **Monthly frequency data** (not quarterly) for Pakistan and Ghana (2020-2024)
2. **Four features** matching SL-FSI methodology:
   - Interbank/Call Money Rate (AWCMR equivalent)
   - Inflation (CPI YoY %)
   - Foreign Exchange Reserves (USD million)
   - Real Policy Rate (Policy Rate - Inflation)

---

## Data Sources Identified

### Pakistan - State Bank of Pakistan (SBP)

| Variable | Source | URL | Notes |
|----------|--------|-----|-------|
| **Foreign Reserves** | SBP Economic Data | [forex.pdf](https://www.sbp.org.pk/ecodata/forex.pdf) | Monthly SBP + Banks reserves |
| **KIBOR** | SBP Easy Data | [easydata.sbp.org.pk](https://easydata.sbp.org.pk/apex/f?p=10:210:) | Karachi Interbank Offered Rate |
| **Policy Rate** | SBP Monetary Policy | [sbp.org.pk/ecodata](https://www.sbp.org.pk/ecodata/index2.asp) | Official policy rate changes |
| **Inflation (CPI)** | Pakistan Bureau of Statistics | [pbs.gov.pk/cpi](https://www.pbs.gov.pk/cpi) | Monthly CPI YoY % |

**Alternative**: IMF Country Reports for Pakistan have confirmed data points:
- April 2024: Reserves ~$8B, Inflation 20.7%
- Early 2024: Reserves ~$4.5B (program start)
- 2023 crisis: Reserves hit $3.7B (January 2023)

### Ghana - Bank of Ghana (BoG)

| Variable | Source | URL | Notes |
|----------|--------|-----|-------|
| **Foreign Reserves** | BoG Economic Data | [Summary of Economic Data](https://www.bog.gov.gh/wp-content/uploads/2024/11/Summary-of-Economic-and-Financial-Data-November-2024.pdf) | Gross + Net International Reserves |
| **Interbank Rate** | BoG Monetary Stats | [bog.gov.gh](https://www.bog.gov.gh/) | Statistical Database |
| **Policy Rate** | BoG Monetary Policy Reports | [Monetary Policy Report](https://www.bog.gov.gh/wp-content/uploads/2024/01/Monetary-Policy-Report-January-2024.pdf) | Policy rate decisions |
| **Inflation (CPI)** | Ghana Statistical Service | [statsghana.gov.gh](https://www.statsghana.gov.gh/) | Monthly CPI |

**Confirmed data points from BoG**:
- November 2024: Gross Reserves $7,893.6M, Net $5,364.6M
- September 2025: Policy rate cut to 21.50%
- Crisis period: Policy rate peaked at 30% (2022-2023)

---

## Data Collection Strategy

### Option 1: Manual Download (Most Reliable)
1. Visit each official source website
2. Download Excel/PDF files for 2020-2024 period
3. Extract monthly data into standardized CSV format
4. Save to `data/cross_country/` directory

### Option 2: API/Programmatic Access
- IMF Data API: [data.imf.org](https://data.imf.org/)
- World Bank API: [api.worldbank.org](https://api.worldbank.org/)
- FRED (St. Louis Fed): Has Ghana inflation data

### Option 3: Enhanced Simulated Data
- Use confirmed data points from IMF/BoG reports
- Interpolate monthly values between known quarterly/annual figures
- Document assumptions clearly
- Compare against actual data when available

---

## Data Structure Required

### Target Format (matching slfsi_daily_panel.csv)

```csv
date,country,reserves_usd_m,inflation_yoy,policy_rate,real_policy_rate,interbank_rate
2020-01-01,Pakistan,12000,8.3,13.25,4.95,13.50
2020-02-01,Pakistan,11800,12.4,13.25,0.85,13.60
...
```

### Key Fields
- `date`: First day of month (YYYY-MM-DD)
- `country`: "Pakistan" or "Ghana"
- `reserves_usd_m`: Foreign exchange reserves in USD millions
- `inflation_yoy`: CPI inflation year-over-year percentage
- `policy_rate`: Central bank policy rate percentage
- `real_policy_rate`: Policy rate minus inflation
- `interbank_rate`: KIBOR (Pakistan) or BoG interbank rate (Ghana)

---

## Validation Events

### Pakistan Crisis Timeline
| Date | Event | Expected Regime |
|------|-------|-----------------|
| 2022-04 | Imran Khan ousted, political crisis begins | STRESS → CRISIS |
| 2022-06 | IMF program stalls, reserve depletion | CRISIS |
| 2023-01 | **Reserves hit $3.7B** (crisis low) | CRISIS |
| 2023-06 | IMF standby arrangement approved | CRISIS → STRESS |
| 2024-04 | Reserves recover to $8B | STRESS → CALM |

### Ghana Crisis Timeline
| Date | Event | Expected Regime |
|------|-------|-----------------|
| 2022-07 | Government approaches IMF | STRESS |
| 2022-12 | **Domestic debt exchange** (default) | CRISIS |
| 2023-01 | Peak inflation 54%, reserves critical | CRISIS |
| 2023-05 | IMF Extended Credit Facility approved | CRISIS → STRESS |
| 2024-01 | External bondholder restructuring | STRESS |

---

## Analysis Pipeline

### Phase 1: Data Preparation
```python
# 1. Load and merge data from all sources
pakistan_data = combine_pk_sources()
ghana_data = combine_gh_sources()

# 2. Standardize to monthly frequency
# 3. Calculate derived features (real_policy_rate)
# 4. Handle missing values (forward fill if needed)
# 5. Save to: data/cross_country/pakistan_monthly.csv
#            data/cross_country/ghana_monthly.csv
```

### Phase 2: HMM Application
```python
# Apply same 3-state HMM as Sri Lanka
features = ['interbank_rate', 'real_policy_rate', 'reserves_usd_m', 'inflation_yoy']

# Use diagonal covariance (better for limited data)
model = GaussianHMM(n_components=3, covariance_type="diag", n_iter=300)

# Fit separately for each country
pakistan_regimes = fit_hmm(pakistan_data)
ghana_regimes = fit_hmm(ghana_data)
```

### Phase 3: Cross-Country Comparison
```python
# 1. Align regime timelines
# 2. Compare transition patterns
# 3. Calculate early warning lead times
# 4. Validate against crisis events
# 5. Document common vs. country-specific patterns
```

---

## Expected Findings

### Common Patterns (Hypothesized)
1. **Reserve collapse leads** (6-12 months before crisis)
2. **Inflation follows** (peaks during acute crisis)
3. **Real rates deeply negative** (loss of monetary control)
4. **3+ threshold breaches = crisis regime**

### Country Differences
- **Pakistan**: Political crisis amplified economic stress
- **Ghana**: Faster escalation to sovereign default
- **Sri Lanka**: Longer build-up period (fertilizer ban, tourism collapse)

---

## Deliverables

### Code
- [ ] `data_collection_pk.py` - Pakistan data gathering script
- [ ] `data_collection_gh.py` - Ghana data gathering script
- [ ] `hmm_pakistan.py` - Apply HMM to Pakistan data
- [ ] `hmm_ghana.py` - Apply HMM to Ghana data
- [ ] `cross_country_comparison.py` - Synthesize findings

### Data Files
- [ ] `data/cross_country/pakistan_monthly.csv` - Full monthly data
- [ ] `data/cross_country/ghana_monthly.csv` - Full monthly data
- [ ] `data/cross_country/pakistan_regimes_3state.csv` - HMM results
- [ ] `data/cross_country/ghana_regimes_3state.csv` - HMM results
- [ ] `data/cross_country/cross_country_comparison.csv` - Synthesis

### Documentation
- [ ] Cross-country validation section for paper
- [ ] Methodology appendix (data sources, processing)
- [ ] Regime timeline visualizations

---

## Next Steps (Priority Order)

1. **Immediate**: Download Pakistan monthly data
   - Start with SBP forex.pdf (reserves)
   - Get KIBOR from SBP EasyData
   - PBS CPI data

2. **Immediate**: Download Ghana monthly data
   - BoG Summary of Economic Data
   - BoG Monetary Policy Reports (policy rates)
   - Ghana Statistical Service CPI

3. **Next**: Process and standardize data
   - Convert to common monthly format
   - Calculate real policy rate
   - Handle any data gaps

4. **Then**: Apply HMM methodology
   - Fit 3-state models
   - Validate regime assignments
   - Compare early warning performance

5. **Finally**: Write up findings
   - Cross-country comparison
   - External validity discussion
   - Policy implications

---

## Alternative Approach: Use What We Have

If manual data collection is too time-consuming, we can:

1. **Enhance simulated data** with confirmed values from IMF/BoG reports
2. **Convert to monthly frequency** by linear interpolation
3. **Run HMM analysis** to test if methodology replicates
4. **Document limitations** clearly in paper
5. **Present as "proof of concept"** for cross-country validation

This approach trades some precision for speed, but still demonstrates:
- Methodology is not Sri Lanka-specific
- Same patterns emerge in other crises
- Framework has external validity

---

*Updated: January 3, 2026*
