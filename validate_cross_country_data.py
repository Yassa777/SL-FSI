#!/usr/bin/env python3
"""
CRITICAL VALIDATION: Compare Our Estimates vs Actual Data
==========================================================
This script honestly assesses how accurate our interpolated data is.

Data sources:
- World Bank API (annual data - authoritative)
- FRED (inflation - annual)
- Our interpolated estimates (monthly)

Run: python validate_cross_country_data.py
"""

import pandas as pd
import numpy as np

print("=" * 70)
print("CRITICAL DATA VALIDATION")
print("Comparing our estimates to actual World Bank data")
print("=" * 70)

# ============================================================
# ACTUAL DATA (World Bank API - just fetched)
# ============================================================

# Pakistan - ACTUAL from World Bank
pk_actual = pd.DataFrame({
    'year': [2020, 2021, 2022, 2023, 2024],
    'reserves_usd_m_actual': [18522, 22812, 9927, 13730, 18408],  # World Bank
    'inflation_actual': [9.74, 9.50, 19.87, 30.77, 12.63]  # World Bank/FRED
})

# Ghana - ACTUAL from World Bank
gh_actual = pd.DataFrame({
    'year': [2020, 2021, 2022, 2023, 2024],
    'reserves_usd_m_actual': [7884, 9917, 5205, 3624, None],  # World Bank (2024 missing)
    'inflation_actual': [9.89, 9.97, 31.26, 38.11, 22.85]  # FRED
})

# ============================================================
# OUR ESTIMATES (from interpolated data)
# ============================================================

pk_est = pd.read_csv('data/cross_country/pakistan_monthly_enhanced.csv', parse_dates=['date'])
gh_est = pd.read_csv('data/cross_country/ghana_monthly_enhanced.csv', parse_dates=['date'])

# Get annual averages from our monthly estimates
pk_est['year'] = pk_est['date'].dt.year
pk_yearly = pk_est.groupby('year').agg({
    'reserves_usd_m': 'mean',
    'inflation_yoy': 'mean'
}).reset_index()
pk_yearly.columns = ['year', 'reserves_usd_m_est', 'inflation_est']

gh_est['year'] = gh_est['date'].dt.year
gh_yearly = gh_est.groupby('year').agg({
    'reserves_usd_m': 'mean',
    'inflation_yoy': 'mean'
}).reset_index()
gh_yearly.columns = ['year', 'reserves_usd_m_est', 'inflation_est']

# ============================================================
# COMPARISON: Pakistan
# ============================================================

print("\n" + "=" * 70)
print("PAKISTAN: ACTUAL vs OUR ESTIMATES")
print("=" * 70)

pk_compare = pk_actual.merge(pk_yearly, on='year')
pk_compare['reserves_error_pct'] = ((pk_compare['reserves_usd_m_est'] - pk_compare['reserves_usd_m_actual'])
                                     / pk_compare['reserves_usd_m_actual'] * 100)
pk_compare['inflation_error_pct'] = ((pk_compare['inflation_est'] - pk_compare['inflation_actual'])
                                      / pk_compare['inflation_actual'] * 100)

print("\n                  RESERVES (USD millions)")
print("-" * 70)
print(f"{'Year':<6} {'Actual':<12} {'Our Est':<12} {'Error %':<10}")
print("-" * 70)
for _, row in pk_compare.iterrows():
    print(f"{row['year']:<6} {row['reserves_usd_m_actual']:>10,.0f}   {row['reserves_usd_m_est']:>10,.0f}   {row['reserves_error_pct']:>+8.1f}%")

print(f"\nMean Absolute Error (Reserves): {pk_compare['reserves_error_pct'].abs().mean():.1f}%")

print("\n                  INFLATION (%)")
print("-" * 70)
print(f"{'Year':<6} {'Actual':<12} {'Our Est':<12} {'Error %':<10}")
print("-" * 70)
for _, row in pk_compare.iterrows():
    print(f"{row['year']:<6} {row['inflation_actual']:>10.1f}%  {row['inflation_est']:>10.1f}%  {row['inflation_error_pct']:>+8.1f}%")

