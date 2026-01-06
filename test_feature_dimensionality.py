#!/usr/bin/env python3
"""
Empirical Test: Impact of Feature Count on HMM Performance
===========================================================
Tests what happens when we add more features to the model.

Run: python test_feature_dimensionality.py
"""

import pandas as pd
import numpy as np
from hmmlearn import hmm
from sklearn.metrics import silhouette_score
import warnings
warnings.filterwarnings('ignore')

print("=" * 70)
print("FEATURE DIMENSIONALITY TEST")
print("=" * 70)

# ============================================================
# Load Data
# ============================================================

panel = pd.read_csv('data/merged/slfsi_daily_panel.csv', parse_dates=['date'])

# Convert to monthly (genuine observations, not forward-filled)
monthly = panel.set_index('date').groupby(pd.Grouper(freq='MS')).first().reset_index()

print(f"\nMonthly observations: {len(monthly)}")

# ============================================================
# Define Feature Sets of Increasing Size
# ============================================================

feature_sets = {
    '4_features': [
        'awcmr', 'real_policy_rate', 'gross_reserves_usd_m', 'ncpi_yoy_pct'
    ],
    '6_features': [
        'awcmr', 'real_policy_rate', 'gross_reserves_usd_m', 'ncpi_yoy_pct',
        'vol_eq_20d', 'usd_lkr'  # Add equity vol, FX rate
    ],
    '8_features': [
        'awcmr', 'real_policy_rate', 'gross_reserves_usd_m', 'ncpi_yoy_pct',
        'vol_eq_20d', 'usd_lkr',
        'tbill_secondary', 'aspi'  # Add t-bill rate, equity index
    ],
    '10_features': [
        'awcmr', 'real_policy_rate', 'gross_reserves_usd_m', 'ncpi_yoy_pct',
        'vol_eq_20d', 'usd_lkr', 'tbill_secondary', 'aspi',
        'sdfr', 'slfr'  # Add standing facility rates
    ]
}

# ============================================================
# Test Each Feature Set
# ============================================================

results = []

for name, features in feature_sets.items():
    print(f"\n{'='*70}")
    print(f"Testing: {name.upper()}")
    print(f"{'='*70}")

    # Check coverage
    available_features = [f for f in features if f in monthly.columns]
    missing = set(features) - set(available_features)

    if missing:
        print(f"⚠ Missing features: {missing}")
        print("Skipping this set.")
        continue

    # Extract data
    X = monthly[available_features].values

    # Check missing values
    n_missing = np.isnan(X).sum()
    coverage = 1 - (n_missing / X.size)
    print(f"Coverage: {coverage*100:.1f}%")

    if coverage < 0.8:
        print("⚠ Insufficient coverage. Skipping.")
        continue

    # Handle remaining NaN (forward fill)
    for i in range(X.shape[1]):
        col = X[:, i]
        mask = np.isnan(col)
        if mask.any():
            idx = np.where(~mask)[0]
            if len(idx) > 0:
                X[mask, i] = np.interp(np.where(mask)[0], idx, col[idx])

    # Scale
    X_scaled = (X - X.mean(axis=0)) / X.std(axis=0)

    # Parameter count
    n_features = len(available_features)
    n_obs = len(X)
    n_params = 3 * (n_features + n_features) + 9  # diagonal covariance
    obs_per_param = n_obs / n_params

    print(f"\nModel dimensions:")
    print(f"  Features: {n_features}")
    print(f"  Observations: {n_obs}")
    print(f"  Parameters: {n_params}")
    print(f"  Obs/Param ratio: {obs_per_param:.2f}")

    # Fit with multiple seeds
    scores = []
    silhouettes = []
    n_transitions_list = []
    convergence_count = 0

    for seed in range(5):
        try:
            model = hmm.GaussianHMM(
                n_components=3,
                covariance_type="diag",
                n_iter=300,
                random_state=seed
            )
            model.fit(X_scaled)

            if model.monitor_.converged:
                convergence_count += 1

            states = model.predict(X_scaled)
            score = model.score(X_scaled)
            scores.append(score)

            n_transitions = (np.diff(states) != 0).sum()
            n_transitions_list.append(n_transitions)

            if len(np.unique(states)) > 1:
                sil = silhouette_score(X_scaled, states)
                silhouettes.append(sil)

        except Exception as e:
            print(f"  Seed {seed} failed: {e}")

    # BIC
    avg_score = np.mean(scores) if scores else np.nan
    bic = -2 * avg_score + n_params * np.log(n_obs) if not np.isnan(avg_score) else np.nan

    # Results
    result = {
        'name': name,
        'n_features': n_features,
        'obs_per_param': obs_per_param,
        'convergence_rate': convergence_count / 5,
        'avg_loglik': avg_score,
        'bic': bic,
        'avg_silhouette': np.mean(silhouettes) if silhouettes else np.nan,
        'avg_transitions': np.mean(n_transitions_list) if n_transitions_list else np.nan
    }
    results.append(result)

    print(f"\nResults:")
    print(f"  Convergence rate: {result['convergence_rate']*100:.0f}%")
    print(f"  Avg log-likelihood: {result['avg_loglik']:.1f}")
    print(f"  BIC: {result['bic']:.0f}")
    print(f"  Avg silhouette: {result['avg_silhouette']:.3f}")
    print(f"  Avg transitions: {result['avg_transitions']:.1f}")

