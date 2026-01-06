#!/usr/bin/env python3
"""
SL-FSI Event-Alignment Validation Framework
============================================
Evaluates HMM regime detection against pre-specified crisis events.

Based on plan.md methodology:
- Dual evaluation windows (±14 days tactical, ±60 days strategic)
- Cost-weighted scoring (λ > 1 for missed signals)
- Z-score baseline benchmark comparison
- Hit rate and false alarm tracking

Run: python validation_framework.py
"""

import pandas as pd
import numpy as np
from hmmlearn import hmm
from datetime import timedelta
import warnings
warnings.filterwarnings('ignore')

# ============================================================
# CONFIGURATION
# ============================================================

# Evaluation windows (in days for daily, months for monthly)
TACTICAL_WINDOW_DAYS = 14
STRATEGIC_WINDOW_DAYS = 60
TACTICAL_WINDOW_MONTHS = 1  # ±1 month for monthly data
STRATEGIC_WINDOW_MONTHS = 2  # ±2 months for monthly data

# Cost-weighted scoring: λ > 1 penalizes missed signals more than false alarms
LAMBDA_MISSED = 2.0  # Cost of missing a crisis
LAMBDA_FALSE = 1.0   # Cost of false alarm

# Z-score threshold for baseline
ZSCORE_THRESHOLD = 2.0

# ============================================================
# PRE-SPECIFIED EVENTS (from plan.md)
# ============================================================

REGIME_SHIFT_ANCHORS = {
    '2022-01-18': {'name': '$500M ISB Repayment', 'expected_regime': 'STRESS', 'type': 'anchor'},
    '2022-03-07': {'name': 'FX Float (CBSL abandons peg)', 'expected_regime': 'STRESS', 'type': 'anchor'},
    '2022-04-12': {'name': 'External Debt Suspension (Default)', 'expected_regime': 'CRISIS', 'type': 'anchor'},
    '2022-09-01': {'name': 'IMF Staff-Level Agreement', 'expected_regime': 'CRISIS', 'type': 'anchor'},
    '2023-03-20': {'name': 'IMF EFF Approval', 'expected_regime': 'CRISIS', 'type': 'anchor'},
    '2023-06-28': {'name': 'Domestic Debt Restructuring Plan', 'expected_regime': 'STRESS', 'type': 'anchor'},
    '2024-06-26': {'name': 'Official Creditor Committee Agreement', 'expected_regime': 'CALM', 'type': 'anchor'},
    '2024-09-19': {'name': 'Bondholder Agreement-in-Principle', 'expected_regime': 'CALM', 'type': 'anchor'},
}

STRESS_SHOCKS = {
    '2019-04-21': {'name': 'Easter Sunday Attacks', 'expected_regime': 'CALM', 'type': 'shock'},
    '2020-03-20': {'name': 'COVID Lockdown Begins', 'expected_regime': 'CALM', 'type': 'shock'},
    '2021-04-22': {'name': 'Fertilizer Import Ban', 'expected_regime': 'CALM', 'type': 'shock'},
    '2022-07-14': {'name': 'President Resigns', 'expected_regime': 'CRISIS', 'type': 'shock'},
}

ALL_EVENTS = {**REGIME_SHIFT_ANCHORS, **STRESS_SHOCKS}


# ============================================================
# DATA LOADING
# ============================================================

def load_data():
    """Load daily panel and prepare monthly aggregation."""
    print("Loading data...")
    daily = pd.read_csv('data/merged/slfsi_daily_panel.csv', parse_dates=['date'])

    # Prepare monthly data
    features = ['awcmr', 'real_policy_rate', 'gross_reserves_usd_m', 'ncpi_yoy_pct']
    daily['year_month'] = daily['date'].dt.to_period('M')
    monthly = daily.groupby('year_month')[features + ['date']].first().reset_index(drop=True)
    monthly = monthly.dropna()

    print(f"  Daily: {len(daily)} rows")
    print(f"  Monthly: {len(monthly)} rows")

    return daily, monthly