print(f"\nMean Absolute Error (Inflation): {pk_compare['inflation_error_pct'].abs().mean():.1f}%")

# ============================================================
# COMPARISON: Ghana
# ============================================================

print("\n\n" + "=" * 70)
print("GHANA: ACTUAL vs OUR ESTIMATES")
print("=" * 70)

gh_compare = gh_actual.merge(gh_yearly, on='year')
# Handle None for 2024
gh_compare_valid = gh_compare[gh_compare['reserves_usd_m_actual'].notna()].copy()
gh_compare_valid['reserves_error_pct'] = ((gh_compare_valid['reserves_usd_m_est'] - gh_compare_valid['reserves_usd_m_actual'])
                                          / gh_compare_valid['reserves_usd_m_actual'] * 100)
gh_compare['inflation_error_pct'] = ((gh_compare['inflation_est'] - gh_compare['inflation_actual'])
                                      / gh_compare['inflation_actual'] * 100)

print("\n                  RESERVES (USD millions)")
print("-" * 70)
print(f"{'Year':<6} {'Actual':<12} {'Our Est':<12} {'Error %':<10}")
print("-" * 70)
for _, row in gh_compare.iterrows():
    if pd.notna(row['reserves_usd_m_actual']):
        error = (row['reserves_usd_m_est'] - row['reserves_usd_m_actual']) / row['reserves_usd_m_actual'] * 100
        print(f"{row['year']:<6} {row['reserves_usd_m_actual']:>10,.0f}   {row['reserves_usd_m_est']:>10,.0f}   {error:>+8.1f}%")
    else:
        print(f"{row['year']:<6} {'N/A':>10}   {row['reserves_usd_m_est']:>10,.0f}   {'N/A':>9}")

print(f"\nMean Absolute Error (Reserves): {gh_compare_valid['reserves_error_pct'].abs().mean():.1f}%")

print("\n                  INFLATION (%)")
print("-" * 70)
print(f"{'Year':<6} {'Actual':<12} {'Our Est':<12} {'Error %':<10}")
print("-" * 70)
for _, row in gh_compare.iterrows():
    print(f"{row['year']:<6} {row['inflation_actual']:>10.1f}%  {row['inflation_est']:>10.1f}%  {row['inflation_error_pct']:>+8.1f}%")

print(f"\nMean Absolute Error (Inflation): {gh_compare['inflation_error_pct'].abs().mean():.1f}%")

# ============================================================
# CRITICAL FINDINGS
# ============================================================

print("\n\n" + "=" * 70)
print("CRITICAL FINDINGS - DATA QUALITY ASSESSMENT")
print("=" * 70)

print("""
PAKISTAN DATA QUALITY:
""")
pk_res_mae = pk_compare['reserves_error_pct'].abs().mean()
pk_inf_mae = pk_compare['inflation_error_pct'].abs().mean()
if pk_res_mae > 30:
    print(f"  ⚠ RESERVES: {pk_res_mae:.0f}% average error - SIGNIFICANT DISCREPANCY")
elif pk_res_mae > 15:
    print(f"  ⚠ RESERVES: {pk_res_mae:.0f}% average error - MODERATE DISCREPANCY")
else:
    print(f"  ✓ RESERVES: {pk_res_mae:.0f}% average error - ACCEPTABLE")

if pk_inf_mae > 30:
    print(f"  ⚠ INFLATION: {pk_inf_mae:.0f}% average error - SIGNIFICANT DISCREPANCY")
elif pk_inf_mae > 15:
    print(f"  ⚠ INFLATION: {pk_inf_mae:.0f}% average error - MODERATE DISCREPANCY")
else:
    print(f"  ✓ INFLATION: {pk_inf_mae:.0f}% average error - ACCEPTABLE")

print("""
GHANA DATA QUALITY:
""")
gh_res_mae = gh_compare_valid['reserves_error_pct'].abs().mean()
gh_inf_mae = gh_compare['inflation_error_pct'].abs().mean()
if gh_res_mae > 30:
    print(f"  ⚠ RESERVES: {gh_res_mae:.0f}% average error - SIGNIFICANT DISCREPANCY")
elif gh_res_mae > 15:
    print(f"  ⚠ RESERVES: {gh_res_mae:.0f}% average error - MODERATE DISCREPANCY")
