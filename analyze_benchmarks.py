#!/usr/bin/env python3
"""
Analyze reserve adequacy benchmarks and threshold breaches.
"""

import pandas as pd
import numpy as np
from pathlib import Path

# Load all data
reserves = pd.read_csv('data/external/reserve_assets_monthly_cbsl.csv', parse_dates=['date'])
imports_df = pd.read_csv('data/external/monthly_imports_usd.csv', parse_dates=['date'])
exports_df = pd.read_csv('data/external/monthly_exports_usd.csv', parse_dates=['date'])
ext_debt = pd.read_csv('data/external/external_debt_usd_quarterly.csv', parse_dates=['date'])
iip = pd.read_csv('data/external/iip_quarterly_2025.csv', parse_dates=['date'])
m2 = pd.read_csv('data/external/monetary_aggregates_monthly.csv', parse_dates=['date'])
fx = pd.read_csv('data/merged/slfsi_monthly_panel.csv', parse_dates=['date'])[['date', 'usd_lkr']]

# Calculate portfolio liabilities
iip['portfolio_liabilities'] = iip['portfolio_equity'].fillna(0) + iip['portfolio_debt'].fillna(0)

# ===================
# 1. IMPORT COVER
# ===================
print("="*70)
print("1. IMPORT COVER ANALYSIS")
print("="*70)

ic = reserves.merge(imports_df, on='date', how='left')
ic['imports_usd_m'] = ic['imports_usd_m'].ffill()
ic['import_cover'] = ic['gross_reserves_usd_m'] / ic['imports_usd_m']

# Net usable reserves (exclude PBOC swap from Mar 2021)
ic['net_reserves'] = ic['gross_reserves_usd_m'].copy()
ic.loc[ic['date'] >= '2021-03-01', 'net_reserves'] -= 1500
ic['net_import_cover'] = ic['net_reserves'] / ic['imports_usd_m']

print("\nImport Cover Thresholds:")
print("  - IMF Minimum: 3 months")
print("  - Comfortable: 6 months")
print("  - Critical: 1 month")

# Find first breach of each threshold
thresholds = [(6, 'comfortable'), (3, 'minimum'), (2, 'warning'), (1, 'critical')]
breaches = {}

for thresh, label in thresholds:
    breach_data = ic[ic['import_cover'] < thresh]
    if len(breach_data) > 0:
        first = breach_data.iloc[0]
        breaches[f'ic_{thresh}m'] = {
            'date': first['date'],
            'value': first['import_cover'],
            'reserves': first['gross_reserves_usd_m']
        }
        print(f"\n  First breach < {thresh} months ({label}):")
        print(f"    Date: {first['date'].strftime('%Y-%m')}")
        print(f"    Import Cover: {first['import_cover']:.2f} months")
        print(f"    Reserves: ${first['gross_reserves_usd_m']:,.0f}M")

# ===================
# 2. GREENSPAN-GUIDOTTI
# ===================
print("\n" + "="*70)
print("2. GREENSPAN-GUIDOTTI ANALYSIS")
print("="*70)

reserves_q = reserves.set_index('date').resample('Q').last().reset_index()
gg = reserves_q.merge(ext_debt[['date', 'govt_short_term_usd_m']], on='date', how='inner')
gg['gg_ratio'] = gg['gross_reserves_usd_m'] / gg['govt_short_term_usd_m']

print("\nGreenspan-Guidotti Ratio = Reserves / Short-term External Debt")
print("Threshold: >= 1.0 (reserves should fully cover short-term debt)")

# Minimum ratio
min_gg = gg.loc[gg['gg_ratio'].idxmin()]
print(f"\nMinimum GG Ratio:")
print(f"  Date: {min_gg['date'].strftime('%Y-Q%q')}")
print(f"  Ratio: {min_gg['gg_ratio']:.2f}")
print(f"  Reserves: ${min_gg['gross_reserves_usd_m']:,.0f}M")
print(f"  Short-term Debt: ${min_gg['govt_short_term_usd_m']:,.0f}M")

breaches_gg = gg[gg['gg_ratio'] < 1.0]
print(f"\nGG Breaches (< 1.0): {len(breaches_gg)}")

