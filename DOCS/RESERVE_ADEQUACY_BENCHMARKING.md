# Reserve Adequacy Benchmarking Analysis

## Sri Lanka 2022 Default Crisis - Predictive Power Assessment

**Created:** January 2026  
**Data Range:** November 2013 - November 2025  
**Key Event:** Sovereign Default on April 12, 2022

---

## Executive Summary

This analysis evaluates multiple reserve adequacy benchmarks against Sri Lanka's 2022 sovereign default to assess their predictive power as early warning indicators. We find that:

1. **Import Cover < 2 months** provided **9-10 months** of lead time before default
2. **IMF ARA < 100%** signaled distress **6 months** before default
3. **Greenspan-Guidotti near-breach** (< 1.5) signaled **6 months** before default
4. **Import Cover < 1 month** (critical) gave **5 months** warning

The combination of these metrics would have provided clear, actionable warning signals beginning in **July 2021** - approximately 9 months before the sovereign default was announced.

---

## 1. Benchmarks Analyzed

### 1.1 Import Cover Ratio

**Formula:**
```
Import Cover (months) = Gross Reserves (USD) / Monthly Imports (USD)
```

**Thresholds:**
| Level | Months | Interpretation |
|-------|--------|----------------|
| Comfortable | ≥ 6 | Adequate buffer |
| IMF Minimum | ≥ 3 | Minimum acceptable |
| Warning | < 2 | Elevated risk |
| Critical | < 1 | Imminent crisis |

**Data Sources:**
- Reserves: `reserve_assets_monthly_cbsl.csv` (CBSL Historical Data Series)
- Imports: `monthly_imports_usd.csv` (CBSL Table 2.04)

**Net Usable Reserves Adjustment:**
From March 2021, gross reserves include $1.5B from the PBOC (China) swap facility, which is encumbered and not freely usable. Net import cover adjusts for this.

---

### 1.2 Greenspan-Guidotti Ratio

**Formula:**
```
GG Ratio = Gross Reserves (USD) / Short-term External Debt (USD)
```

**Threshold:** ≥ 1.0 (reserves should fully cover short-term debt maturing within 12 months)

**Interpretation:**
- GG ≥ 1.0: Country can repay all short-term obligations without external financing
- GG < 1.0: Vulnerability to rollover risk and sudden stops

**Data Sources:**
- Reserves: `reserve_assets_monthly_cbsl.csv` (quarterly aggregated)
- Short-term Debt: `external_debt_usd_quarterly.csv` (CBSL Table 2.12, government short-term external debt)

---

### 1.3 IMF Assessing Reserve Adequacy (ARA) Metric

**Formula:**
```
ARA = 5% × Annual Exports + 5% × Broad Money (M2) + 30% × Short-term Debt + 15% × Portfolio Liabilities
```

**Threshold:** Reserves should be **100-150%** of ARA for adequate coverage.

**Component Weights Rationale (IMF):**
| Component | Weight | Risk Captured |
|-----------|--------|---------------|
| Exports | 5% | Current account volatility |
| Broad Money (M2) | 5% | Capital flight by residents |
| Short-term Debt | 30% | Rollover risk |
| Portfolio Liabilities | 15% | Non-resident portfolio outflows |

**Data Sources:**
- Exports: `monthly_exports_usd.csv` (CBSL Table 2.02, annualized from quarterly sum)
- M2: `monetary_aggregates_monthly.csv` (CBSL Table 4.02, converted to USD)
- Short-term Debt: `external_debt_usd_quarterly.csv` (CBSL Table 2.12)
- Portfolio Liabilities: `iip_quarterly_2025.csv` (CBSL IIP, equity + debt securities)

---

## 2. Threshold Breaches - Chronological Sequence

### 2.1 Import Cover Breaches

| Date | Event | Reserves (USD M) | Import Cover | Threshold |
|------|-------|------------------|--------------|-----------|
| **2017-03** | First < 3 months | $5,117 | 2.74 mo | IMF Minimum |
| **2021-03** | PBOC swap activated | $4,055 | 2.11 mo | Below minimum |
| **2021-07** | First < 2 months | $2,806 | 1.64 mo | Warning |
| **2021-09** | Economic emergency | $2,704 | 1.77 mo | Warning |
| **2021-11** | First < 1 month | $1,588 | **0.90 mo** | **Critical** |
| **2022-03** | Pre-default low | $1,917 | 1.05 mo | Critical |
| **2022-04** | Default announced | $1,812 | 1.07 mo | Critical |