else:
    print(f"  ✓ RESERVES: {gh_res_mae:.0f}% average error - ACCEPTABLE")

if gh_inf_mae > 30:
    print(f"  ⚠ INFLATION: {gh_inf_mae:.0f}% average error - SIGNIFICANT DISCREPANCY")
elif gh_inf_mae > 15:
    print(f"  ⚠ INFLATION: {gh_inf_mae:.0f}% average error - MODERATE DISCREPANCY")
else:
    print(f"  ✓ INFLATION: {gh_inf_mae:.0f}% average error - ACCEPTABLE")

# ============================================================
# SPECIFIC PROBLEM AREAS
# ============================================================

print("\n\n" + "=" * 70)
print("SPECIFIC PROBLEM AREAS")
print("=" * 70)

# Ghana 2023 reserves
gh_2023 = gh_compare[gh_compare['year'] == 2023].iloc[0]
print(f"""
GHANA 2023 RESERVES:
  Actual (World Bank):  ${gh_2023['reserves_usd_m_actual']:,.0f}M
  Our estimate:         ${gh_2023['reserves_usd_m_est']:,.0f}M

  → We OVERESTIMATED reserves by {(gh_2023['reserves_usd_m_est']/gh_2023['reserves_usd_m_actual']-1)*100:.0f}%
  → This means the Ghana crisis was MORE SEVERE than we modeled
  → Our HMM might be UNDERDETECTING crisis severity
""")

# Pakistan 2022 check
pk_2022 = pk_compare[pk_compare['year'] == 2022].iloc[0]
print(f"""
PAKISTAN 2022 RESERVES:
  Actual (World Bank):  ${pk_2022['reserves_usd_m_actual']:,.0f}M
  Our estimate:         ${pk_2022['reserves_usd_m_est']:,.0f}M

  → We {"UNDERESTIMATED" if pk_2022['reserves_usd_m_est'] < pk_2022['reserves_usd_m_actual'] else "OVERESTIMATED"} reserves
  → Error: {(pk_2022['reserves_usd_m_est']/pk_2022['reserves_usd_m_actual']-1)*100:+.0f}%
""")

# ============================================================
# IMPLICATIONS FOR OUR CLAIMS
# ============================================================

print("\n" + "=" * 70)
print("IMPLICATIONS FOR 'METHODOLOGY GENERALIZES' CLAIM")
print("=" * 70)

print("""
HONEST ASSESSMENT:

1. DATA QUALITY ISSUES:
   - Our estimates are based on interpolation + public reports
   - World Bank data shows significant discrepancies (especially Ghana reserves)
   - Monthly granularity is SIMULATED, not observed

2. WHAT WE CAN CLAIM:
   ✓ Similar PATTERNS exist across countries (reserve collapse, inflation surge)
   ✓ Same FEATURES are relevant (reserves, inflation, real rates)
   ✓ 3-state model STRUCTURE may apply

3. WHAT WE CANNOT CLAIM (yet):
   ✗ Precise regime timing validated
   ✗ Event detection rates are accurate
   ✗ Early warning lead times are confirmed
   ✗ Methodology "works" on Pakistan/Ghana (insufficient data quality)

4. TO MAKE STRONGER CLAIMS, WE NEED:
   - Actual monthly data from SBP, BoG, PBS, GSS
   - KIBOR and Ghana interbank rates (not estimates)
   - Proper out-of-sample validation

5. CURRENT STATUS:
   This is a PROOF OF CONCEPT, not a validated extension.
   The cross-country work demonstrates FEASIBILITY, not CONFIRMATION.
""")

# Save comparison for reference
pk_compare.to_csv('data/cross_country/pakistan_validation_vs_worldbank.csv', index=False)
gh_compare.to_csv('data/cross_country/ghana_validation_vs_worldbank.csv', index=False)
print("\n✓ Saved: data/cross_country/pakistan_validation_vs_worldbank.csv")
print("✓ Saved: data/cross_country/ghana_validation_vs_worldbank.csv")

print("\n" + "=" * 70)
print("VALIDATION COMPLETE")
print("=" * 70)
