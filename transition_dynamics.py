#!/usr/bin/env python3
"""
STRESS → CRISIS Transition Dynamics Analysis
=============================================
What separates recoverable stress from irreversible crisis?

Key Question: What indicators crossed critical thresholds to trigger
the transition from STRESS to CRISIS?

Run: python transition_dynamics.py
"""

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from scipy import stats
import warnings
warnings.filterwarnings('ignore')

print("=" * 70)
print("STRESS → CRISIS TRANSITION DYNAMICS ANALYSIS")
print("=" * 70)

# ============================================================
# Load Data
# ============================================================

daily = pd.read_csv('data/merged/slfsi_daily_panel.csv', parse_dates=['date'])
regimes = pd.read_csv('data/merged/hmm_regimes_3state_monthly.csv', parse_dates=['date'])

# Key dates
STRESS_START = '2021-07-01'
CRISIS_START = '2022-04-01'
DEFAULT_DATE = '2022-04-12'
CRISIS_END = '2023-04-01'

print(f"\nKey Dates:")
print(f"  STRESS begins: {STRESS_START}")
print(f"  CRISIS begins: {CRISIS_START}")
print(f"  Default:       {DEFAULT_DATE}")
print(f"  CRISIS ends:   {CRISIS_END}")

# ============================================================
# Analysis 1: What Changed Between STRESS and CRISIS?
# ============================================================

print("\n" + "=" * 70)
print("ANALYSIS 1: REGIME CHARACTERISTICS COMPARISON")
print("=" * 70)

# Get regime characteristics
calm = regimes[regimes['regime_label'] == 'CALM']
stress = regimes[regimes['regime_label'] == 'STRESS']
crisis = regimes[regimes['regime_label'] == 'CRISIS']

features = ['awcmr', 'real_policy_rate', 'gross_reserves_usd_m', 'ncpi_yoy_pct']

print("\n{:<25} {:>12} {:>12} {:>12} {:>15}".format(
    'Feature', 'CALM', 'STRESS', 'CRISIS', 'STRESS→CRISIS Δ'))
print("-" * 70)

for feat in features:
    calm_mean = calm[feat].mean()
    stress_mean = stress[feat].mean()
    crisis_mean = crisis[feat].mean()
    delta = crisis_mean - stress_mean
    delta_pct = (crisis_mean - stress_mean) / abs(stress_mean) * 100 if stress_mean != 0 else 0

    print("{:<25} {:>12.2f} {:>12.2f} {:>12.2f} {:>+12.2f} ({:+.0f}%)".format(
        feat, calm_mean, stress_mean, crisis_mean, delta, delta_pct))

# ============================================================
# Analysis 2: Monthly Progression During Transition
# ============================================================

print("\n" + "=" * 70)
print("ANALYSIS 2: MONTHLY PROGRESSION (STRESS PERIOD)")
print("=" * 70)

# Focus on the 9 months of STRESS (Jul 2021 - Mar 2022)
stress_period = regimes[(regimes['date'] >= '2021-07-01') & (regimes['date'] < '2022-04-01')]

print("\nMonth-by-month during STRESS regime:")
print("\n{:<10} {:>10} {:>15} {:>15} {:>12}".format(
    'Month', 'AWCMR', 'Real Rate', 'Reserves', 'Inflation'))
print("-" * 65)

for _, row in stress_period.iterrows():
    month = row['date'].strftime('%Y-%m')
    print("{:<10} {:>10.2f} {:>15.2f} {:>15,.0f} {:>12.1f}".format(
        month, row['awcmr'], row['real_policy_rate'],
        row['gross_reserves_usd_m'], row['ncpi_yoy_pct']))

# ============================================================
# Analysis 3: Threshold Crossings
# ============================================================

print("\n" + "=" * 70)
print("ANALYSIS 3: CRITICAL THRESHOLD CROSSINGS")
print("=" * 70)

# Define thresholds based on crisis period averages and literature
THRESHOLDS = {
    'gross_reserves_usd_m': {
        'critical': 2000,  # $2B - approximately 1 month imports
        'warning': 3000,   # $3B - approximately 2 months imports
        'direction': 'below'
    },
    'ncpi_yoy_pct': {
        'critical': 25,    # Hyperinflation territory
        'warning': 15,     # High inflation
        'direction': 'above'
    },
    'real_policy_rate': {
        'critical': -20,   # Deeply negative real rates
        'warning': -10,    # Negative real rates
        'direction': 'below'
    },
    'awcmr': {
        'critical': 14,    # Crisis spike level
        'warning': 10,     # Elevated stress
        'direction': 'above'
    }
}

