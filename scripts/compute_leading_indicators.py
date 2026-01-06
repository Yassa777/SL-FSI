#!/usr/bin/env python3
"""
Leading Indicators Computation
==============================
Computes forward-looking leading indicators for early warning analysis.

Indicators:
1. ISB Yield Spread (ISB yield - US 10Y Treasury)
2. Net Usable Reserves (Gross - PBOC Swap - ST Liabilities)
3. NDF Premium (when Bloomberg data available)
4. Reserve Adequacy Ratio (Reserves / Monthly Imports)
5. Real Effective Rate Gap

Run: python scripts/compute_leading_indicators.py
"""

import pandas as pd
import numpy as np
import os
from datetime import datetime
import warnings
warnings.filterwarnings('ignore')

# ============================================================
# Configuration
# ============================================================

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
MERGED_DIR = os.path.join(PROJECT_ROOT, 'data', 'merged')
EXTERNAL_DIR = os.path.join(PROJECT_ROOT, 'data', 'external')

print("=" * 70)
print("LEADING INDICATORS COMPUTATION")
print("=" * 70)

# ============================================================
# Load Data
# ============================================================

print("\nLoading merged panel data...")
daily = pd.read_csv(os.path.join(MERGED_DIR, 'slfsi_daily_panel.csv'), parse_dates=['date'])
monthly = pd.read_csv(os.path.join(MERGED_DIR, 'slfsi_monthly_panel.csv'), parse_dates=['date'])

print(f"  Daily panel: {len(daily)} rows ({daily['date'].min().strftime('%Y-%m')} to {daily['date'].max().strftime('%Y-%m')})")
print(f"  Monthly panel: {len(monthly)} rows")

# ============================================================
# Indicator 1: ISB Yield Spread
# ============================================================

print("\n" + "-" * 50)
print("Indicator 1: ISB YIELD SPREAD")
print("-" * 50)

if 'isb_yield' in monthly.columns and 'us_10y_yield' in monthly.columns:
    # Compute spread in basis points
    monthly['isb_spread_bps'] = (monthly['isb_yield'] - monthly['us_10y_yield']) * 100
    
    valid = monthly['isb_spread_bps'].notna().sum()
    print(f"  Valid observations: {valid}")
    
    if valid > 0:
        print(f"  Mean spread: {monthly['isb_spread_bps'].mean():.0f} bps")
        print(f"  Max spread: {monthly['isb_spread_bps'].max():.0f} bps")
        
        # Identify distressed periods (spread > 1000 bps = 10%)
        distressed = monthly[monthly['isb_spread_bps'] > 1000][['date', 'isb_spread_bps']]
        if len(distressed) > 0:
            print(f"\n  Distressed periods (spread > 1000 bps):")
            for _, row in distressed.head(5).iterrows():
                print(f"    {row['date'].strftime('%Y-%m')}: {row['isb_spread_bps']:.0f} bps")
else:
    print("  Skipped: isb_yield or us_10y_yield not available")

# ============================================================
# Indicator 2: Net Usable Reserves
# ============================================================

print("\n" + "-" * 50)
print("Indicator 2: NET USABLE RESERVES")
print("-" * 50)

if 'gross_reserves_usd_m' in monthly.columns:
    # PBOC swap facility: $1.5B effective from ~Mar 2021
    # This was not truly "usable" as it was a currency swap, not liquid reserves
    PBOC_SWAP_USD_M = 1500
    PBOC_SWAP_START = pd.Timestamp('2021-03-01')
    
    # Compute net usable reserves
    monthly['net_reserves_usd_m'] = monthly['gross_reserves_usd_m'].copy()
    mask = monthly['date'] >= PBOC_SWAP_START
    monthly.loc[mask, 'net_reserves_usd_m'] = (
        monthly.loc[mask, 'gross_reserves_usd_m'] - PBOC_SWAP_USD_M
    )
    
    # Compute net import cover (using $1.5B monthly imports)
    MONTHLY_IMPORTS_USD_M = 1500
    monthly['net_import_cover'] = monthly['net_reserves_usd_m'] / MONTHLY_IMPORTS_USD_M
    
    # Show comparison
    print("\n  Gross vs Net Reserves at Key Dates:")
    key_dates = ['2020-12-01', '2021-06-01', '2021-12-01', '2022-03-01', '2022-06-01']
    print(f"  {'Date':<12} {'Gross ($M)':<12} {'Net ($M)':<12} {'Net Cover (mo)':<15}")
    print("  " + "-" * 50)
    
    for date_str in key_dates:
        date = pd.Timestamp(date_str)
        row = monthly[monthly['date'] == date]
        if len(row) > 0:
            r = row.iloc[0]
            gross = r['gross_reserves_usd_m']
            net = r['net_reserves_usd_m']
            cover = r['net_import_cover']
            print(f"  {date.strftime('%Y-%m'):<12} {gross:>10,.0f}  {net:>10,.0f}  {cover:>12.1f}")
    
    # When did net reserves first go negative or below 2 months?
    critical = monthly[(monthly['net_import_cover'] < 2) & (monthly['date'] >= '2021-01-01')]
    if len(critical) > 0:
        first_critical = critical.iloc[0]
        print(f"\n  First month with net import cover < 2 months:")
        print(f"    {first_critical['date'].strftime('%Y-%m')}: {first_critical['net_import_cover']:.1f} months")
