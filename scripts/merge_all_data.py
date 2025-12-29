#!/usr/bin/env python3
"""
SL-FSI Data Merger
==================
Combines all 18 data streams into a unified panel dataset.

Handles:
- Daily market data (FX, equities, rates)
- Weekly auction data (T-bills, T-bonds)
- Monthly macro data (reserves, inflation, tourism, remittances)

Output:
- data/merged/slfsi_daily_panel.csv - Daily frequency, monthly data forward-filled
- data/merged/slfsi_monthly_panel.csv - Monthly frequency for macro analysis

Run: python scripts/merge_all_data.py
"""

import pandas as pd
import numpy as np
import os
from datetime import datetime

# ============================================================
# Configuration
# ============================================================

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PROCESSED_DIR = os.path.join(PROJECT_ROOT, 'data', 'processed')
EXTERNAL_DIR = os.path.join(PROJECT_ROOT, 'data', 'external')
OUTPUT_DIR = os.path.join(PROJECT_ROOT, 'data', 'merged')

os.makedirs(OUTPUT_DIR, exist_ok=True)

# Date range for analysis
START_DATE = '2018-01-01'
END_DATE = '2025-12-31'

print("="*70)
print("SL-FSI DATA MERGER")
print("="*70)
print(f"Date range: {START_DATE} to {END_DATE}")

# ============================================================
# Helper Functions
# ============================================================

def load_csv(filepath, date_col='date'):
    """Load CSV with date parsing."""
    if os.path.exists(filepath):
        df = pd.read_csv(filepath)
        df[date_col] = pd.to_datetime(df[date_col])
        return df
    else:
        print(f"  ⚠ Not found: {filepath}")
        return None

def clean_numeric(df, cols=None):
    """Convert columns to numeric, handling errors."""
    if cols is None:
        cols = [c for c in df.columns if c != 'date']
    for col in cols:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors='coerce')
    return df

# ============================================================
# Load CBSL Processed Data (Daily/Weekly)
# ============================================================

print("\n📊 Loading CBSL processed data...")

# D1: USD/LKR Exchange Rate
d1 = load_csv(os.path.join(PROCESSED_DIR, 'D1_usd_lkr.csv'))
if d1 is not None:
    d1 = d1.rename(columns={'USD_Spot_Rate': 'usd_lkr'})
    d1 = clean_numeric(d1)
    d1 = d1[['date', 'usd_lkr']].dropna()
    print(f"  D1 USD/LKR: {len(d1)} rows")

# D2: AWCMR (Interbank Rate)
d2 = load_csv(os.path.join(PROCESSED_DIR, 'D2_awcmr.csv'))
if d2 is not None:
    d2 = d2.rename(columns={'Average_Weighted_Call_Money_Rate': 'awcmr'})
    d2 = clean_numeric(d2)
    d2 = d2[['date', 'awcmr']].dropna()
    print(f"  D2 AWCMR: {len(d2)} rows")

# D3: ASPI (Equity Index)
d3 = load_csv(os.path.join(PROCESSED_DIR, 'D3_aspi.csv'))
if d3 is not None:
    d3 = d3.rename(columns={'EQUITY__All_share_price_index': 'aspi'})
    d3 = clean_numeric(d3)
    d3 = d3[['date', 'aspi']].dropna()
    print(f"  D3 ASPI: {len(d3)} rows")

# D4: Equity Turnover
d4 = load_csv(os.path.join(PROCESSED_DIR, 'D4_turnover.csv'))
if d4 is not None:
    d4 = d4.rename(columns={'EQUITY__Daily_Turnover': 'equity_turnover'})
    d4 = clean_numeric(d4)
    d4 = d4[['date', 'equity_turnover']].dropna()
    print(f"  D4 Turnover: {len(d4)} rows")

