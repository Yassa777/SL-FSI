#!/usr/bin/env python3
"""
Download external data for SL-FSI project

Run: python scripts/download_external_data.py

Dependencies: pip install yfinance pandas
"""

import os
import sys
import pandas as pd
from datetime import datetime

# Add project root to path
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
os.chdir(project_root)

# Create output directory
os.makedirs('data/external', exist_ok=True)

print("="*60)
print("SL-FSI External Data Downloader")
print("="*60)

# ============================================================
# D6: Global Gold Price (USD)
# ============================================================
print("\n[D6] Downloading Gold prices (GC=F)...")
try:
    import yfinance as yf
    gold = yf.download('GC=F', start='2010-01-01', end='2025-12-31', progress=False)
    gold = gold[['Close']].rename(columns={'Close': 'gold_usd_oz'})
    gold.index.name = 'date'
    gold = gold.reset_index()
    gold['date'] = pd.to_datetime(gold['date']).dt.date
    gold.to_csv('data/external/D6_gold_usd.csv', index=False)
    print(f"  ✓ Saved {len(gold)} rows")
    print(f"  Date range: {gold['date'].min()} to {gold['date'].max()}")
    print(f"  Sample: ${gold['gold_usd_oz'].iloc[-1]:.2f}/oz (latest)")
except ImportError:
    print("  ✗ yfinance not installed. Run: pip install yfinance")
except Exception as e:
    print(f"  ✗ Error: {e}")

# ============================================================
# US Treasury 10Y Yield (for EMBI spread calculation)
# ============================================================
print("\n[D16-helper] Downloading US Treasury 10Y yield (^TNX)...")
try:
    import yfinance as yf
    ust = yf.download('^TNX', start='2010-01-01', end='2025-12-31', progress=False)
    ust = ust[['Close']].rename(columns={'Close': 'us_10y_yield_pct'})
    ust.index.name = 'date'
    ust = ust.reset_index()
    ust['date'] = pd.to_datetime(ust['date']).dt.date
    ust.to_csv('data/external/us_treasury_10y.csv', index=False)
    print(f"  ✓ Saved {len(ust)} rows")
    print(f"  Date range: {ust['date'].min()} to {ust['date'].max()}")
    print(f"  Sample: {ust['us_10y_yield_pct'].iloc[-1]:.2f}% (latest)")
except Exception as e:
    print(f"  ✗ Error: {e}")

# ============================================================
# D10: Policy Rates (Manual compilation)
# ============================================================
print("\n[D10] Creating Policy Rates dataset...")

policy_rates_data = [
    # (date, sdfr, slfr, opr, notes)
    # Pre-crisis period
    ('2019-01-01', 7.00, 8.00, None, 'Starting point'),
    ('2019-05-31', 7.00, 8.00, None, 'MPC'),
    ('2019-08-22', 7.00, 8.00, None, 'MPC'),
    
    # COVID response - aggressive cuts
    ('2020-01-30', 6.50, 7.50, None, 'MPC - COVID concerns'),
    ('2020-03-16', 6.25, 7.25, None, 'Emergency - COVID'),
    ('2020-04-03', 6.00, 7.00, None, 'Emergency'),
    ('2020-04-09', 5.50, 6.50, None, 'Emergency'),
    ('2020-05-06', 5.50, 6.50, None, 'MPC'),
    ('2020-07-08', 4.50, 5.50, None, 'MPC - Deep cut'),
    
    # Rates held low through 2021
    ('2021-01-27', 4.50, 5.50, None, 'MPC - Hold'),
    ('2021-08-19', 4.50, 5.50, None, 'MPC - Still holding despite pressure'),
    
    # Crisis response - aggressive hikes
    ('2022-01-20', 5.00, 6.00, None, 'MPC - First hike'),
    ('2022-03-04', 5.50, 6.50, None, 'Emergency - FX pressure'),
    ('2022-04-08', 13.50, 14.50, None, 'EMERGENCY - Massive 700bps hike'),
    ('2022-07-08', 14.50, 15.50, None, 'MPC - Peak rates'),
    
    # Post-IMF normalization
    ('2023-06-01', 11.00, 12.00, None, 'MPC - Start cutting'),
    ('2023-07-13', 10.00, 11.00, None, 'MPC'),
    ('2023-10-04', 9.00, 10.00, None, 'MPC'),
    ('2024-03-26', 8.50, 9.50, None, 'MPC'),
    ('2024-06-04', 8.25, 9.25, None, 'MPC'),
    
    # New OPR framework
    ('2024-09-04', None, None, 8.00, 'NEW OPR FRAMEWORK'),
    ('2024-11-26', None, None, 7.75, 'MPC'),
]