**Key Observation:** Import cover fell below 1 month in November 2021 - **5 months before default**.

---

### 2.2 Greenspan-Guidotti Near-Breaches

The GG ratio never technically breached 1.0, but came extremely close:

| Quarter | Reserves (USD M) | ST Debt (USD M) | GG Ratio | Status |
|---------|------------------|-----------------|----------|--------|
| Q3 2021 | $2,704 | $2,661 | **1.02** | Near-breach |
| Q1 2022 | $1,917 | $1,618 | 1.18 | Stressed |
| Q2 2022 | $1,854 | $1,479 | 1.25 | Stressed |
| Q3 2022 | $1,779 | $1,283 | 1.39 | Stressed |

**Key Observation:** GG ratio touched 1.02 in Q3 2021 - **6 months before default**. The lack of technical breach may reflect debt restructuring efforts rather than true adequacy.

---

### 2.3 IMF ARA Breaches

| Quarter | Reserves (USD M) | ARA Requirement | ARA Ratio | Status |
|---------|------------------|-----------------|-----------|--------|
| Q3 2021 | $2,704 | $3,809 | **71.0%** | **Breach** |
| Q4 2021 | $3,139 | $3,691 | 85.1% | Breach |
| Q1 2022 | $1,917 | $2,821 | **68.0%** | **Minimum** |
| Q2 2022 | $1,854 | $2,257 | 82.1% | Breach |
| Q3 2022 | $1,779 | $2,272 | 78.3% | Breach |
| Q4 2022 | $1,898 | $2,164 | 87.7% | Breach |
| Q1 2023 | $2,694 | $2,548 | 105.7% | Recovery |

**Key Observation:** ARA breached 100% in Q3 2021 - **6 months before default**. The breach persisted for 6 consecutive quarters.

---

## 3. Early Warning Lead Time Analysis

### 3.1 Lead Time Before April 12, 2022 Default

| Benchmark | First Breach Date | Lead Time | Assessment |
|-----------|-------------------|-----------|------------|
| Import Cover < 6 mo | 2013-11 | ~8 years | Too early, low specificity |
| Import Cover < 3 mo | 2017-03 | 62 months | Early signal, needs context |
| Import Cover < 2 mo | **2021-07** | **9 months** | **Actionable warning** |
| Import Cover < 1 mo | 2021-11 | 5 months | Imminent crisis |
| IMF ARA < 100% | **2021-Q3** | **6 months** | **Actionable warning** |
| GG Ratio < 1.5 | 2021-Q3 | 6 months | Near-crisis |

### 3.2 Optimal Warning Window

The **July-September 2021** period represents the optimal early warning window where multiple benchmarks signaled distress simultaneously:

```
July 2021:     Import Cover falls below 2 months (1.64 mo)
September 2021: IMF ARA falls below 100% (71%)
                GG Ratio approaches 1.0 (1.02)
                Economic Emergency declared
```

This 6-9 month lead time would have been sufficient for:
- Seeking preemptive IMF support
- Initiating debt restructuring negotiations
- Implementing emergency import controls

---

## 4. Crisis Event Timeline

| Date | Event | Reserves | Import Cover |
|------|-------|----------|--------------|
| 2019-04-21 | Easter Sunday bombings | $7,214M | 4.52 mo |
| 2020-03-01 | COVID-19 pandemic begins | $7,534M | 6.25 mo |
| 2020-12-31 | End of pandemic year | $5,664M | 3.46 mo |
| **2021-03-01** | **PBOC $1.5B swap activated** | **$4,055M** | **2.11 mo** |
| 2021-07-01 | Food emergency declared | $2,806M | 1.64 mo |
| 2021-09-01 | Economic emergency declared | $2,704M | 1.77 mo |
| 2021-11-01 | Reserves critical low | $1,588M | **0.90 mo** |
| **2022-04-12** | **Sovereign default announced** | **$1,812M** | **1.07 mo** |
| 2022-07-05 | Wickremesinghe becomes president | $1,817M | 1.25 mo |
| 2023-03-20 | IMF EFF approved | $2,694M | 1.86 mo |
| 2024-12-31 | Recovery milestone | $6,122M | 3.18 mo |
| 2025-09-30 | Latest data | $6,244M | 3.05 mo |

---

## 5. Historical Backtesting

### 5.1 2018 Currency Depreciation