else:
    print("  Skipped: gross_reserves_usd_m not available")

# ============================================================
# Indicator 3: NDF Premium (Placeholder for Bloomberg data)
# ============================================================

print("\n" + "-" * 50)
print("Indicator 3: NDF PREMIUM (Bloomberg data required)")
print("-" * 50)

ndf_path = os.path.join(EXTERNAL_DIR, 'ndf_rates.csv')
if os.path.exists(ndf_path):
    ndf_df = pd.read_csv(ndf_path, parse_dates=['date'])
    print(f"  Loaded NDF rates: {len(ndf_df)} rows")
    
    # Compute NDF premium
    if 'ndf_1m' in ndf_df.columns and 'usd_lkr' in monthly.columns:
        merged = monthly.merge(ndf_df[['date', 'ndf_1m']], on='date', how='left')
        merged['ndf_premium_pct'] = (merged['ndf_1m'] / merged['usd_lkr'] - 1) * 100
        
        valid = merged['ndf_premium_pct'].notna().sum()
        print(f"  Valid NDF premium observations: {valid}")
        
        monthly = merged
else:
    print("  NDF data not available. To add:")
    print("    1. Export NDF rates from Bloomberg (LKR NDF Curncy)")
    print("    2. Save as data/external/ndf_rates.csv with columns: date, ndf_1m, ndf_3m, ndf_6m, ndf_12m")
    print("    3. Re-run this script")

# ============================================================
# Indicator 4: Real Policy Rate Gap
# ============================================================

print("\n" + "-" * 50)
print("Indicator 4: REAL POLICY RATE GAP")
print("-" * 50)

if 'real_policy_rate' in monthly.columns:
    # Real rate = Nominal rate - Inflation
    # Gap = How far below equilibrium (assume equilibrium = 2%)
    EQUILIBRIUM_REAL_RATE = 2.0
    
    monthly['real_rate_gap'] = monthly['real_policy_rate'] - EQUILIBRIUM_REAL_RATE
    
    # Identify financial repression (deeply negative real rates)
    repression = monthly[(monthly['real_policy_rate'] < -10) & (monthly['date'] >= '2021-01-01')]
    if len(repression) > 0:
        print(f"  Periods of financial repression (real rate < -10%):")
        for _, row in repression.head(5).iterrows():
            print(f"    {row['date'].strftime('%Y-%m')}: {row['real_policy_rate']:.1f}%")
    
    # Show evolution
    print("\n  Real Policy Rate at Key Dates:")
    key_dates = ['2020-01-01', '2021-07-01', '2022-04-01', '2022-09-01', '2023-06-01', '2024-01-01']
    for date_str in key_dates:
        date = pd.Timestamp(date_str)
        row = monthly[monthly['date'] == date]
        if len(row) > 0:
            r = row.iloc[0]
            print(f"    {date.strftime('%Y-%m')}: {r['real_policy_rate']:.1f}%")
else:
    print("  Skipped: real_policy_rate not available")

# ============================================================
# Indicator 5: Composite Early Warning Score
# ============================================================

print("\n" + "-" * 50)
print("Indicator 5: COMPOSITE EARLY WARNING SCORE")
print("-" * 50)

# Create composite score based on multiple indicators
# Each indicator is standardized and combined

components = []

if 'net_import_cover' in monthly.columns:
    # Invert so lower cover = higher stress
    monthly['z_reserve_stress'] = -(monthly['net_import_cover'] - monthly['net_import_cover'].mean()) / monthly['net_import_cover'].std()
    components.append('z_reserve_stress')

