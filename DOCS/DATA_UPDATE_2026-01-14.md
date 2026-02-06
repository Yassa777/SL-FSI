# Data Update: January 14, 2026

## Summary

This document records significant data improvements made to the SL-FSI project.

---

## 1. Reserve Assets Data - MAJOR UPDATE

### Previous State
- **Source**: CBSL + World Bank interpolation
- **Range**: Jan 2018 - Nov 2024 (83 records)
- **2005-2017**: Linearly interpolated from World Bank annual data
- **Components**: Gross reserves only

### New State
- **Source**: CBSL Official Reserve Assets Historical Data Series
- **Range**: Nov 2013 - Dec 2025 (146 actual CBSL records)
- **Full range**: Jan 2005 - Dec 2025 (252 records total)
- **Components**: 
  - `gross_reserves_usd_m` - Total official reserves
  - `fx_reserves_usd_m` - Foreign currency reserves
  - `imf_position_usd_m` - IMF reserve position
  - `sdrs_usd_m` - Special Drawing Rights
  - `gold_usd_m` - Gold holdings
- **Units**: USD millions

### Key Values (Crisis Period)
| Date | Reserves (USD M) | Source |
|------|------------------|--------|
| Jan 2020 | 7,510 | CBSL Historical |
| Aug 2021 | 2,805 | CBSL Historical |
| Apr 2022 | 1,812 (a) | CBSL Historical |
| Dec 2022 | 1,898 (a) | CBSL Historical |
| Dec 2023 | 4,392 (a) | CBSL Historical |
| Dec 2024 | 6,122 (a) | CBSL Historical |
| Dec 2025 | 6,825 (a) | CBSL Historical (provisional) |

**(a)** Includes PBOC swap arrangement proceeds (subject to conditionalities)

### Files Updated
- `data/external/reserve_assets_monthly_cbsl.csv` - NEW: Clean monthly reserves with components
- `data/external/D12_reserves_compiled.csv` - UPDATED: Merged dataset with full history
- `data/external/D12_reserves_compiled_old.csv` - BACKUP: Previous version

---

## 2. Central Government Debt Data - NEW

### Source
- CBSL SDDS Historical Data Series
- File: `Central Government Debt Q3 2025.xlsx`

### Coverage
- **Range**: 2000 (annual) through Q3 2025 (quarterly)
- **Frequency**: Quarterly from 2014 Q1
- **Units**: LKR millions

### Key Fields
| Field | Description |
|-------|-------------|
| `total_debt_lkr_m` | Total central government debt |
| `domestic_debt_lkr_m` | Domestic debt total |
| `domestic_short_term_lkr_m` | Short-term domestic debt |
| `domestic_medium_long_lkr_m` | Medium/long-term domestic debt |
| `foreign_debt_lkr_m` | Foreign debt total |
| `foreign_short_term_lkr_m` | Short-term foreign debt |
| `total_short_term_lkr_m` | Combined short-term debt |

### New Capabilities
This data enables calculation of:
- **Greenspan-Guidotti ratio**: `reserves / short_term_debt`
- Requires conversion from LKR to USD using month-end FX rates

### Files Created
- `data/external/central_govt_debt_quarterly.csv` - Clean quarterly debt data

---

## 3. AWCMR Data - PREVIOUSLY UPDATED

As documented in `WORKING_FEATURE_SET.md`:

### Previous State
- **Range**: Ended December 2020
- **Coverage**: 9.6% of crisis period

### Current State
- **Range**: January 2003 - September 2025
- **Coverage**: 100% of crisis period
- **Source**: CBSL Statistical Tables (table4.04)
- **File**: `data/external/awcmr_monthly_cbsl.csv`

---

## 4. International Investment Position (IIP) Data - NEW

### Source
- CBSL Data Library HTML export
- File: `International Investment Position.xls`

### Coverage
- **Range**: Q1 2005 - Q4 2012 (for portfolio liabilities)
- **Reserves Coverage**: Q1 2005 - Q2 2021 (66 quarters)
- **Frequency**: Quarterly
- **Units**: USD millions

### Key Fields
| Field | Description | Valid Values |
|-------|-------------|--------------|
| `portfolio_liabilities` | Portfolio investment liabilities | 32 (2005-2012) |
| `gross_reserves` | Official reserve assets | 66 (2005-2021) |
| `import_cover_months` | Months of import cover | 67 (2005-2021) |
| `iip_assets` | Total IIP assets | 31 (2005-2012) |

### Limitation
Portfolio liabilities data only extends to 2012 - this predates the crisis period and cannot be used for crisis-era IMF ARA calculations without obtaining updated data.

### Files Created
- `data/external/iip_quarterly_clean.csv`

---

## 5. Money Supply (M2) Data - NEW

### Source
- CBSL Data Library HTML export
- File: `reserve_money.xls`

### Coverage
- **Range**: Jan 2005 - Dec 2013 (108 months for M2)
- **Frequency**: Monthly
- **Units**: LKR millions

### Key Fields
| Field | Description | Valid Values |
|-------|-------------|--------------|
| `broad_money_m2` | Broad money supply M2 | 108 (2005-2013) |
| `broad_money_m2b` | M2b aggregate | 108 (2005-2013) |
| `reserve_money` | Reserve money | 82 values |
| `net_foreign_assets` | NFA of banking system | 49 values |

### Key Values
| Date | M2 (LKR Millions) |
|------|-------------------|
| Dec 2005 | 1,536,755 |
| Dec 2010 | 3,821,803 |
| Dec 2013 | 5,665,313 |