# Near breaches
near_gg = gg[(gg['gg_ratio'] >= 1.0) & (gg['gg_ratio'] < 1.5)]
print(f"Near breaches (1.0-1.5): {len(near_gg)}")
if len(near_gg) > 0:
    for _, row in near_gg.iterrows():
        print(f"  {row['date'].strftime('%Y-Q%q')}: {row['gg_ratio']:.2f}")

# ===================
# 3. IMF ARA
# ===================
print("\n" + "="*70)
print("3. IMF ARA ANALYSIS")
print("="*70)

# Quarterly M2 with FX
m2_q = m2.set_index('date').resample('Q').last().reset_index()
fx_q = fx.set_index('date').resample('Q').last().reset_index()
m2_q = m2_q.merge(fx_q, on='date', how='left')
m2_q['m2_usd_m'] = m2_q['broad_money_m2_lkr_m'] / m2_q['usd_lkr']

# Quarterly exports (annualized)
exports_q = exports_df.set_index('date').resample('Q').sum().reset_index()
exports_q['annual_exports'] = exports_q['exports_usd_m'] * 4

# Build ARA
ara = reserves_q[['date', 'gross_reserves_usd_m']].copy()
ara = ara.merge(m2_q[['date', 'm2_usd_m']], on='date', how='left')
ara = ara.merge(ext_debt[['date', 'govt_short_term_usd_m']], on='date', how='left')
ara = ara.merge(iip[['date', 'portfolio_liabilities']], on='date', how='left')
ara = ara.merge(exports_q[['date', 'annual_exports']], on='date', how='left')

ara['ara_exports'] = 0.05 * ara['annual_exports'].fillna(0)
ara['ara_m2'] = 0.05 * ara['m2_usd_m'].fillna(0)
ara['ara_debt'] = 0.30 * ara['govt_short_term_usd_m'].fillna(0)
ara['ara_portfolio'] = 0.15 * ara['portfolio_liabilities'].fillna(0)
ara['ara_total'] = ara['ara_exports'] + ara['ara_m2'] + ara['ara_debt'] + ara['ara_portfolio']
ara['ara_ratio'] = ara['gross_reserves_usd_m'] / ara['ara_total']
ara['ara_pct'] = ara['ara_ratio'] * 100

print("\nIMF ARA Formula:")
print("  ARA = 5% x Exports + 5% x M2 + 30% x Short-term Debt + 15% x Portfolio Liabilities")
print("  Threshold: >= 100%")

ara_valid = ara.dropna(subset=['ara_total'])
ara_breaches = ara_valid[ara_valid['ara_ratio'] < 1.0]
print(f"\nARA Breaches (< 100%): {len(ara_breaches)} quarters")

if len(ara_breaches) > 0:
    first_ara = ara_breaches.iloc[0]
    last_ara = ara_breaches.iloc[-1]
    print(f"\n  First breach: {first_ara['date'].strftime('%Y-Q%q')} ({first_ara['ara_pct']:.1f}%)")
    print(f"  Last breach: {last_ara['date'].strftime('%Y-Q%q')} ({last_ara['ara_pct']:.1f}%)")
    print(f"  Minimum: {ara_breaches['ara_pct'].min():.1f}%")

# ===================
# 4. CRISIS TIMELINE
# ===================
print("\n" + "="*70)
print("4. CRISIS TIMELINE")
print("="*70)

default_date = pd.Timestamp('2022-04-12')

events = [
    ('2019-04-21', 'Easter bombings'),
    ('2020-03-01', 'COVID-19 pandemic begins'),
    ('2021-03-01', 'PBOC swap activated'),
    ('2021-07-01', 'Food emergency declared'),
    ('2021-09-01', 'Economic emergency declared'),
    ('2022-04-12', 'Sovereign default announced'),
    ('2022-07-05', 'Wickremesinghe becomes president'),
    ('2023-03-20', 'IMF EFF approved'),
]

print("\nKey Events with Reserve Status:")
for date_str, event in events:
    d = pd.Timestamp(date_str)
    ic_at = ic[ic['date'] <= d]
    if len(ic_at) > 0:
        row = ic_at.iloc[-1]
        print(f"  {date_str}: {event}")
        print(f"             Reserves: ${row['gross_reserves_usd_m']:,.0f}M | Import Cover: {row['import_cover']:.2f} mo")

# ===================
# 5. EARLY WARNING LEAD TIME
# ===================
print("\n" + "="*70)
print("5. EARLY WARNING LEAD TIME")
print("="*70)