# ============================================================
# HMM MODEL
# ============================================================

def fit_3state_monthly_hmm(monthly, features):
    """Fit the recommended 3-state monthly HMM."""
    print("\nFitting 3-state monthly HMM...")

    X = monthly[features].values
    X_scaled = (X - X.mean(axis=0)) / X.std(axis=0)

    model = hmm.GaussianHMM(n_components=3, covariance_type="diag", n_iter=300, random_state=42)
    model.fit(X_scaled)
    states = model.predict(X_scaled)

    monthly = monthly.copy()
    monthly['regime'] = states

    # Label regimes by inflation level
    state_inflation = {s: monthly[monthly['regime'] == s]['ncpi_yoy_pct'].mean() for s in range(3)}
    sorted_states = sorted(state_inflation.keys(), key=lambda x: state_inflation[x])
    state_labels = {sorted_states[0]: 'CALM', sorted_states[1]: 'STRESS', sorted_states[2]: 'CRISIS'}
    monthly['regime_label'] = monthly['regime'].map(state_labels)

    # Get transition dates
    transitions = monthly[monthly['regime'].diff() != 0].copy()

    print(f"  States: {state_labels}")
    print(f"  Transitions: {len(transitions) - 1}")

    return monthly, model, state_labels


# ============================================================
# Z-SCORE BASELINE MODEL
# ============================================================

def fit_zscore_baseline(monthly, features, threshold=ZSCORE_THRESHOLD):
    """Fit a simple z-score threshold baseline model."""
    print(f"\nFitting Z-score baseline (threshold={threshold})...")

    monthly = monthly.copy()

    # Compute z-scores for each feature
    for feat in features:
        monthly[f'{feat}_zscore'] = (monthly[feat] - monthly[feat].mean()) / monthly[feat].std()

    # Composite z-score (average absolute z-score)
    zscore_cols = [f'{feat}_zscore' for feat in features]
    monthly['composite_zscore'] = monthly[zscore_cols].abs().mean(axis=1)

    # Classify based on threshold
    # CRISIS if any feature has |z| > 2*threshold
    # STRESS if any feature has |z| > threshold
    # CALM otherwise

    max_abs_zscore = monthly[zscore_cols].abs().max(axis=1)

    monthly['zscore_regime'] = 'CALM'
    monthly.loc[max_abs_zscore > threshold, 'zscore_regime'] = 'STRESS'
    monthly.loc[max_abs_zscore > threshold * 1.5, 'zscore_regime'] = 'CRISIS'

    # Count regime distribution
    regime_counts = monthly['zscore_regime'].value_counts()
    print(f"  Regime distribution: {regime_counts.to_dict()}")

    return monthly


# ============================================================
# EVENT EVALUATION
# ============================================================

def evaluate_event_alignment(monthly, events, model_col, window_months):
    """
    Evaluate if model detects correct regime around events.

    Returns dict with:
    - hits: correctly classified events
    - misses: incorrectly classified events
    - details: per-event results
    """
    results = {
        'hits': 0,
        'misses': 0,
        'details': []
    }

    for event_date_str, event_info in events.items():
        event_date = pd.to_datetime(event_date_str)
        event_name = event_info['name']
        expected_regime = event_info['expected_regime']
        event_type = event_info['type']

        # Find the month of the event
        event_month = event_date.to_period('M')

        # Get regime in the window around the event
        window_start = event_month - window_months
        window_end = event_month + window_months

        # Find matching rows
        monthly['period'] = monthly['date'].dt.to_period('M')
        window_data = monthly[(monthly['period'] >= window_start) & (monthly['period'] <= window_end)]

        if len(window_data) == 0:
            results['details'].append({
                'date': event_date_str,
                'name': event_name,
                'type': event_type,
                'expected': expected_regime,
                'detected': 'NO DATA',
                'hit': False,
                'in_window': False
            })
            continue

        # Check if expected regime appears in window
        detected_regimes = window_data[model_col].unique()

        # Get the regime at the exact event month (or closest)
        exact_month = window_data[window_data['period'] == event_month]
        if len(exact_month) > 0:
            detected_at_event = exact_month[model_col].values[0]
        else:
            detected_at_event = window_data[model_col].values[0]

        hit = expected_regime in detected_regimes or detected_at_event == expected_regime

        if hit:
            results['hits'] += 1
        else:
            results['misses'] += 1

        results['details'].append({
            'date': event_date_str,
            'name': event_name,
            'type': event_type,
            'expected': expected_regime,
            'detected': detected_at_event,
            'all_in_window': list(detected_regimes),
            'hit': hit
        })

    return results