### Limitation
M2 data only extends to 2013 - this predates the crisis period. For IMF ARA calculations during 2020-2024, additional M2 data would need to be sourced.

### Files Created
- `data/external/money_supply_monthly_clean.csv`

---

## 6. Additional Files (Unexplored)

The following files were collected but not yet parsed:

| File | Likely Content | Status |
|------|----------------|--------|
| `table2.12_20251231_e.xlsx` | External sector data | Unexplored |
| `table2.14.*.xlsx` | Various CBSL tables | Unexplored |
| `table2.15.2_20251231_e.xlsx` | Monetary data | Unexplored |

---

## 7. Data Coverage Summary

### Core HMM Features (Crisis Period 2020-2024)

| Feature | Previous Coverage | Current Coverage | Source |
|---------|------------------|------------------|--------|
| `awcmr` | 9.6% (ended 2020) | **100%** | CBSL Monthly |
| `gross_reserves_usd_m` | 100% (interpolated) | **100%** (actual) | CBSL Historical |
| `real_policy_rate` | 100% | 100% | Derived |
| `ncpi_yoy_pct` | 100% | 100% | DCS |

### Extended Coverage

| Data Stream | Range | Records | Frequency |
|-------------|-------|---------|-----------|
| Reserves (actual CBSL) | Nov 2013 - Dec 2025 | 146 | Monthly |
| Reserves (with interpolation) | Jan 2005 - Dec 2025 | 252 | Monthly |
| AWCMR | Jan 2003 - Sep 2025 | 274 | Monthly |
| Central Govt Debt | 2000 - Q3 2025 | 61 | Quarterly |

---

## 8. Reserve Adequacy Benchmarking - Assessment

### Immediately Available (Crisis Period)

| Benchmark | Data | Range | Notes |
|-----------|------|-------|-------|
| **Import Cover** | Reserves / $1.5B monthly imports | Nov 2013 - Dec 2025 | Actual CBSL data |
| **Net Usable Reserves** | Gross - PBOC swap | Mar 2021 - Dec 2025 | PBOC swap = $1.5B |
| **Net Import Cover** | Net reserves / imports | Mar 2021 - Dec 2025 | Adjusted for encumbrances |

### Now Possible (Historical Period)

| Benchmark | Data Required | Status | Coverage |
|-----------|--------------|--------|----------|
| **Greenspan-Guidotti** | Short-term debt | ✅ Available | Q1 2014 - Q3 2025 |
| **IMF ARA (historical)** | M2 + short-term debt + portfolio liabilities | ⚠️ Partial | 2005-2012 only |

### Data Gaps for Full IMF ARA

| Component | Available | Missing |
|-----------|-----------|---------|
| Reserves | Nov 2013 - Dec 2025 | Jan 2005 - Oct 2013 (interpolated) |
| Short-term Debt | Q1 2014 - Q3 2025 | Before 2014 |
| Portfolio Liabilities | 2005-2012 | **2013-2025** ← Gap |
| Broad Money M2 | 2005-2013 | **2014-2025** ← Gap |

**Note**: To calculate IMF ARA for the crisis period (2020-2024), updated Portfolio Liabilities and M2 data would be needed from CBSL.

---

## 9. Scripts and Tools

### Created
- `parse_manual_extraction.py` - Parses CBSL Excel files (reserves, debt)
- `parse_cbsl_html_v2.py` - Parses CBSL HTML exports (IIP, Money Supply)

### Usage
```bash
cd /path/to/SL-FSI
/opt/anaconda3/bin/python parse_manual_extraction.py
/opt/anaconda3/bin/python parse_cbsl_html_v2.py
```

### Output Files
| File | Description |
|------|-------------|
| `reserve_assets_monthly_cbsl.csv` | Monthly reserves Nov 2013 - Dec 2025 |
| `central_govt_debt_quarterly.csv` | Quarterly debt 2000 - Q3 2025 |
| `iip_quarterly_clean.csv` | Quarterly IIP 2005 - 2021 |
| `money_supply_monthly_clean.csv` | Monthly M2 2005 - 2013 |
| `D12_reserves_compiled.csv` | Merged reserve dataset 2005 - 2025 |

---

## 10. Next Steps

### Immediate Actions
1. **Calculate Greenspan-Guidotti ratio** - Convert LKR debt to USD using FX rates and compute reserves/short-term-debt ratio
2. **Update data pipeline** - Incorporate new reserve data into `merge_all_data.py` or ETL scripts
3. **Validate against crisis events** - Confirm reserve thresholds align with known events (Apr 2022 default)

### Data Gaps to Address
1. **Obtain updated M2 data (2014-2025)** - Check CBSL Monthly Bulletin or Statistical Appendix
2. **Obtain updated Portfolio Liabilities (2013-2025)** - Check CBSL IIP releases or IMF IFS
3. **Explore unexplored xlsx files** - May contain additional monetary/external data

### For Full IMF ARA Calculation
The IMF Assessing Reserve Adequacy (ARA) metric requires:
- 5% of Exports
- 5% of Broad Money (M2)
- 30% of Short-term Debt
- 15% of Portfolio Liabilities

Currently available: Exports (partial), Short-term Debt (2014+)
Missing for crisis period: M2 (2014+), Portfolio Liabilities (2013+)

---

*Created: January 14, 2026*
*Updated: January 14, 2026 - Added IIP and Money Supply parsing*
