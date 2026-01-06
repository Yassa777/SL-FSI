#!/usr/bin/env python3
"""
Enhanced Validation Framework with Sustained Crossing
======================================================
Implements dual-window evaluation with probability-based sustained crossing.

Key Features:
1. Dual windows: ±1 month (tactical), ±2 months (strategic)
2. Sustained crossing: K=3 consecutive months above threshold tau=0.7
3. Probability-based evaluation (not just labels)

Run: python enhanced_validation.py
"""

import pandas as pd
import numpy as np
from datetime import timedelta
import warnings
warnings.filterwarnings('ignore')

# ============================================================
# CONFIGURATION
# ============================================================

# Sustained crossing parameters
TAU = 0.7  # Probability threshold (70% confident)
K = 3      # Consecutive months required

# Evaluation windows (in months)
TACTICAL_WINDOW = 1   # ±1 month
STRATEGIC_WINDOW = 2  # ±2 months

# ============================================================
# PRE-SPECIFIED EVENTS
# ============================================================

CRISIS_EVENTS = {
    # Regime shift anchors
    '2022-01-18': {'name': '$500M ISB Repayment', 'expected': 'STRESS', 'type': 'anchor'},
    '2022-03-07': {'name': 'FX Float (CBSL abandons peg)', 'expected': 'CRISIS', 'type': 'anchor'},
    '2022-04-12': {'name': 'Sovereign Default', 'expected': 'CRISIS', 'type': 'anchor'},
    '2022-09-01': {'name': 'IMF Staff-Level Agreement', 'expected': 'CRISIS', 'type': 'anchor'},
    '2023-03-20': {'name': 'IMF EFF Approval', 'expected': 'CRISIS', 'type': 'anchor'},
    '2023-06-28': {'name': 'Domestic Debt Restructuring', 'expected': 'STRESS', 'type': 'anchor'},
    '2024-06-26': {'name': 'Official Creditor Agreement', 'expected': 'CALM', 'type': 'anchor'},

    # Stress shocks
    '2019-04-21': {'name': 'Easter Sunday Attacks', 'expected': 'STRESS', 'type': 'shock'},
    '2020-03-20': {'name': 'COVID Lockdown', 'expected': 'STRESS', 'type': 'shock'},
    '2021-04-22': {'name': 'Fertilizer Import Ban', 'expected': 'STRESS', 'type': 'shock'},
    '2022-07-14': {'name': 'President Resigns', 'expected': 'CRISIS', 'type': 'shock'},
}

# ============================================================
# CORE EVALUATION FUNCTION
# ============================================================

def evaluate_hit(regime_probs_monthly, event_date, expected_regime,
                 tau=TAU, k=K, window_months=STRATEGIC_WINDOW):
    """
    Evaluate if HMM detects expected regime around event.

    A 'hit' requires:
    1. K consecutive months where P(expected_regime) > tau
    2. At least one such sequence within ±window_months of event

    Parameters:
    -----------
    regime_probs_monthly : DataFrame with 'period', 'p_calm', 'p_stress', 'p_crisis'
    event_date : pd.Timestamp
    expected_regime : str ('CALM', 'STRESS', or 'CRISIS')
    tau : float, probability threshold (default 0.7)
    k : int, consecutive months required (default 3)
    window_months : int, evaluation window (default 2)

    Returns:
    --------
    dict with:
        - is_hit: bool
        - max_prob: float (maximum probability of expected regime in window)
        - sustained_count: int (number of sustained crossing occurrences)
        - window_probs: list of probabilities in window
    """
    # Convert event date to period
    event_period = event_date.to_period('M')
    window_start = event_period - window_months
    window_end = event_period + window_months

    # Get observations in window
    in_window = (regime_probs_monthly['period'] >= window_start) & \
                (regime_probs_monthly['period'] <= window_end)
    window_probs = regime_probs_monthly[in_window].copy()

    if len(window_probs) == 0:
        return {
            'is_hit': False,
            'max_prob': 0.0,
            'sustained_count': 0,
            'window_probs': [],
            'reason': 'No data in window'
        }

    # Get probability column for expected regime
    prob_col = f'p_{expected_regime.lower()}'

    if prob_col not in window_probs.columns:
        return {
            'is_hit': False,
            'max_prob': 0.0,
            'sustained_count': 0,
            'window_probs': [],
            'reason': f'Column {prob_col} not found'
        }

    probs = window_probs[prob_col].values
    max_prob = probs.max() if len(probs) > 0 else 0.0

    # Check for K consecutive months above tau
    above_threshold = (probs > tau).astype(int)

    # Rolling sum to find K consecutive
    sustained_count = 0
    for i in range(len(above_threshold) - k + 1):
        if above_threshold[i:i+k].sum() == k:
            sustained_count += 1

    is_hit = sustained_count > 0

    return {
        'is_hit': is_hit,
        'max_prob': max_prob,
        'sustained_count': sustained_count,
        'window_probs': probs.tolist(),
        'reason': 'Hit' if is_hit else f'Max prob {max_prob:.1%} < {tau:.0%} or not sustained'
    }