def calculate_metrics(hmm_results, baseline_results, lambda_missed=LAMBDA_MISSED, lambda_false=LAMBDA_FALSE):
    """Calculate evaluation metrics for both models."""

    metrics = {}

    for name, results in [('HMM', hmm_results), ('Z-Score', baseline_results)]:
        total = results['hits'] + results['misses']
        hit_rate = results['hits'] / total if total > 0 else 0
        miss_rate = results['misses'] / total if total > 0 else 0

        # Cost-weighted score (lower is better)
        cost = lambda_missed * results['misses'] + lambda_false * 0  # No false alarms in this eval

        metrics[name] = {
            'hits': results['hits'],
            'misses': results['misses'],
            'total': total,
            'hit_rate': hit_rate,
            'miss_rate': miss_rate,
            'cost_weighted_score': cost
        }

    return metrics


# ============================================================
# TRANSITION ANALYSIS
# ============================================================

def analyze_regime_transitions(monthly, model_col='regime_label'):
    """Analyze timing of regime transitions."""
    print(f"\n{'='*80}")
    print("REGIME TRANSITION ANALYSIS")
    print('='*80)

    # Find transition points
    transitions = []
    prev_regime = None

    for idx, row in monthly.iterrows():
        current_regime = row[model_col]
        if prev_regime is not None and current_regime != prev_regime:
            transitions.append({
                'date': row['date'],
                'from': prev_regime,
                'to': current_regime
            })
        prev_regime = current_regime

    print(f"\nTransition Points:")
    for t in transitions:
        print(f"  {t['date'].strftime('%Y-%m')}: {t['from']} → {t['to']}")

    # Calculate lead time to key events
    print(f"\nLead Time Analysis:")
    key_crisis_events = [
        ('2022-03-07', 'FX Float'),
        ('2022-04-12', 'Default'),
    ]

    # Find first STRESS and CRISIS transitions
    first_stress = None
    first_crisis = None

    for t in transitions:
        if t['to'] == 'STRESS' and first_stress is None:
            first_stress = t['date']
        if t['to'] == 'CRISIS' and first_crisis is None:
            first_crisis = t['date']

    for event_date_str, event_name in key_crisis_events:
        event_date = pd.to_datetime(event_date_str)

        if first_stress:
            stress_lead = (event_date - first_stress).days
            print(f"  {event_name}: STRESS detected {stress_lead} days before")

        if first_crisis:
            crisis_lead = (event_date - first_crisis).days
            print(f"  {event_name}: CRISIS detected {crisis_lead} days before")

    return transitions


# ============================================================
# FALSE ALARM ANALYSIS
# ============================================================