# ============================================================
# Summary Comparison
# ============================================================

print("\n" + "=" * 70)
print("SUMMARY COMPARISON")
print("=" * 70)

df_results = pd.DataFrame(results)

if len(df_results) > 0:
    print("\n" + df_results.to_string(index=False))

    # Find best by BIC
    best_idx = df_results['bic'].idxmin()
    best = df_results.loc[best_idx]

    print(f"\n→ Best by BIC: {best['name']} ({best['n_features']} features)")
    print(f"  BIC: {best['bic']:.0f}")

    # Diminishing returns analysis
    if len(df_results) > 1:
        print("\nDiminishing Returns Analysis:")
        df_sorted = df_results.sort_values('n_features')

        for i in range(1, len(df_sorted)):
            prev = df_sorted.iloc[i-1]
            curr = df_sorted.iloc[i]

            feature_increase = curr['n_features'] - prev['n_features']
            bic_change = curr['bic'] - prev['bic']
            sil_change = curr['avg_silhouette'] - prev['avg_silhouette']

            print(f"\n  {prev['name']} → {curr['name']}:")
            print(f"    +{feature_increase} features")
            print(f"    BIC change: {bic_change:+.0f} {'(better)' if bic_change < 0 else '(worse)'}")
            print(f"    Silhouette change: {sil_change:+.3f}")

# ============================================================
# Interpretation
# ============================================================

print("\n" + "=" * 70)
print("INTERPRETATION")
print("=" * 70)

print("""
KEY INSIGHTS:

1. CONVERGENCE RATE:
   - If <80%: Model is unstable with this many features
   - High-dimensional models may not converge reliably

2. BIC (Lower is better):
   - Penalizes model complexity
   - Shows trade-off between fit and parsimony

3. SILHOUETTE SCORE (Higher is better):
   - Measures how well-separated regimes are
   - Score <0.3: Poor separation
   - Score >0.5: Good separation

4. TRANSITIONS:
   - More features may reduce or increase transitions
   - Fewer transitions = cleaner regime timeline

5. OBS/PARAM RATIO:
   - <1: Severe overfitting risk
   - 1-2: Caution needed
   - >2: Generally safe

RECOMMENDATION:
Choose the model with:
- BIC close to minimum
- Obs/Param ratio >1.5
- High convergence rate
- Interpretable features
""")

print("\n" + "=" * 70)
print("TEST COMPLETE")
print("=" * 70)
