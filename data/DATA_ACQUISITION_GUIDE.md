# SL-FSI Data Acquisition Guide

This guide provides practical methods to obtain the 8 missing data streams.

---

## 📊 Summary Table

| Stream | Data | Method | Difficulty | Priority |
|--------|------|--------|------------|----------|
| **D6** | Global Gold (USD) | Python (yfinance) | 🟢 Easy | High |
| **D10** | Policy Rates | Manual + CBSL | 🟡 Medium | High |
| **D11** | OMO Liquidity | CBSL Data Library | 🟡 Medium | Low |
| **D12** | Reserves | CBSL Data Library | 🟢 Easy | **Critical** |
| **D13** | Inflation | Census Dept Website | 🟢 Easy | **Critical** |
| **D16** | EMBI+ Spread | Calculate from D15 | 🟢 Easy | Medium |
| **D17** | Tourism | SLTDA Website | 🟡 Medium | Medium |
| **D18** | Remittances | CBSL Data Library | 🟢 Easy | Medium |

---

## D6: Global Gold Price (USD) 🟢

### Method: Python (yfinance)
**This is fully automated - just run the script!**

```python
import yfinance as yf
import pandas as pd

# Download gold futures data
gold = yf.download('GC=F', start='2015-01-01', end='2025-12-31')
gold = gold[['Close']].rename(columns={'Close': 'gold_usd'})
gold.index.name = 'date'
gold.to_csv('data/external/D6_gold_usd.csv')
print(f"Downloaded {len(gold)} days of gold prices")
```

### Alternative: World Gold Council
- URL: https://www.gold.org/goldhub/data/gold-prices
- Format: CSV download available
- Coverage: Daily, going back decades

---

## D10: Policy Rates (SDFR/SLFR/OPR) 🟡

### Method: Manual compilation from CBSL announcements

**Pre-2024 (SDFR/SLFR Corridor):**

| Effective Date | SDFR (Floor) | SLFR (Ceiling) | Source |
|---------------|--------------|----------------|--------|
| 2019-05-31 | 7.00% | 8.00% | MPC |
| 2020-01-30 | 6.50% | 7.50% | MPC |
| 2020-03-16 | 6.25% | 7.25% | Emergency |
| 2020-04-03 | 6.00% | 7.00% | Emergency |
| 2020-04-09 | 5.50% | 6.50% | Emergency |
| 2020-05-06 | 5.50% | 6.50% | MPC |
| 2020-07-08 | 4.50% | 5.50% | MPC |
| 2021-08-19 | 4.50% | 5.50% | MPC |
| 2022-01-20 | 5.00% | 6.00% | MPC |
| 2022-03-04 | 5.50% | 6.50% | Emergency |
| 2022-04-08 | 6.50% | 7.50% | Emergency |
| 2022-04-08 | 13.50% | 14.50% | Emergency |
| 2022-07-08 | 14.50% | 15.50% | MPC |
| 2023-06-01 | 11.00% | 12.00% | MPC |
| 2023-07-13 | 10.00% | 11.00% | MPC |
| 2023-10-04 | 9.00% | 10.00% | MPC |
| 2024-03-26 | 8.50% | 9.50% | MPC |
| 2024-06-04 | 8.25% | 9.25% | MPC |

**Post-2024 (OPR Single Rate):**

| Effective Date | OPR | Notes |
|---------------|-----|-------|
| 2024-09-04 | 8.00% | New framework |
| 2024-11-26 | 7.75% | Current |

### Where to Find Updates:
- https://www.cbsl.gov.lk/en/monetary-policy
- https://www.cbsl.gov.lk/en/news (press releases)

### CSV Format to Create:
```csv
date,sdfr,slfr,opr,notes
2019-05-31,7.00,8.00,,MPC
2020-01-30,6.50,7.50,,MPC
...
2024-09-04,,,8.00,New OPR framework
```

---

## D11: OMO Liquidity 🟡

### Method: CBSL Data Library

**URL:** https://www.cbsl.gov.lk/en/statistics/statistical-tables/monetary-sector

Look for:
- "Standing Deposit Facility"
- "Standing Lending Facility"  
- "Open Market Operations"

### Alternative: CBSL Daily Data
The CBSL publishes daily liquidity conditions. You can find this in:
- CBSL Weekly Economic Indicators
- CBSL Daily Statistics page

**Priority:** LOW - this can be skipped for MVP

---

## D12: Official Foreign Reserves 🔴 CRITICAL

### Method: CBSL Statistical Tables

**URL:** https://www.cbsl.gov.lk/en/statistics/statistical-tables/external-sector

**Navigate to:** "Reserve Data" section → "Reserve Data Template - Historical"

### Alternative: IMF SDDS (High Quality)
The IMF's Special Data Dissemination Standard has standardized reserve data:
- URL: https://dsbb.imf.org/sdds/country/LKA/category/IRS
- Format: Excel downloads available
- Contains: Gross Official Reserves, broken down by category