if 'real_policy_rate' in monthly.columns:
    # Invert so lower real rate = higher stress  
    monthly['z_real_rate_stress'] = -(monthly['real_policy_rate'] - monthly['real_policy_rate'].mean()) / monthly['real_policy_rate'].std()
    components.append('z_real_rate_stress')

if 'isb_spread_bps' in monthly.columns:
    # Higher spread = higher stress
    monthly['z_isb_stress'] = (monthly['isb_spread_bps'] - monthly['isb_spread_bps'].mean()) / monthly['isb_spread_bps'].std()
    components.append('z_isb_stress')

if len(components) >= 2:
    # Compute composite score (average of available z-scores)
    monthly['early_warning_score'] = monthly[components].mean(axis=1)
    
    valid = monthly['early_warning_score'].notna().sum()
    print(f"  Components used: {components}")
    print(f"  Valid observations: {valid}")
    
    # Identify high-stress periods (score > 1.5)
    high_stress = monthly[(monthly['early_warning_score'] > 1.5) & (monthly['date'] >= '2020-01-01')]
    if len(high_stress) > 0:
        print(f"\n  High stress periods (score > 1.5):")
        for _, row in high_stress.head(10).iterrows():
            print(f"    {row['date'].strftime('%Y-%m')}: {row['early_warning_score']:.2f}")
else:
    print("  Insufficient components for composite score")

# ============================================================
# Save Enhanced Monthly Data
# ============================================================

print("\n" + "=" * 70)
print("SAVING RESULTS")
print("=" * 70)

# Save enhanced monthly panel
output_path = os.path.join(MERGED_DIR, 'monthly_with_indicators.csv')
monthly.to_csv(output_path, index=False)
print(f"  Saved: {output_path}")
print(f"  Columns: {len(monthly.columns)}")

# Create summary of new indicators
new_cols = ['isb_spread_bps', 'net_reserves_usd_m', 'net_import_cover', 'real_rate_gap', 
            'early_warning_score', 'z_reserve_stress', 'z_real_rate_stress', 'z_isb_stress']
existing_new = [c for c in new_cols if c in monthly.columns]
print(f"\n  New indicator columns: {existing_new}")

# ============================================================
# Summary Report
# ============================================================

print("\n" + "=" * 70)
print("EARLY WARNING TIMELINE")
print("=" * 70)

# When did each indicator first signal stress?
default_date = pd.Timestamp('2022-04-12')

signals = []

# Net reserves < 2 months
if 'net_import_cover' in monthly.columns:
    first_low_reserve = monthly[(monthly['net_import_cover'] < 2) & (monthly['date'] < default_date)]
    if len(first_low_reserve) > 0:
        first_date = first_low_reserve.iloc[0]['date']
        lead_days = (default_date - first_date).days
        signals.append(('Net reserves < 2 months', first_date, lead_days))

# Real rate < -10%
if 'real_policy_rate' in monthly.columns:
    first_repression = monthly[(monthly['real_policy_rate'] < -10) & (monthly['date'] < default_date)]
    if len(first_repression) > 0:
        first_date = first_repression.iloc[0]['date']
        lead_days = (default_date - first_date).days
        signals.append(('Real rate < -10%', first_date, lead_days))

# ISB spread > 1000 bps
if 'isb_spread_bps' in monthly.columns:
    first_distress = monthly[(monthly['isb_spread_bps'] > 1000) & (monthly['date'] < default_date)]
    if len(first_distress) > 0:
        first_date = first_distress.iloc[0]['date']
        lead_days = (default_date - first_date).days
        signals.append(('ISB spread > 1000 bps', first_date, lead_days))

# Early warning score > 1.5
if 'early_warning_score' in monthly.columns:
    first_ews = monthly[(monthly['early_warning_score'] > 1.5) & (monthly['date'] < default_date)]
    if len(first_ews) > 0:
        first_date = first_ews.iloc[0]['date']
        lead_days = (default_date - first_date).days
        signals.append(('Composite EWS > 1.5', first_date, lead_days))

print(f"\nDefault Date: {default_date.strftime('%Y-%m-%d')}")
print(f"\n{'Signal':<25} {'First Date':<12} {'Lead Time':<15}")
print("-" * 55)

for signal_name, first_date, lead_days in sorted(signals, key=lambda x: -x[2]):
    lead_months = lead_days // 30
    print(f"{signal_name:<25} {first_date.strftime('%Y-%m'):<12} {lead_days} days ({lead_months} mo)")

print("\n" + "=" * 70)
print("LEADING INDICATORS COMPUTATION COMPLETE")
print("=" * 70)