def analyze_false_alarms(monthly, model_col='regime_label', events=ALL_EVENTS):
    """
    Analyze potential false alarms - regime changes not associated with events.
    """
    print(f"\n{'='*80}")
    print("FALSE ALARM ANALYSIS")
    print('='*80)

    # Get all transition dates
    transitions = []
    prev_regime = None

    for idx, row in monthly.iterrows():
        current_regime = row[model_col]
        if prev_regime is not None and current_regime != prev_regime:
            transitions.append(row['date'])
        prev_regime = current_regime

    # Check if each transition is near an event
    event_dates = [pd.to_datetime(d) for d in events.keys()]

    false_alarms = []
    justified_transitions = []

    for trans_date in transitions:
        # Check if any event is within 60 days
        near_event = False
        nearest_event = None
        min_dist = float('inf')

        for event_date in event_dates:
            dist = abs((trans_date - event_date).days)
            if dist < min_dist:
                min_dist = dist
                nearest_event = event_date
            if dist <= 60:
                near_event = True

        if near_event:
            justified_transitions.append({
                'transition_date': trans_date,
                'nearest_event': nearest_event,
                'distance_days': min_dist
            })
        else:
            false_alarms.append({
                'transition_date': trans_date,
                'nearest_event': nearest_event,
                'distance_days': min_dist
            })

    print(f"\nTotal transitions: {len(transitions)}")
    print(f"Justified (within 60 days of event): {len(justified_transitions)}")
    print(f"Potential false alarms: {len(false_alarms)}")

    if false_alarms:
        print("\nPotential False Alarms:")
        for fa in false_alarms:
            print(f"  {fa['transition_date'].strftime('%Y-%m')}: "
                  f"nearest event {fa['distance_days']} days away")

    false_alarm_rate = len(false_alarms) / len(transitions) if transitions else 0

    return {
        'total_transitions': len(transitions),
        'justified': len(justified_transitions),
        'false_alarms': len(false_alarms),
        'false_alarm_rate': false_alarm_rate
    }


# ============================================================
# MAIN REPORT
# ============================================================