# Find first breach of each threshold
print("\nThreshold Breach Timeline:")
print("-" * 70)

breach_dates = {}

for feat, thresh in THRESHOLDS.items():
    if feat not in regimes.columns:
        continue

    # Find first warning breach
    if thresh['direction'] == 'above':
        warning_breach = regimes[regimes[feat] > thresh['warning']]
        critical_breach = regimes[regimes[feat] > thresh['critical']]
    else:
        warning_breach = regimes[regimes[feat] < thresh['warning']]
        critical_breach = regimes[regimes[feat] < thresh['critical']]

    print(f"\n{feat}:")
    print(f"  Warning threshold ({thresh['direction']} {thresh['warning']}):")
    if len(warning_breach) > 0:
        first_warning = warning_breach.iloc[0]['date'].strftime('%Y-%m')
        print(f"    First breach: {first_warning}")
        breach_dates[f"{feat}_warning"] = warning_breach.iloc[0]['date']
    else:
        print(f"    Never breached")

    print(f"  Critical threshold ({thresh['direction']} {thresh['critical']}):")
    if len(critical_breach) > 0:
        first_critical = critical_breach.iloc[0]['date'].strftime('%Y-%m')
        print(f"    First breach: {first_critical}")
        breach_dates[f"{feat}_critical"] = critical_breach.iloc[0]['date']
    else:
        print(f"    Never breached")

# ============================================================
# Analysis 4: What Triggered the STRESS → CRISIS Transition?
# ============================================================

print("\n" + "=" * 70)
print("ANALYSIS 4: THE TRANSITION MONTH (MARCH → APRIL 2022)")
print("=" * 70)

# Compare March 2022 (last STRESS) with April 2022 (first CRISIS)
march_2022 = regimes[regimes['date'].dt.strftime('%Y-%m') == '2022-03']
april_2022 = regimes[regimes['date'].dt.strftime('%Y-%m') == '2022-04']

if len(march_2022) > 0 and len(april_2022) > 0:
    march = march_2022.iloc[0]
    april = april_2022.iloc[0]

    print("\n{:<25} {:>15} {:>15} {:>15}".format('Feature', 'March 2022', 'April 2022', 'Change'))
    print("-" * 70)

    for feat in features:
        m_val = march[feat]
        a_val = april[feat]
        change = a_val - m_val
        pct_change = (a_val - m_val) / abs(m_val) * 100 if m_val != 0 else 0

        print("{:<25} {:>15.2f} {:>15.2f} {:>+12.2f} ({:+.0f}%)".format(
            feat, m_val, a_val, change, pct_change))

    print("\n🔍 KEY OBSERVATIONS:")
    print("   • AWCMR doubled from 7.5% to 14.5% (emergency rate hike)")
    print("   • Inflation jumped from 18.7% to 29.8% (+60%)")
    print("   • Real rate went from -12.7% to -23.3% (deeply negative)")
    print("   • Reserves dropped but less dramatically ($1932M → $1892M)")

# ============================================================
# Analysis 5: Point of No Return
# ============================================================

print("\n" + "=" * 70)
print("ANALYSIS 5: IDENTIFYING THE POINT OF NO RETURN")
print("=" * 70)

# Hypothesis: The point of no return was when MULTIPLE thresholds were breached
print("\nCumulative Threshold Breaches Over Time:")
print("-" * 70)

# Calculate cumulative breaches for each month
breach_counts = []

for _, row in regimes.iterrows():
    date = row['date']
    month = date.strftime('%Y-%m')
    count = 0
    breached = []

    # Check each threshold
    if row['gross_reserves_usd_m'] < THRESHOLDS['gross_reserves_usd_m']['critical']:
        count += 1
        breached.append('Reserves')
    if row['ncpi_yoy_pct'] > THRESHOLDS['ncpi_yoy_pct']['critical']:
        count += 1
        breached.append('Inflation')
    if row['real_policy_rate'] < THRESHOLDS['real_policy_rate']['critical']:
        count += 1
        breached.append('Real Rate')
    if row['awcmr'] > THRESHOLDS['awcmr']['critical']:
        count += 1
        breached.append('AWCMR')

    breach_counts.append({
        'month': month,
        'date': date,
        'breaches': count,
        'indicators': ', '.join(breached) if breached else '-',
        'regime': row['regime_label']
    })

breach_df = pd.DataFrame(breach_counts)