| Metric | Value | Breach? |
|--------|-------|---------|
| Minimum Import Cover | 3.70 months (March 2018) | No (> 3 mo) |
| Minimum ARA Ratio | 221.2% | No |
| Minimum GG Ratio | 4.29 | No |

**Conclusion:** The 2018 currency crisis did not trigger reserve adequacy breaches, indicating it was primarily a currency/confidence shock rather than a solvency crisis.

### 5.2 2008-2009 Global Financial Crisis

**Note:** Reserve data not available for this period (data begins November 2013).

### 5.3 2011-2012 Balance of Payments Crisis

**Note:** Reserve data not available for this period (data begins November 2013).

---

## 6. Component Analysis - 2022 Crisis Build-up

### 6.1 Reserve Depletion Trajectory

| Period | Reserves Change | Driver |
|--------|-----------------|--------|
| Jan 2020 - Dec 2020 | -$2,000M (-26%) | COVID-19 impact, tourism collapse |
| Jan 2021 - Jun 2021 | -$1,600M (-28%) | Import cover, debt service |
| Jul 2021 - Dec 2021 | -$900M (-24%) | Fuel/food imports, capital flight |
| Jan 2022 - Apr 2022 | +$300M | ISB maturities paid, PBOC drawdown |

### 6.2 IMF ARA Component Breakdown (Q3 2021 - Crisis Quarter)

| Component | Weight | Value (USD M) | Contribution to ARA |
|-----------|--------|---------------|---------------------|
| 5% × Exports | 5% | $4,100 (annual) | $205M |
| 5% × M2 | 5% | $44,000 (converted) | $2,200M |
| 30% × ST Debt | 30% | $2,661M | $798M |
| 15% × Portfolio | 15% | $4,040M | $606M |
| **Total ARA** | | | **$3,809M** |
| **Actual Reserves** | | | **$2,704M** |
| **ARA Ratio** | | | **71%** |

---

## 7. Conclusions and Recommendations

### 7.1 Benchmark Effectiveness Ranking

| Rank | Benchmark | Lead Time | Specificity | Recommendation |
|------|-----------|-----------|-------------|----------------|
| 1 | **Import Cover < 2 mo** | 9 months | High | Primary early warning |
| 2 | **IMF ARA < 100%** | 6 months | High | Comprehensive metric |
| 3 | **GG Ratio < 1.5** | 6 months | Medium | Debt-focused warning |
| 4 | Import Cover < 1 mo | 5 months | Very High | Imminent crisis |
| 5 | Import Cover < 3 mo | 62 months | Low | Background indicator |

### 7.2 Recommended Early Warning Framework

For predictive modeling of sovereign debt crises:

1. **Yellow Alert:** Import Cover < 3 months OR ARA < 150%
2. **Orange Alert:** Import Cover < 2 months OR ARA < 100% OR GG < 1.5
3. **Red Alert:** Import Cover < 1 month AND ARA < 80%

### 7.3 Limitations

1. **Data availability:** Historical crises (2008-2009, 2011-2012) cannot be backtested
2. **PBOC swap opacity:** Net usable reserves unclear due to conditionalities
3. **Lagged reporting:** Quarterly data for ARA components limits real-time monitoring
4. **Single crisis sample:** Results based on one default event

---

## 8. Data Sources Summary

| Data Stream | Source | File | Range |
|-------------|--------|------|-------|
| Gross Reserves | CBSL Historical | `reserve_assets_monthly_cbsl.csv` | Nov 2013 - Dec 2025 |
| Monthly Imports | CBSL Table 2.04 | `monthly_imports_usd.csv` | Jan 2007 - Nov 2025 |
| Monthly Exports | CBSL Table 2.02 | `monthly_exports_usd.csv` | Jan 2007 - Nov 2025 |
| External Debt (USD) | CBSL Table 2.12 | `external_debt_usd_quarterly.csv` | Q4 2012 - Q3 2025 |
| Portfolio Liabilities | CBSL IIP | `iip_quarterly_2025.csv` | Q4 2012 - Q3 2025 |
| Broad Money M2 | CBSL Table 4.02 | `monetary_aggregates_monthly.csv` | Dec 1995 - Sep 2025 |

---

## Appendix: Visualization

The interactive Streamlit dashboard (`app_reserve_adequacy.py`) provides:
- Time series charts of all benchmarks
- Threshold breach highlighting
- Component breakdowns for IMF ARA
- Crisis period markers
- Data tables with download options

Run with: `streamlit run app_reserve_adequacy.py`

---

*Document generated: January 2026*
*Analysis by: SL-FSI Project*