# D5: Market Cap
d5 = load_csv(os.path.join(PROCESSED_DIR, 'D5_market_cap.csv'))
if d5 is not None:
    d5 = d5.rename(columns={'EQUITY_Market_Capitalization': 'market_cap'})
    d5 = clean_numeric(d5)
    d5 = d5[['date', 'market_cap']].dropna()
    print(f"  D5 Market Cap: {len(d5)} rows")

# D6/D7: SL20 + Local Gold
d6d7 = load_csv(os.path.join(PROCESSED_DIR, 'D6_D7_sl20_gold.csv'))
if d6d7 is not None:
    d6d7 = d6d7.rename(columns={
        'EQUITY_S&P_SL20_Index': 'sl20_index',
        'Gold_Price': 'gold_lkr'
    })
    d6d7 = clean_numeric(d6d7)
    d6d7 = d6d7[['date', 'sl20_index', 'gold_lkr']]
    print(f"  D6/D7 SL20+Gold: {len(d6d7)} rows")

# D8: T-Bill Yields
d8 = load_csv(os.path.join(PROCESSED_DIR, 'D8_tbills.csv'))
if d8 is not None:
    # Rename the columns we have - processed file may have truncated names
    rename_map = {}
    for col in d8.columns:
        if 'Primary' in col:
            rename_map[col] = 'tbill_primary'
        elif 'Secondary' in col:
            rename_map[col] = 'tbill_secondary'
    if rename_map:
        d8 = d8.rename(columns=rename_map)
    d8 = clean_numeric(d8)
    cols = ['date'] + [c for c in d8.columns if c != 'date']
    d8 = d8[cols]
    print(f"  D8 T-Bills: {len(d8)} rows, cols: {[c for c in d8.columns if c != 'date']}")
else:
    d8 = None

# D9: T-Bond Yields
d9 = load_csv(os.path.join(PROCESSED_DIR, 'D9_tbonds.csv'))
if d9 is not None:
    rename_map = {}
    for col in d9.columns:
        if 'Secondary' in col:
            rename_map[col] = 'tbond_yield'
    if rename_map:
        d9 = d9.rename(columns=rename_map)
    d9 = clean_numeric(d9)
    cols = ['date'] + [c for c in d9.columns if c != 'date']
    d9 = d9[cols]
    print(f"  D9 T-Bonds: {len(d9)} rows, cols: {[c for c in d9.columns if c != 'date']}")
else:
    d9 = None

# D14: REER
d14 = load_csv(os.path.join(PROCESSED_DIR, 'D14_reer_nfa.csv'))
if d14 is not None:
    d14 = d14.rename(columns={'Real_Effective_Exchange_Rate_Index': 'reer_index'})
    d14 = clean_numeric(d14)
    d14 = d14[['date', 'reer_index']].dropna(subset=['reer_index'])
    print(f"  D14 REER: {len(d14)} rows")

# D15: ISB Yields
d15 = load_csv(os.path.join(PROCESSED_DIR, 'D15_isb.csv'))
if d15 is not None:
    # Find the ISB yield column
    for col in d15.columns:
        if 'ISB' in col or 'isb' in col.lower():
            d15 = d15.rename(columns={col: 'isb_yield'})
            break
    d15 = clean_numeric(d15)
    if 'isb_yield' in d15.columns:
        d15 = d15[['date', 'isb_yield']].dropna()
        print(f"  D15 ISB: {len(d15)} rows")

# ============================================================
# Load External Data
# ============================================================

print("\n📊 Loading external data...")

# D6: Global Gold (USD)
gold_usd = load_csv(os.path.join(EXTERNAL_DIR, 'D6_gold_usd.csv'))
if gold_usd is not None:
    gold_usd = gold_usd.rename(columns={'gold_usd_oz': 'gold_usd'})
    gold_usd = gold_usd[['date', 'gold_usd']].dropna()
    print(f"  D6 Gold USD: {len(gold_usd)} rows")

# D10: Policy Rates
policy = load_csv(os.path.join(EXTERNAL_DIR, 'D10_policy_rates_daily.csv'))
if policy is not None:
    policy = policy[['date', 'sdfr', 'slfr', 'opr', 'policy_ceiling']].copy()
    print(f"  D10 Policy Rates: {len(policy)} rows")