print(f"\nDefault Date: {default_date.strftime('%Y-%m-%d')}")
print("\nLead time for threshold breaches:")

# Import cover breaches
for thresh in [6, 3, 2, 1]:
    breach = ic[ic['import_cover'] < thresh]
    if len(breach) > 0:
        first = breach.iloc[0]
        lead_days = (default_date - first['date']).days
        print(f"  Import Cover < {thresh} months: {first['date'].strftime('%Y-%m')} ({lead_days} days / {lead_days/30:.0f} months before default)")

# ARA breach
if len(ara_breaches) > 0:
    first_ara_breach = ara_breaches.iloc[0]
    lead_days = (default_date - first_ara_breach['date']).days
    print(f"  ARA < 100%: {first_ara_breach['date'].strftime('%Y-Q%q')} ({lead_days} days / {lead_days/30:.0f} months before default)")

# ===================
# 6. HISTORICAL CRISES BACKTEST
# ===================
print("\n" + "="*70)
print("6. HISTORICAL CRISES BACKTEST")
print("="*70)

historical_crises = [
    ('2008-2009', 'Global Financial Crisis', '2008-01-01', '2009-12-31'),
    ('2011-2012', 'BoP Crisis / IMF Program', '2011-01-01', '2012-12-31'),
    ('2018', 'Currency Depreciation', '2018-01-01', '2018-12-31'),
]

for name, desc, start, end in historical_crises:
    start_d = pd.Timestamp(start)
    end_d = pd.Timestamp(end)
    
    # Get import cover for period
    period_ic = ic[(ic['date'] >= start_d) & (ic['date'] <= end_d)]
    
    if len(period_ic) > 0:
        min_ic = period_ic['import_cover'].min()
        min_date = period_ic.loc[period_ic['import_cover'].idxmin(), 'date']
        print(f"\n{name}: {desc}")
        print(f"  Minimum Import Cover: {min_ic:.2f} months ({min_date.strftime('%Y-%m')})")
        print(f"  Breach < 3 months: {'Yes' if min_ic < 3 else 'No'}")
        
        # Check ARA for period
        period_ara = ara_valid[(ara_valid['date'] >= start_d) & (ara_valid['date'] <= end_d)]
        if len(period_ara) > 0:
            min_ara = period_ara['ara_pct'].min()
            print(f"  Minimum ARA: {min_ara:.1f}%")
    else:
        print(f"\n{name}: {desc}")
        print(f"  No data available for this period")

# ===================
# 7. SUMMARY
# ===================
print("\n" + "="*70)
print("7. SUMMARY - PREDICTIVE POWER")
print("="*70)

print("\nBenchmark Performance for 2022 Default Prediction:")
print("-" * 50)
print("| Benchmark              | First Signal | Lead Time |")
print("-" * 50)

# IC < 3 months
if 'ic_3m' in breaches:
    lead = (default_date - breaches['ic_3m']['date']).days
    print(f"| Import Cover < 3mo     | {breaches['ic_3m']['date'].strftime('%Y-%m')}    | {lead//30} months  |")

# IC < 2 months
if 'ic_2m' in breaches:
    lead = (default_date - breaches['ic_2m']['date']).days
    print(f"| Import Cover < 2mo     | {breaches['ic_2m']['date'].strftime('%Y-%m')}    | {lead//30} months  |")

# IC < 1 month
if 'ic_1m' in breaches:
    lead = (default_date - breaches['ic_1m']['date']).days
    print(f"| Import Cover < 1mo     | {breaches['ic_1m']['date'].strftime('%Y-%m')}    | {lead//30} months  |")

# ARA breach
if len(ara_breaches) > 0:
    first_ara = ara_breaches.iloc[0]
    lead = (default_date - first_ara['date']).days
    print(f"| IMF ARA < 100%         | {first_ara['date'].strftime('%Y-Q%q')}   | {lead//30} months  |")

# GG near-breach
if len(near_gg) > 0:
    first_near = near_gg.iloc[0]
    lead = (default_date - first_near['date']).days
    print(f"| GG Ratio < 1.5         | {first_near['date'].strftime('%Y-Q%q')}   | {lead//30} months  |")

print("-" * 50)

print("\n✓ Analysis complete")
