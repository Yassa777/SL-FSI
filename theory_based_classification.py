#!/usr/bin/env python3
"""
Theory-Based Regime Classification
===================================
Implements regime classification based on three theoretical frameworks:

1. Krugman (1979) Balance of Payments Crisis Model
   - Reserve adequacy: months of import cover
   - CRISIS: < 2 months, STRESS: < 4 months, CALM: >= 4 months

2. Reinhart-Rogoff (2009) Debt Intolerance
   - Real interest rate sustainability
   - CRISIS: real rate < -20%, STRESS: < 0%, CALM: >= 0%

3. Calvo (1998) Sudden Stop
   - Capital flow reversals proxied by ISB yield spread
   - CRISIS: spread > 2000 bps, STRESS: > 500 bps, CALM: <= 500 bps

This creates a parallel classification to compare with HMM-detected regimes.

Run: python theory_based_classification.py
"""

import pandas as pd
import numpy as np
import os
import warnings
warnings.filterwarnings('ignore')

# ============================================================
# Configuration
# ============================================================

PROJECT_ROOT = os.path.dirname(os.path.abspath(__file__))
MERGED_DIR = os.path.join(PROJECT_ROOT, 'data', 'merged')

# Theory-based thresholds (from plan)
KRUGMAN_THRESHOLDS = {
    'CRISIS': 2,    # Reserve cover < 2 months
    'STRESS': 4,    # Reserve cover < 4 months
}

REINHART_ROGOFF_THRESHOLDS = {
    'CRISIS': -20,  # Real rate < -20%
    'STRESS': 0,    # Real rate < 0%
}

CALVO_THRESHOLDS = {
    'CRISIS': 2000,  # ISB spread > 2000 bps (20%)
    'STRESS': 500,   # ISB spread > 500 bps (5%)
}

print("=" * 70)
print("THEORY-BASED REGIME CLASSIFICATION")
print("=" * 70)

# ============================================================
# Load Data
# ============================================================

print("\nLoading data...")

# Try enhanced monthly data first
monthly_path = os.path.join(MERGED_DIR, 'monthly_with_indicators.csv')
if os.path.exists(monthly_path):
    monthly = pd.read_csv(monthly_path, parse_dates=['date'])
    print(f"  Loaded enhanced monthly: {len(monthly)} rows")
else:
    monthly = pd.read_csv(os.path.join(MERGED_DIR, 'slfsi_monthly_panel.csv'), parse_dates=['date'])
    print(f"  Loaded standard monthly: {len(monthly)} rows")

# Load HMM regimes for comparison
hmm_path = os.path.join(MERGED_DIR, 'hmm_probs_monthly.csv')
if os.path.exists(hmm_path):
    hmm_regimes = pd.read_csv(hmm_path, parse_dates=['date'])
    print(f"  Loaded HMM regimes: {len(hmm_regimes)} rows")
else:
    hmm_regimes = None
    print("  HMM regimes not available (run recursive_realtime_hmm.py first)")

# ============================================================
# Theory 1: Krugman BOP Model
# ============================================================

def classify_krugman(row):
    """
    Krugman (1979) BOP Crisis Model
    
    Uses reserve adequacy (months of import cover) as primary indicator.
    When reserves fall below critical threshold, speculative attack is imminent.
    """
    # Use net reserves if available, otherwise gross
    if 'net_import_cover' in row.index and pd.notna(row['net_import_cover']):
        cover = row['net_import_cover']
    elif 'import_cover_months' in row.index and pd.notna(row['import_cover_months']):
        cover = row['import_cover_months']
    else:
        return np.nan
    
    if cover < KRUGMAN_THRESHOLDS['CRISIS']:
        return 'CRISIS'
    elif cover < KRUGMAN_THRESHOLDS['STRESS']:
        return 'STRESS'
    else:
        return 'CALM'


print("\n" + "-" * 50)
print("Theory 1: KRUGMAN BOP MODEL")
print("-" * 50)

monthly['krugman_regime'] = monthly.apply(classify_krugman, axis=1)

krugman_counts = monthly['krugman_regime'].value_counts()
print(f"\nRegime distribution:")
for regime, count in krugman_counts.items():
    pct = count / len(monthly) * 100
    print(f"  {regime}: {count} months ({pct:.1f}%)")

# Show crisis periods
krugman_crisis = monthly[monthly['krugman_regime'] == 'CRISIS'][['date', 'net_import_cover']]
if len(krugman_crisis) > 0:
    print(f"\nCRISIS periods (reserve cover < {KRUGMAN_THRESHOLDS['CRISIS']} months):")
    for _, row in krugman_crisis.head(10).iterrows():
        print(f"  {row['date'].strftime('%Y-%m')}: {row.get('net_import_cover', 'N/A'):.1f} months")

# ============================================================
# Theory 2: Reinhart-Rogoff Debt Intolerance
# ============================================================