policy_rates = pd.DataFrame(policy_rates_data, 
                           columns=['date', 'sdfr', 'slfr', 'opr', 'notes'])
policy_rates['date'] = pd.to_datetime(policy_rates['date']).dt.date

# Create a step-function expanded version (daily)
print("  Expanding to daily frequency...")
date_range = pd.date_range('2019-01-01', '2025-12-31', freq='D')
daily_rates = pd.DataFrame({'date': date_range})
daily_rates['date'] = daily_rates['date'].dt.date

# Forward-fill rates
policy_rates_sorted = policy_rates.sort_values('date')
for idx, row in policy_rates_sorted.iterrows():
    mask = daily_rates['date'] >= row['date']
    if row['sdfr'] is not None:
        daily_rates.loc[mask, 'sdfr'] = row['sdfr']
        daily_rates.loc[mask, 'slfr'] = row['slfr']
    if row['opr'] is not None:
        daily_rates.loc[mask, 'opr'] = row['opr']

# Calculate policy ceiling (for interbank stress spread)
daily_rates['policy_ceiling'] = daily_rates['slfr'].fillna(daily_rates['opr'])

daily_rates.to_csv('data/external/D10_policy_rates_daily.csv', index=False)
policy_rates.to_csv('data/external/D10_policy_rates_changes.csv', index=False)
print(f"  ✓ Saved {len(policy_rates)} rate change events")
print(f"  ✓ Saved {len(daily_rates)} daily forward-filled rates")

# ============================================================
# D12, D13, D17, D18: Create templates for manual data
# ============================================================
print("\n[Templates] Creating templates for manual data entry...")

# D12: Reserves template
reserves_template = pd.DataFrame({
    'date': pd.date_range('2015-01', periods=120, freq='ME').strftime('%Y-%m'),
    'gross_reserves_usd_m': [None] * 120,
    'import_cover_months': [None] * 120,
    'notes': [''] * 120
})
reserves_template.to_csv('data/external/D12_reserves_TEMPLATE.csv', index=False)
print("  ✓ Created D12_reserves_TEMPLATE.csv")

# D13: Inflation template
inflation_template = pd.DataFrame({
    'date': pd.date_range('2015-01', periods=120, freq='ME').strftime('%Y-%m'),
    'ncpi_index': [None] * 120,
    'ncpi_yoy_pct': [None] * 120,
    'core_inflation_pct': [None] * 120
})
inflation_template.to_csv('data/external/D13_inflation_TEMPLATE.csv', index=False)
print("  ✓ Created D13_inflation_TEMPLATE.csv")

# D17: Tourism template
tourism_template = pd.DataFrame({
    'date': pd.date_range('2015-01', periods=120, freq='ME').strftime('%Y-%m'),
    'arrivals': [None] * 120,
    'earnings_usd_m': [None] * 120
})
tourism_template.to_csv('data/external/D17_tourism_TEMPLATE.csv', index=False)
print("  ✓ Created D17_tourism_TEMPLATE.csv")

# D18: Remittances template
remit_template = pd.DataFrame({
    'date': pd.date_range('2015-01', periods=120, freq='ME').strftime('%Y-%m'),
    'remittances_usd_m': [None] * 120
})
remit_template.to_csv('data/external/D18_remittances_TEMPLATE.csv', index=False)
print("  ✓ Created D18_remittances_TEMPLATE.csv")

# ============================================================
# Summary
# ============================================================
print("\n" + "="*60)
print("DOWNLOAD SUMMARY")
print("="*60)

print("\n✅ COMPLETED (automated):")
print("   • D6_gold_usd.csv - Global gold prices")
print("   • us_treasury_10y.csv - For EMBI spread calculation")
print("   • D10_policy_rates_daily.csv - Policy rates (step-function)")
print("   • D10_policy_rates_changes.csv - Policy rate change events")

print("\n📋 TEMPLATES CREATED (fill manually):")
print("   • D12_reserves_TEMPLATE.csv")
print("   • D13_inflation_TEMPLATE.csv")
print("   • D17_tourism_TEMPLATE.csv")
print("   • D18_remittances_TEMPLATE.csv")

print("\n📥 MANUAL DOWNLOAD INSTRUCTIONS:")
print("""
   D12 (Reserves):
   → https://www.cbsl.gov.lk/cbsl_custom/data/library/index.php
   → Category: External Sector → International Reserves
   
   D13 (Inflation):
   → http://www.statistics.gov.lk/InflationAndPrices
   → Download monthly NCPI bulletins
   
   D17 (Tourism):
   → https://www.sltda.gov.lk/en/statistics
   → Monthly arrival statistics
   
   D18 (Remittances):
   → CBSL Data Library → External Sector → Balance of Payments
   → Workers' Remittances
""")

print("\n" + "="*60)