def evaluate_all_events(regime_probs_monthly, events, window_months, tau=TAU, k=K):
    """
    Evaluate all events with sustained crossing logic.

    Returns DataFrame with detailed results.
    """
    results = []

    for event_date_str, event_info in events.items():
        event_date = pd.Timestamp(event_date_str)
        expected_regime = event_info['expected']

        eval_result = evaluate_hit(
            regime_probs_monthly,
            event_date,
            expected_regime,
            tau=tau,
            k=k,
            window_months=window_months
        )

        results.append({
            'date': event_date_str,
            'event': event_info['name'],
            'type': event_info['type'],
            'expected_regime': expected_regime,
            'is_hit': eval_result['is_hit'],
            'max_prob': eval_result['max_prob'],
            'sustained_count': eval_result['sustained_count'],
            'reason': eval_result['reason']
        })

    return pd.DataFrame(results)


# ============================================================
# MAIN VALIDATION REPORT
# ============================================================

def generate_enhanced_validation_report():
    """Generate full validation report with sustained crossing."""

    print("=" * 80)
    print("ENHANCED VALIDATION FRAMEWORK")
    print(f"Sustained Crossing: K={K} consecutive months, τ={TAU:.0%} threshold")
    print("=" * 80)

    # Load probability data
    print("\nLoading regime probabilities...")
    try:
        probs_df = pd.read_csv('data/merged/hmm_probs_monthly.csv', parse_dates=['date'])
        probs_df['period'] = probs_df['date'].dt.to_period('M')
        print(f"  Loaded {len(probs_df)} months")
        print(f"  Date range: {probs_df['date'].min().strftime('%Y-%m')} to {probs_df['date'].max().strftime('%Y-%m')}")
    except Exception as e:
        print(f"  ERROR: Could not load probability data: {e}")
        print("  Run recursive_realtime_hmm.py first!")
        return None

    # ============================================================
    # Tactical Window Evaluation (±1 month)
    # ============================================================

    print("\n" + "=" * 80)
    print(f"TACTICAL WINDOW EVALUATION (±{TACTICAL_WINDOW} month)")
    print("=" * 80)

    tactical_results = evaluate_all_events(
        probs_df, CRISIS_EVENTS, TACTICAL_WINDOW, tau=TAU, k=K
    )

    print(f"\n{'Date':<12} {'Event':<30} {'Expected':<10} {'Hit':<6} {'MaxProb':<10} {'Sustained':<10}")
    print("-" * 90)

    for _, row in tactical_results.iterrows():
        hit_str = "✓" if row['is_hit'] else "✗"
        print(f"{row['date']:<12} {row['event'][:28]:<30} {row['expected_regime']:<10} {hit_str:<6} {row['max_prob']:<10.1%} {row['sustained_count']:<10}")

    tactical_hits = tactical_results['is_hit'].sum()
    tactical_total = len(tactical_results)
    print(f"\nTactical Hit Rate: {tactical_hits}/{tactical_total} = {tactical_hits/tactical_total:.1%}")

    # ============================================================
    # Strategic Window Evaluation (±2 months)
    # ============================================================

    print("\n" + "=" * 80)
    print(f"STRATEGIC WINDOW EVALUATION (±{STRATEGIC_WINDOW} months)")
    print("=" * 80)

    strategic_results = evaluate_all_events(
        probs_df, CRISIS_EVENTS, STRATEGIC_WINDOW, tau=TAU, k=K
    )

    print(f"\n{'Date':<12} {'Event':<30} {'Expected':<10} {'Hit':<6} {'MaxProb':<10} {'Sustained':<10}")
    print("-" * 90)

    for _, row in strategic_results.iterrows():
        hit_str = "✓" if row['is_hit'] else "✗"
        print(f"{row['date']:<12} {row['event'][:28]:<30} {row['expected_regime']:<10} {hit_str:<6} {row['max_prob']:<10.1%} {row['sustained_count']:<10}")

    strategic_hits = strategic_results['is_hit'].sum()
    strategic_total = len(strategic_results)
    print(f"\nStrategic Hit Rate: {strategic_hits}/{strategic_total} = {strategic_hits/strategic_total:.1%}")

    # ============================================================
    # Sensitivity Analysis: Varying tau and K
    # ============================================================

    print("\n" + "=" * 80)
    print("SENSITIVITY ANALYSIS")
    print("=" * 80)

    print("\nStrategic Hit Rate by (tau, K):")
    header = "tau \\ K"
    print(f"{header:<8}", end="")
    for k_val in [1, 2, 3, 4]:
        print(f"K={k_val:<7}", end="")
    print()
    print("-" * 40)

    for tau_val in [0.5, 0.6, 0.7, 0.8, 0.9]:
        print(f"τ={tau_val:<6}", end="")
        for k_val in [1, 2, 3, 4]:
            results = evaluate_all_events(
                probs_df, CRISIS_EVENTS, STRATEGIC_WINDOW, tau=tau_val, k=k_val
            )
            hit_rate = results['is_hit'].sum() / len(results)
            print(f"{hit_rate:<8.0%}", end="")
        print()

    # ============================================================
    # Early Warning Analysis
    # ============================================================

    print("\n" + "=" * 80)
    print("EARLY WARNING ANALYSIS")
    print("=" * 80)

    # Key crisis date: April 2022 default
    default_date = pd.Timestamp('2022-04-12')
    default_period = default_date.to_period('M')

    # Find when CRISIS probability first exceeded threshold
    crisis_threshold_periods = probs_df[probs_df['p_crisis'] > TAU]['period']
    stress_threshold_periods = probs_df[probs_df['p_stress'] > TAU]['period']

    print(f"\nDefault Date: {default_date.strftime('%Y-%m-%d')}")

    if len(crisis_threshold_periods) > 0:
        first_crisis_signal = crisis_threshold_periods.min()
        lead_months = (default_period - first_crisis_signal).n
        print(f"First CRISIS signal (P > {TAU:.0%}): {first_crisis_signal}")
        print(f"  Lead time: {lead_months} months before default")
    else:
        print(f"No CRISIS signal above {TAU:.0%} threshold")

    if len(stress_threshold_periods) > 0:
        first_stress_signal = stress_threshold_periods.min()
        lead_months_stress = (default_period - first_stress_signal).n
        print(f"\nFirst STRESS signal (P > {TAU:.0%}): {first_stress_signal}")
        print(f"  Lead time: {lead_months_stress} months before default")

    # ============================================================
    # Summary
    # ============================================================

    print("\n" + "=" * 80)
    print("VALIDATION SUMMARY")
    print("=" * 80)

    print(f"""
EVALUATION PARAMETERS:
  - Probability threshold (τ): {TAU:.0%}
  - Sustained crossing (K): {K} consecutive months
  - Tactical window: ±{TACTICAL_WINDOW} month
  - Strategic window: ±{STRATEGIC_WINDOW} months

RESULTS:
  - Tactical Hit Rate: {tactical_hits}/{tactical_total} ({tactical_hits/tactical_total:.0%})
  - Strategic Hit Rate: {strategic_hits}/{strategic_total} ({strategic_hits/strategic_total:.0%})

KEY INSIGHT:
  The sustained crossing requirement (K={K} months above {TAU:.0%})
  ensures that detected regimes are stable, not transient fluctuations.
  Lower hit rates with stricter thresholds indicate genuine regime detection
  rather than noisy oscillations.
""")

    # Save results
    strategic_results.to_csv('data/merged/enhanced_validation_results.csv', index=False)
    print("Saved: data/merged/enhanced_validation_results.csv")

    return {
        'tactical': tactical_results,
        'strategic': strategic_results
    }


# ============================================================
# MAIN
# ============================================================

if __name__ == '__main__':
    results = generate_enhanced_validation_report()