def classify_reinhart_rogoff(row):
    """
    Reinhart-Rogoff (2009) Debt Intolerance
    
    Uses real interest rate as indicator of fiscal sustainability.
    Deeply negative real rates signal financial repression and unsustainable debt.
    """
    if 'real_policy_rate' not in row.index or pd.isna(row['real_policy_rate']):
        return np.nan
    
    real_rate = row['real_policy_rate']
    
    if real_rate < REINHART_ROGOFF_THRESHOLDS['CRISIS']:
        return 'CRISIS'
    elif real_rate < REINHART_ROGOFF_THRESHOLDS['STRESS']:
        return 'STRESS'
    else:
        return 'CALM'


print("\n" + "-" * 50)
print("Theory 2: REINHART-ROGOFF DEBT INTOLERANCE")
print("-" * 50)

monthly['rr_regime'] = monthly.apply(classify_reinhart_rogoff, axis=1)

rr_counts = monthly['rr_regime'].value_counts()
print(f"\nRegime distribution:")
for regime, count in rr_counts.items():
    pct = count / len(monthly) * 100
    print(f"  {regime}: {count} months ({pct:.1f}%)")

# Show crisis periods
rr_crisis = monthly[monthly['rr_regime'] == 'CRISIS'][['date', 'real_policy_rate']]
if len(rr_crisis) > 0:
    print(f"\nCRISIS periods (real rate < {REINHART_ROGOFF_THRESHOLDS['CRISIS']}%):")
    for _, row in rr_crisis.head(10).iterrows():
        print(f"  {row['date'].strftime('%Y-%m')}: {row['real_policy_rate']:.1f}%")

# ============================================================
# Theory 3: Calvo Sudden Stop
# ============================================================

def classify_calvo(row):
    """
    Calvo (1998) Sudden Stop Model
    
    Uses ISB yield spread as proxy for capital flow reversals.
    High spreads indicate market pricing of default risk and capital outflows.
    """
    if 'isb_spread_bps' not in row.index or pd.isna(row['isb_spread_bps']):
        return np.nan
    
    spread = row['isb_spread_bps']
    
    if spread > CALVO_THRESHOLDS['CRISIS']:
        return 'CRISIS'
    elif spread > CALVO_THRESHOLDS['STRESS']:
        return 'STRESS'
    else:
        return 'CALM'


print("\n" + "-" * 50)
print("Theory 3: CALVO SUDDEN STOP")
print("-" * 50)

monthly['calvo_regime'] = monthly.apply(classify_calvo, axis=1)

calvo_counts = monthly['calvo_regime'].value_counts()
print(f"\nRegime distribution:")
for regime, count in calvo_counts.items():
    pct = count / len(monthly) * 100
    print(f"  {regime}: {count} months ({pct:.1f}%)")

# Show stress/crisis periods
calvo_stress = monthly[monthly['calvo_regime'].isin(['STRESS', 'CRISIS'])][['date', 'isb_spread_bps', 'calvo_regime']]
if len(calvo_stress) > 0:
    print(f"\nSTRESS/CRISIS periods (ISB spread > {CALVO_THRESHOLDS['STRESS']} bps):")
    for _, row in calvo_stress.head(10).iterrows():
        print(f"  {row['date'].strftime('%Y-%m')}: {row['isb_spread_bps']:.0f} bps ({row['calvo_regime']})")

# ============================================================
# Combined Theory-Based Classification
# ============================================================

def classify_combined_theory(row):
    """
    Combined multi-theory regime classification.
    
    CRISIS if ANY theory signals crisis.
    STRESS if ANY theory signals stress (and none signal crisis).
    CALM otherwise.
    """
    regimes = []
    
    for col in ['krugman_regime', 'rr_regime', 'calvo_regime']:
        if col in row.index and pd.notna(row[col]):
            regimes.append(row[col])
    
    if len(regimes) == 0:
        return np.nan
    
    if 'CRISIS' in regimes:
        return 'CRISIS'
    elif 'STRESS' in regimes:
        return 'STRESS'
    else:
        return 'CALM'


print("\n" + "-" * 50)
print("COMBINED THEORY-BASED REGIME")
print("-" * 50)

monthly['theory_regime'] = monthly.apply(classify_combined_theory, axis=1)

combined_counts = monthly['theory_regime'].value_counts()
print(f"\nCombined regime distribution:")
for regime, count in combined_counts.items():
    pct = count / len(monthly) * 100
    print(f"  {regime}: {count} months ({pct:.1f}%)")

# ============================================================
# Comparison with HMM Regimes
# ============================================================