# D12: Reserves
reserves = load_csv(os.path.join(EXTERNAL_DIR, 'D12_reserves_compiled.csv'))
if reserves is not None:
    reserves = reserves[['date', 'gross_reserves_usd_m']].dropna()
    print(f"  D12 Reserves: {len(reserves)} rows")

# D13: Inflation
inflation = load_csv(os.path.join(EXTERNAL_DIR, 'D13_inflation_monthly_compiled.csv'))
if inflation is not None:
    inflation = inflation[['date', 'ncpi_yoy_pct']].dropna()
    print(f"  D13 Inflation: {len(inflation)} rows")

# D17: Tourism
tourism = load_csv(os.path.join(EXTERNAL_DIR, 'D17_tourism.csv'))
if tourism is not None:
    tourism = tourism[['date', 'tourism_earnings_usd_m']].dropna()
    print(f"  D17 Tourism: {len(tourism)} rows")

# D18: Remittances
remit = load_csv(os.path.join(EXTERNAL_DIR, 'D18_remittances.csv'))
if remit is not None:
    remit = remit[['date', 'remittances_usd_m']].dropna()
    print(f"  D18 Remittances: {len(remit)} rows")

# US Treasury (for EMBI spread calculation)
ust = load_csv(os.path.join(EXTERNAL_DIR, 'us_treasury_10y.csv'))
if ust is not None:
    ust = ust.rename(columns={'us_10y_yield_pct': 'us_10y_yield'})
    ust = ust[['date', 'us_10y_yield']].dropna()
    print(f"  US Treasury 10Y: {len(ust)} rows")

# ============================================================
# Create Daily Date Spine
# ============================================================

print("\n🔧 Creating daily date spine...")

date_range = pd.date_range(start=START_DATE, end=END_DATE, freq='D')
daily = pd.DataFrame({'date': date_range})
print(f"  Date range: {len(daily)} days")

# ============================================================
# Merge Daily Data
# ============================================================

print("\n🔧 Merging daily data...")

# Merge all daily datasets
daily_datasets = [
    (d1, 'D1'),
    (d2, 'D2'),
    (d3, 'D3'),
    (d4, 'D4'),
    (d5, 'D5'),
    (d6d7, 'D6/D7'),
    (d8, 'D8'),
    (d9, 'D9'),
    (d15, 'D15'),
    (gold_usd, 'Gold USD'),
    (policy, 'Policy'),
    (ust, 'UST'),
]

for df, name in daily_datasets:
    if df is not None:
        daily = daily.merge(df, on='date', how='left')
        print(f"  Merged {name}")

# ============================================================
# Merge Monthly Data (with forward-fill)
# ============================================================

print("\n🔧 Merging monthly data (forward-fill to daily)...")

monthly_datasets = [
    (d14, 'REER'),
    (reserves, 'Reserves'),
    (inflation, 'Inflation'),
    (tourism, 'Tourism'),
    (remit, 'Remittances'),
]

for df, name in monthly_datasets:
    if df is not None:
        daily = daily.merge(df, on='date', how='left')
        # Forward-fill monthly data
        for col in df.columns:
            if col != 'date' and col in daily.columns:
                daily[col] = daily[col].ffill()
        print(f"  Merged & forward-filled {name}")

# ============================================================
# Create Derived Features
# ============================================================

print("\n🔧 Creating derived features...")

# 1. FX Log Returns
if 'usd_lkr' in daily.columns:
    daily['r_fx'] = np.log(daily['usd_lkr'] / daily['usd_lkr'].shift(1))
    # Use min_periods to handle gaps (weekends, holidays)
    daily['vol_fx_20d'] = daily['r_fx'].rolling(20, min_periods=10).std()
    print("  Created: r_fx, vol_fx_20d")