def generate_validation_report():
    """Generate full validation report."""

    print("=" * 80)
    print("SL-FSI EVENT-ALIGNMENT VALIDATION FRAMEWORK")
    print("=" * 80)

    # Load data
    daily, monthly = load_data()
    features = ['awcmr', 'real_policy_rate', 'gross_reserves_usd_m', 'ncpi_yoy_pct']

    # Fit models
    monthly_hmm, model, state_labels = fit_3state_monthly_hmm(monthly, features)
    monthly_baseline = fit_zscore_baseline(monthly_hmm.copy(), features)

    # Merge baseline results
    monthly_hmm['zscore_regime'] = monthly_baseline['zscore_regime']

    # Evaluate against events
    print(f"\n{'='*80}")
    print("EVENT ALIGNMENT EVALUATION")
    print('='*80)

    # Tactical window (±1 month)
    print(f"\n--- Tactical Window (±{TACTICAL_WINDOW_MONTHS} month) ---")

    hmm_tactical = evaluate_event_alignment(
        monthly_hmm, ALL_EVENTS, 'regime_label', TACTICAL_WINDOW_MONTHS
    )
    baseline_tactical = evaluate_event_alignment(
        monthly_hmm, ALL_EVENTS, 'zscore_regime', TACTICAL_WINDOW_MONTHS
    )

    # Strategic window (±2 months)
    print(f"\n--- Strategic Window (±{STRATEGIC_WINDOW_MONTHS} months) ---")

    hmm_strategic = evaluate_event_alignment(
        monthly_hmm, ALL_EVENTS, 'regime_label', STRATEGIC_WINDOW_MONTHS
    )
    baseline_strategic = evaluate_event_alignment(
        monthly_hmm, ALL_EVENTS, 'zscore_regime', STRATEGIC_WINDOW_MONTHS
    )

    # Calculate metrics
    tactical_metrics = calculate_metrics(hmm_tactical, baseline_tactical)
    strategic_metrics = calculate_metrics(hmm_strategic, baseline_strategic)

    # Print results
    print(f"\n{'='*80}")
    print("RESULTS SUMMARY")
    print('='*80)

    print(f"\n{'Metric':<25} {'HMM (Tactical)':<18} {'Z-Score (Tactical)':<18} {'HMM (Strategic)':<18} {'Z-Score (Strategic)':<18}")
    print("-" * 100)

    print(f"{'Hits':<25} {tactical_metrics['HMM']['hits']:<18} {tactical_metrics['Z-Score']['hits']:<18} {strategic_metrics['HMM']['hits']:<18} {strategic_metrics['Z-Score']['hits']:<18}")
    print(f"{'Misses':<25} {tactical_metrics['HMM']['misses']:<18} {tactical_metrics['Z-Score']['misses']:<18} {strategic_metrics['HMM']['misses']:<18} {strategic_metrics['Z-Score']['misses']:<18}")
    print(f"{'Hit Rate':<25} {tactical_metrics['HMM']['hit_rate']:<18.1%} {tactical_metrics['Z-Score']['hit_rate']:<18.1%} {strategic_metrics['HMM']['hit_rate']:<18.1%} {strategic_metrics['Z-Score']['hit_rate']:<18.1%}")
    print(f"{'Cost-Weighted Score':<25} {tactical_metrics['HMM']['cost_weighted_score']:<18.1f} {tactical_metrics['Z-Score']['cost_weighted_score']:<18.1f} {strategic_metrics['HMM']['cost_weighted_score']:<18.1f} {strategic_metrics['Z-Score']['cost_weighted_score']:<18.1f}")

    # Detailed event results
    print(f"\n{'='*80}")
    print("DETAILED EVENT RESULTS (Strategic Window)")
    print('='*80)

    print(f"\n{'Date':<12} {'Event':<35} {'Expected':<10} {'HMM':<10} {'Z-Score':<10} {'HMM Hit':<10}")
    print("-" * 95)

    for i, detail in enumerate(hmm_strategic['details']):
        baseline_detail = baseline_strategic['details'][i]
        hmm_hit = "✓" if detail['hit'] else "✗"
        zscore_hit = "✓" if baseline_detail['hit'] else "✗"

        print(f"{detail['date']:<12} {detail['name'][:33]:<35} {detail['expected']:<10} {detail['detected']:<10} {baseline_detail['detected']:<10} {hmm_hit:<10}")

    # Transition analysis
    transitions = analyze_regime_transitions(monthly_hmm, 'regime_label')

    # False alarm analysis
    false_alarm_results = analyze_false_alarms(monthly_hmm, 'regime_label')

    # Final summary
    print(f"\n{'='*80}")
    print("VALIDATION SUMMARY")
    print('='*80)

    print(f"""
MODEL PERFORMANCE:
  HMM 3-State Monthly:
    - Strategic Hit Rate: {strategic_metrics['HMM']['hit_rate']:.1%}
    - Tactical Hit Rate: {tactical_metrics['HMM']['hit_rate']:.1%}
    - False Alarm Rate: {false_alarm_results['false_alarm_rate']:.1%}

  Z-Score Baseline:
    - Strategic Hit Rate: {strategic_metrics['Z-Score']['hit_rate']:.1%}
    - Tactical Hit Rate: {tactical_metrics['Z-Score']['hit_rate']:.1%}

COMPARISON:
  HMM vs Z-Score (Strategic): {'+' if strategic_metrics['HMM']['hit_rate'] > strategic_metrics['Z-Score']['hit_rate'] else '-'}{abs(strategic_metrics['HMM']['hit_rate'] - strategic_metrics['Z-Score']['hit_rate']):.1%} hit rate difference

KEY FINDINGS:
  - STRESS regime detected: {transitions[0]['date'].strftime('%Y-%m') if transitions else 'N/A'}
  - CRISIS regime detected: {[t['date'].strftime('%Y-%m') for t in transitions if t['to'] == 'CRISIS'][0] if any(t['to'] == 'CRISIS' for t in transitions) else 'N/A'}
  - Total regime transitions: {len(transitions)}
  - Events evaluated: {len(ALL_EVENTS)}
""")

    # Save results
    results_df = pd.DataFrame(hmm_strategic['details'])
    results_df.to_csv('data/merged/validation_results.csv', index=False)
    print("✓ Saved: data/merged/validation_results.csv")

    monthly_hmm.to_csv('data/merged/monthly_regimes_validated.csv', index=False)
    print("✓ Saved: data/merged/monthly_regimes_validated.csv")

    return {
        'tactical': tactical_metrics,
        'strategic': strategic_metrics,
        'false_alarms': false_alarm_results,
        'transitions': transitions,
        'monthly_data': monthly_hmm
    }


if __name__ == '__main__':
    results = generate_validation_report()