if hmm_regimes is not None:
    print("\n" + "=" * 70)
    print("THEORY vs HMM REGIME COMPARISON")
    print("=" * 70)
    
    # Merge on date
    comparison = monthly.merge(
        hmm_regimes[['date', 'regime_realtime', 'p_calm', 'p_stress', 'p_crisis']],
        on='date',
        how='inner'
    )
    
    if len(comparison) > 0:
        # Agreement rate
        comparison['agreement'] = comparison['theory_regime'] == comparison['regime_realtime']
        agreement_rate = comparison['agreement'].mean()
        
        print(f"\nOverlapping observations: {len(comparison)}")
        print(f"Agreement rate: {agreement_rate:.1%}")
        
        # Confusion matrix
        print("\nConfusion Matrix (Theory vs HMM):")
        header = "Theory \\ HMM"
        print(f"{header:<15} {'CALM':<10} {'STRESS':<10} {'CRISIS':<10}")
        print("-" * 45)
        
        for theory_regime in ['CALM', 'STRESS', 'CRISIS']:
            row_data = comparison[comparison['theory_regime'] == theory_regime]
            calm_count = (row_data['regime_realtime'] == 'CALM').sum()
            stress_count = (row_data['regime_realtime'] == 'STRESS').sum()
            crisis_count = (row_data['regime_realtime'] == 'CRISIS').sum()
            print(f"{theory_regime:<15} {calm_count:<10} {stress_count:<10} {crisis_count:<10}")
        
        # Key insight: When do they disagree?
        disagreements = comparison[~comparison['agreement']]
        if len(disagreements) > 0:
            print(f"\nKey Disagreements ({len(disagreements)} months):")
            print(f"{'Date':<12} {'Theory':<10} {'HMM':<10} {'P(Crisis)':<12}")
            print("-" * 50)
            for _, row in disagreements.head(10).iterrows():
                print(f"{row['date'].strftime('%Y-%m'):<12} {row['theory_regime']:<10} {row['regime_realtime']:<10} {row['p_crisis']:.1%}")

# ============================================================
# Validation: Theory Thresholds Alignment
# ============================================================

print("\n" + "=" * 70)
print("VALIDATION: MEAN VALUES BY REGIME")
print("=" * 70)

# Check if HMM regimes align with theoretical expectations
if hmm_regimes is not None and len(comparison) > 0:
    print("\nHMM Regime Characteristics:")
    print(f"{'Regime':<10} {'Reserve Cover':<15} {'Real Rate':<15} {'ISB Spread':<15}")
    print("-" * 60)
    
    for regime in ['CALM', 'STRESS', 'CRISIS']:
        regime_data = comparison[comparison['regime_realtime'] == regime]
        if len(regime_data) > 0:
            reserve_mean = regime_data['net_import_cover'].mean() if 'net_import_cover' in regime_data.columns else np.nan
            real_rate_mean = regime_data['real_policy_rate'].mean() if 'real_policy_rate' in regime_data.columns else np.nan
            isb_mean = regime_data['isb_spread_bps'].mean() if 'isb_spread_bps' in regime_data.columns else np.nan
            
            reserve_str = f"{reserve_mean:.1f} mo" if pd.notna(reserve_mean) else "N/A"
            real_rate_str = f"{real_rate_mean:.1f}%" if pd.notna(real_rate_mean) else "N/A"
            isb_str = f"{isb_mean:.0f} bps" if pd.notna(isb_mean) else "N/A"
            
            print(f"{regime:<10} {reserve_str:<15} {real_rate_str:<15} {isb_str:<15}")
    
    # Validate ordering
    print("\nValidation Tests:")
    
    # Test 1: Reserve ordering (CALM > STRESS > CRISIS)
    calm_reserve = comparison[comparison['regime_realtime'] == 'CALM']['net_import_cover'].mean()
    stress_reserve = comparison[comparison['regime_realtime'] == 'STRESS']['net_import_cover'].mean()
    crisis_reserve = comparison[comparison['regime_realtime'] == 'CRISIS']['net_import_cover'].mean()
    
    if pd.notna(calm_reserve) and pd.notna(stress_reserve) and pd.notna(crisis_reserve):
        reserve_ordered = calm_reserve > stress_reserve > crisis_reserve
        print(f"  Reserve ordering (CALM > STRESS > CRISIS): {'PASS' if reserve_ordered else 'FAIL'}")
    
    # Test 2: Real rate sign flip
    calm_rate = comparison[comparison['regime_realtime'] == 'CALM']['real_policy_rate'].mean()
    crisis_rate = comparison[comparison['regime_realtime'] == 'CRISIS']['real_policy_rate'].mean()
    
    if pd.notna(calm_rate) and pd.notna(crisis_rate):
        rate_sign = calm_rate > 0 and crisis_rate < 0
        print(f"  Real rate sign flip (CALM +, CRISIS -): {'PASS' if rate_sign else 'FAIL'}")

# ============================================================
# Save Results
# ============================================================

print("\n" + "=" * 70)
print("SAVING RESULTS")
print("=" * 70)

# Save enhanced monthly with theory regimes
output_path = os.path.join(MERGED_DIR, 'monthly_with_theory_regimes.csv')
monthly.to_csv(output_path, index=False)
print(f"  Saved: {output_path}")

# Save comparison if available
if hmm_regimes is not None and len(comparison) > 0:
    comparison_path = os.path.join(MERGED_DIR, 'theory_vs_hmm_comparison.csv')
    comparison.to_csv(comparison_path, index=False)
    print(f"  Saved: {comparison_path}")

print("\n" + "=" * 70)
print("THEORY-BASED CLASSIFICATION COMPLETE")
print("=" * 70)