# 2. Equity Log Returns
if 'aspi' in daily.columns:
    daily['r_eq'] = np.log(daily['aspi'] / daily['aspi'].shift(1))
    # Use min_periods to handle gaps (weekends, holidays)
    daily['vol_eq_20d'] = daily['r_eq'].rolling(20, min_periods=10).std()
    print("  Created: r_eq, vol_eq_20d")

# 3. Real Equity Returns (FX-adjusted)
if 'r_eq' in daily.columns and 'r_fx' in daily.columns:
    daily['r_eq_real'] = daily['r_eq'] - daily['r_fx']
    print("  Created: r_eq_real")

# 4. Gold Premium (Shadow FX Indicator)
if 'gold_lkr' in daily.columns and 'gold_usd' in daily.columns and 'usd_lkr' in daily.columns:
    # Convert local gold to per oz (assuming it's per gram, multiply by 31.1)
    # Note: CBSL gold price units need verification
    daily['implied_fx'] = daily['gold_lkr'] / daily['gold_usd']
    daily['gold_premium_pct'] = (daily['implied_fx'] / daily['usd_lkr'] - 1) * 100
    print("  Created: implied_fx, gold_premium_pct")

# 5. Reserve Metrics
if 'gross_reserves_usd_m' in daily.columns:
    # Reserve slope (3-month rolling regression) - use min_periods for monthly data
    def safe_slope(x):
        x_valid = x.dropna()
        if len(x_valid) >= 3:
            return np.polyfit(range(len(x_valid)), x_valid.values, 1)[0]
        return np.nan
    daily['reserve_slope_3m'] = daily['gross_reserves_usd_m'].rolling(90, min_periods=30).apply(safe_slope, raw=False)
    # Import cover (rough estimate using average monthly imports ~$1.5B)
    daily['import_cover_months'] = daily['gross_reserves_usd_m'] / 1500
    print("  Created: reserve_slope_3m, import_cover_months")

# 6. Interbank Stress Spread
if 'awcmr' in daily.columns and 'policy_ceiling' in daily.columns:
    daily['interbank_spread'] = daily['awcmr'] - daily['policy_ceiling']
    print("  Created: interbank_spread")

# 7. Real Policy Rate
if 'policy_ceiling' in daily.columns and 'ncpi_yoy_pct' in daily.columns:
    daily['real_policy_rate'] = daily['policy_ceiling'] - daily['ncpi_yoy_pct']
    print("  Created: real_policy_rate")

# 8. Yield Curve Slope (use available tenors)
slope_created = False
if 'tbond_yield' in daily.columns and 'tbill_primary' in daily.columns:
    daily['yield_curve_slope'] = daily['tbond_yield'] - daily['tbill_primary']
    slope_created = True
elif 'isb_yield' in daily.columns and 'tbill_primary' in daily.columns:
    daily['yield_curve_slope'] = daily['isb_yield'] - daily['tbill_primary']
    slope_created = True
elif 'isb_yield' in daily.columns and 'policy_ceiling' in daily.columns:
    daily['yield_curve_slope'] = daily['isb_yield'] - daily['policy_ceiling']
    slope_created = True
if slope_created:
    print("  Created: yield_curve_slope")
else:
    print("  ⚠ yield_curve_slope: insufficient data")

# 9. Turnover Ratio
if 'equity_turnover' in daily.columns and 'market_cap' in daily.columns:
    daily['turnover_ratio'] = daily['equity_turnover'] / daily['market_cap']
    print("  Created: turnover_ratio")

# 10. EMBI Spread (approximation)
if 'isb_yield' in daily.columns and 'us_10y_yield' in daily.columns:
    daily['embi_spread_approx'] = (daily['isb_yield'] - daily['us_10y_yield']) * 100  # in bps
    print("  Created: embi_spread_approx")

# ============================================================
# Filter to analysis period
# ============================================================

daily = daily[(daily['date'] >= START_DATE) & (daily['date'] <= END_DATE)]

# ============================================================
# Create Monthly Aggregation
# ============================================================

print("\n🔧 Creating monthly aggregation...")