### Trading Economics (Quick Access):
- URL: https://tradingeconomics.com/sri-lanka/foreign-exchange-reserves
- Has: Monthly data with charts
- Export: Click "Download" for Excel

### Expected Fields:
- Gross Official Reserves (USD millions)
- Net Foreign Assets of Monetary Authorities
- Import Cover (months)

### Known Values (for verification):
| Date | Reserves (USD B) | Source |
|------|-----------------|--------|
| Jan 2020 | 7.5 | CBSL |
| Jan 2021 | 5.5 | CBSL |
| Jan 2022 | 2.4 | CBSL |
| Apr 2022 | 1.9 | CBSL |
| Dec 2023 | 4.4 | CBSL |
| Aug 2025 | 6.2 | Trading Economics |

---

## D13: Inflation (NCPI/CCPI) 🔴 CRITICAL

### Method: Department of Census and Statistics

**URL:** http://www.statistics.gov.lk/

**Direct Link:** http://www.statistics.gov.lk/InflationAndPrices/StaticalInformation/MonthlyCPIBulletins

### What to Download:
1. **NCPI (National CPI)** - Current standard
2. **CCPI (Colombo CPI)** - Historical (pre-2015)

### Data Available:
- Monthly index values (base year = 100)
- Year-over-Year % change (headline inflation)
- Core inflation (excluding food & fuel)

### Trading Economics (Quick Reference):
https://tradingeconomics.com/sri-lanka/inflation-cpi

### Expected CSV Format:
```csv
date,ncpi_index,ncpi_yoy,ccpi_index,ccpi_yoy
2020-01,136.5,5.2,138.2,4.8
2020-02,137.1,5.4,138.9,5.1
...
```

---

## D16: EMBI+ Spread 🟢

### Method: Calculate from existing data!

Since we have D15 (ISB yields), we can approximate the spread:

```python
import pandas as pd
import yfinance as yf

# Get US Treasury 10-year yield
ust = yf.download('^TNX', start='2015-01-01', end='2025-12-31')
ust = ust[['Close']].rename(columns={'Close': 'us_10y_yield'})

# Load our ISB data
isb = pd.read_csv('data/processed/D15_isb.csv', parse_dates=['date'])

# Merge and calculate spread
merged = isb.merge(ust, left_on='date', right_index=True, how='left')
merged['embi_spread_approx'] = merged['isb_yield'] - merged['us_10y_yield']
# Convert to basis points
merged['embi_spread_bps'] = merged['embi_spread_approx'] * 100

merged.to_csv('data/external/D16_embi_spread_approx.csv', index=False)
```

**Note:** This is an approximation. True EMBI+ data requires JP Morgan subscription.

---

## D17: Tourism Arrivals 🟡

### Method: SLTDA Website

**URL:** https://www.sltda.gov.lk/en/statistics

### What's Available:
- Monthly tourist arrivals by country
- Tourism earnings (USD)
- Purpose of visit breakdown

### Alternative: CBSL Data Library
1. Go to CBSL Data Library
2. Select Category: **Real Sector**
3. Look for: **Tourism Arrivals** or **Tourist Arrivals**

### Expected CSV Format:
```csv
date,arrivals,earnings_usd_m
2020-01,228,450
2020-02,207,380
2020-03,71,120
...
```

---

## D18: Worker Remittances 🟢

### Method: CBSL Data Library

**URL:** https://www.cbsl.gov.lk/en/statistics/statistical-tables/external-sector

**Look for:** "Workers' Remittances" under Balance of Payments

### Direct Data Library Query:
1. Go to: https://www.cbsl.gov.lk/cbsl_custom/data/library/index.php
2. Select Category: **External Sector**
3. Select Sub-category: **Balance of Payments**
4. Select Items: "Workers' Remittances"
5. Download as Excel

### Trading Economics (Quick Reference):
https://tradingeconomics.com/sri-lanka/remittances

### Expected CSV Format:
```csv
date,remittances_usd_m
2020-01,567.3
2020-02,542.1
2020-03,489.5
...
```

---

## 🐍 Automated Download Script

Create this file at `scripts/download_external_data.py`:

```python
#!/usr/bin/env python3
"""
Download external data for SL-FSI project
Run: python scripts/download_external_data.py
"""

import os
import pandas as pd
from datetime import datetime

# Create output directory
os.makedirs('data/external', exist_ok=True)

# ============================================================
# D6: Global Gold Price (USD)
# ============================================================
print("Downloading D6: Gold prices...")
try:
    import yfinance as yf
    gold = yf.download('GC=F', start='2015-01-01', end='2025-12-31', progress=False)
    gold = gold[['Close']].rename(columns={'Close': 'gold_usd'})
    gold.index.name = 'date'
    gold = gold.reset_index()
    gold['date'] = pd.to_datetime(gold['date']).dt.date
    gold.to_csv('data/external/D6_gold_usd.csv', index=False)
    print(f"  ✓ Saved {len(gold)} rows to D6_gold_usd.csv")
except Exception as e:
    print(f"  ✗ Error: {e}")
    print("  Install yfinance: pip install yfinance")

# ============================================================
# D16: US Treasury Yield (for EMBI spread calculation)
# ============================================================
print("Downloading US Treasury 10Y yield...")
try:
    import yfinance as yf
    ust = yf.download('^TNX', start='2015-01-01', end='2025-12-31', progress=False)
    ust = ust[['Close']].rename(columns={'Close': 'us_10y_yield'})
    ust.index.name = 'date'
    ust = ust.reset_index()
    ust['date'] = pd.to_datetime(ust['date']).dt.date
    ust.to_csv('data/external/us_treasury_10y.csv', index=False)
    print(f"  ✓ Saved {len(ust)} rows to us_treasury_10y.csv")
except Exception as e:
    print(f"  ✗ Error: {e}")

# ============================================================
# D10: Policy Rates (Manual data)
# ============================================================
print("Creating D10: Policy rates template...")
policy_rates = pd.DataFrame([
    # Pre-2024 SDFR/SLFR Corridor
    ('2019-05-31', 7.00, 8.00, None, 'MPC'),
    ('2020-01-30', 6.50, 7.50, None, 'MPC'),
    ('2020-03-16', 6.25, 7.25, None, 'Emergency'),
    ('2020-04-03', 6.00, 7.00, None, 'Emergency'),
    ('2020-04-09', 5.50, 6.50, None, 'Emergency'),
    ('2020-07-08', 4.50, 5.50, None, 'MPC'),
    ('2022-01-20', 5.00, 6.00, None, 'MPC'),
    ('2022-03-04', 5.50, 6.50, None, 'Emergency'),
    ('2022-04-08', 13.50, 14.50, None, 'Emergency crisis'),
    ('2022-07-08', 14.50, 15.50, None, 'MPC'),
    ('2023-06-01', 11.00, 12.00, None, 'MPC'),
    ('2023-07-13', 10.00, 11.00, None, 'MPC'),
    ('2023-10-04', 9.00, 10.00, None, 'MPC'),
    ('2024-03-26', 8.50, 9.50, None, 'MPC'),
    ('2024-06-04', 8.25, 9.25, None, 'MPC'),
    # Post-2024 OPR
    ('2024-09-04', None, None, 8.00, 'New OPR framework'),
    ('2024-11-26', None, None, 7.75, 'MPC'),
], columns=['date', 'sdfr', 'slfr', 'opr', 'notes'])
policy_rates.to_csv('data/external/D10_policy_rates.csv', index=False)
print(f"  ✓ Saved {len(policy_rates)} rate changes to D10_policy_rates.csv")

# ============================================================
# Summary
# ============================================================
print("\n" + "="*60)
print("DOWNLOAD COMPLETE")
print("="*60)
print("\nAutomated downloads:")
print("  - D6_gold_usd.csv (Global gold prices)")
print("  - us_treasury_10y.csv (For EMBI spread calc)")
print("  - D10_policy_rates.csv (Policy rates - needs verification)")
print("\nManual downloads needed:")
print("  - D12: Reserves → CBSL Data Library (External Sector)")
print("  - D13: Inflation → Census Dept (statistics.gov.lk)")
print("  - D17: Tourism → SLTDA (sltda.gov.lk/en/statistics)")
print("  - D18: Remittances → CBSL Data Library (BoP)")
print("  - D11: OMO Liquidity → CBSL (optional)")
```

---

## 📋 Quick Checklist

### Automated (run the script above):
- [ ] D6: Gold prices ← `yfinance`
- [ ] D10: Policy rates ← Template created, verify
- [ ] D16: EMBI spread ← Calculate from D15 + UST

### Manual Downloads from CBSL Data Library:
Go to: https://www.cbsl.gov.lk/cbsl_custom/data/library/index.php

- [ ] D12: Reserves → External Sector → International Reserves
- [ ] D18: Remittances → External Sector → Balance of Payments
- [ ] D11: OMO → Monetary Sector → OMO (optional)

### Manual Downloads from Other Sources:
- [ ] D13: Inflation → http://www.statistics.gov.lk/InflationAndPrices
- [ ] D17: Tourism → https://www.sltda.gov.lk/en/statistics

---

## 🎯 Minimum Viable Dataset

For MVP, focus on these **4 critical additions**:

1. **D6: Gold (USD)** - Automated via yfinance
2. **D10: Policy Rates** - Use the template provided
3. **D12: Reserves** - Download from CBSL
4. **D13: Inflation** - Download from Census Dept

With these + existing data, you can build:
- Shadow FX indicator (Gold Premium)
- Real rate calculations
- Reserve depletion signal

---

*Last updated: 2024-12-19*