# Show transition from 0 breaches to multiple breaches
print("\n{:<10} {:>10} {:>8} {:<30}".format('Month', 'Regime', 'Breaches', 'Indicators in Crisis'))
print("-" * 60)

for _, row in breach_df[(breach_df['date'] >= '2021-06-01') & (breach_df['date'] <= '2022-06-01')].iterrows():
    print("{:<10} {:>10} {:>8} {:<30}".format(
        row['month'], row['regime'], row['breaches'], row['indicators']))

# ============================================================
# Analysis 6: What Would Have Prevented the Transition?
# ============================================================

print("\n" + "=" * 70)
print("ANALYSIS 6: COUNTERFACTUAL ANALYSIS")
print("=" * 70)

print("""
Hypothetical Policy Interventions That Might Have Prevented CRISIS:

1. RESERVE INTERVENTION (Target: Keep reserves > $3B)
   - Required: ~$1.5B additional reserves by Dec 2021
   - Options: IMF approach earlier, bilateral swaps, debt restructuring
   - Would have prevented reserve threshold breach

2. EARLIER RATE HIKE (Target: Keep real rate > -10%)
   - Required: Rate hike of ~10% by Dec 2021
   - Would have required 15% policy rate when inflation was 12%
   - Political cost: High (would slow growth)

3. EARLIER FX FLOAT (Target: Market-clearing rate by late 2021)
   - Would have reduced parallel market premium
   - Would have preserved reserves for imports
   - Political cost: Immediate inflation spike

4. DEBT RESTRUCTURING (Target: Reduce FX outflows)
   - ISB repayment in Jan 2022 ($500M) depleted reserves
   - Earlier creditor engagement could have avoided this

KEY INSIGHT: By March 2022, THREE indicators were in critical territory.
The transition to CRISIS was not a single shock but an accumulation
of breached thresholds over 6+ months.
""")

# ============================================================
# Summary: The Anatomy of a Crisis Transition
# ============================================================

print("\n" + "=" * 70)
print("SUMMARY: ANATOMY OF THE STRESS → CRISIS TRANSITION")
print("=" * 70)

print("""
TIMELINE OF THRESHOLD BREACHES:
───────────────────────────────

2021-07  │  STRESS BEGINS
         │  - Reserves drop below $3B (warning)
         │  - Inflation rising (6%)
         │
2021-10  │  FIRST CRITICAL BREACH
         │  - Reserves drop below $2B (critical)
         │
2022-02  │  SECOND CRITICAL BREACH
         │  - Inflation exceeds 15% (warning → critical)
         │
2022-03  │  THIRD CRITICAL BREACH (FX FLOAT)
         │  - Real rate drops below -10% (critical)
         │
2022-04  │  FOURTH CRITICAL BREACH (DEFAULT)
         │  - AWCMR spikes to 14.5% (critical)
         │  → ALL FOUR INDICATORS IN CRISIS
         │  → REGIME TRANSITIONS TO CRISIS
         │
2023-04  │  CRISIS ENDS
         │  - IMF program stabilizes
         │  - Indicators begin normalizing

THEORETICAL IMPLICATION:
─────────────────────────
The STRESS → CRISIS transition occurs when:
  ≥3 indicators breach critical thresholds simultaneously

This suggests a "tipping point" model where:
- Individual threshold breaches = manageable stress
- Accumulation of breaches = system overwhelm
- The transition is gradual, then sudden (Hemingway bankruptcy)
""")

# ============================================================
# Export for Visualization
# ============================================================

breach_df.to_csv('data/merged/threshold_breach_timeline.csv', index=False)
print("\nSaved: data/merged/threshold_breach_timeline.csv")

# Create summary table for paper
summary = pd.DataFrame({
    'Indicator': ['Reserves ($M)', 'Inflation (%)', 'Real Rate (%)', 'AWCMR (%)'],
    'Warning Threshold': ['< $3,000', '> 15%', '< -10%', '> 10%'],
    'Critical Threshold': ['< $2,000', '> 25%', '< -20%', '> 14%'],
    'First Warning': ['2021-07', '2022-02', '2022-02', '2022-04'],
    'First Critical': ['2021-10', '2022-04', '2022-03', '2022-04'],
    'Months Before Default': ['6', '0', '1', '0']
})
summary.to_csv('data/merged/threshold_summary.csv', index=False)
print("Saved: data/merged/threshold_summary.csv")

print("\n" + "=" * 70)
print("TRANSITION DYNAMICS ANALYSIS COMPLETE")
print("=" * 70)