# Set date as index for resampling
daily_indexed = daily.set_index('date')

# Define aggregation rules - only include columns that exist
agg_rules = {}

# Prices: end of month
for col in ['usd_lkr', 'aspi', 'sl20_index', 'gold_usd', 'gold_lkr', 'market_cap']:
    if col in daily_indexed.columns:
        agg_rules[col] = 'last'

# Rates: end of month
for col in ['awcmr', 'tbill_primary', 'tbill_secondary', 'tbond_yield', 'isb_yield', 'policy_ceiling', 'sdfr', 'slfr', 'us_10y_yield']:
    if col in daily_indexed.columns:
        agg_rules[col] = 'last'

# Turnover: sum for month
for col in ['equity_turnover']:
    if col in daily_indexed.columns:
        agg_rules[col] = 'sum'

# Volatility: average for month
for col in ['vol_fx_20d', 'vol_eq_20d']:
    if col in daily_indexed.columns:
        agg_rules[col] = 'mean'

# Macro: already monthly, take last
for col in ['reer_index', 'gross_reserves_usd_m', 'ncpi_yoy_pct', 'tourism_earnings_usd_m', 'remittances_usd_m']:
    if col in daily_indexed.columns:
        agg_rules[col] = 'last'

# Derived: take last
for col in ['gold_premium_pct', 'interbank_spread', 'real_policy_rate', 'yield_curve_slope', 'import_cover_months', 'embi_spread_approx', 'r_fx', 'r_eq', 'r_eq_real', 'turnover_ratio']:
    if col in daily_indexed.columns:
        agg_rules[col] = 'last'

monthly = daily_indexed.resample('ME').agg(agg_rules).reset_index()

# ============================================================
# Save Output
# ============================================================

print("\n💾 Saving merged datasets...")

# Save daily panel
daily_path = os.path.join(OUTPUT_DIR, 'slfsi_daily_panel.csv')
daily.to_csv(daily_path, index=False)
print(f"  ✓ Daily panel: {daily_path}")
print(f"    Rows: {len(daily)}, Columns: {len(daily.columns)}")

# Save monthly panel
monthly_path = os.path.join(OUTPUT_DIR, 'slfsi_monthly_panel.csv')
monthly.to_csv(monthly_path, index=False)
print(f"  ✓ Monthly panel: {monthly_path}")
print(f"    Rows: {len(monthly)}, Columns: {len(monthly.columns)}")

# ============================================================
# Data Quality Report
# ============================================================

print("\n" + "="*70)
print("DATA QUALITY REPORT")
print("="*70)

print("\n📊 Column Coverage (Daily Panel):")
print("-" * 50)

# Focus on crisis period
crisis = daily[(daily['date'] >= '2020-01-01') & (daily['date'] <= '2023-12-31')]
total_crisis_days = len(crisis)

for col in daily.columns:
    if col == 'date':
        continue
    valid = crisis[col].notna().sum()
    pct = valid / total_crisis_days * 100
    status = "✓" if pct > 50 else "⚠" if pct > 10 else "✗"
    print(f"  {status} {col}: {pct:.1f}% coverage ({valid}/{total_crisis_days} days)")

print("\n📊 Key Features for HMM:")
print("-" * 50)
hmm_features = [
    'r_fx', 'vol_fx_20d', 'r_eq_real', 'gold_premium_pct',
    'interbank_spread', 'real_policy_rate', 'import_cover_months',
    'embi_spread_approx', 'turnover_ratio'
]
for feat in hmm_features:
    if feat in daily.columns:
        valid = crisis[feat].notna().sum()
        pct = valid / total_crisis_days * 100
        print(f"  {feat}: {pct:.1f}% coverage")
    else:
        print(f"  {feat}: NOT CREATED")

print("\n" + "="*70)
print("MERGE COMPLETE!")
print("="*70)
print(f"\nOutput files:")
print(f"  • {daily_path}")
print(f"  • {monthly_path}")
print(f"\nReady for feature engineering and HMM fitting!")

