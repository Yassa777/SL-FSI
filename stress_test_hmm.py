#!/usr/bin/env python3
"""
HMM STRESS TEST: How Robust Are Our Claims?
============================================
Tests:
1. Sensitivity to random seed
2. Sensitivity to initialization
3. How much does regime assignment change?
4. Is 3-state model actually better than 2-state?
5. What happens with corrected (World Bank) data?

Run: python stress_test_hmm.py
"""

import pandas as pd
import numpy as np
from hmmlearn import hmm
from sklearn.metrics import silhouette_score
import warnings
warnings.filterwarnings('ignore')

print("=" * 70)
print("HMM STRESS TEST: ROBUSTNESS ANALYSIS")
print("=" * 70)

# ============================================================
# Load Data
# ============================================================

pk = pd.read_csv('data/cross_country/pakistan_monthly_enhanced.csv', parse_dates=['date'])
gh = pd.read_csv('data/cross_country/ghana_monthly_enhanced.csv', parse_dates=['date'])

# Features
FEATURES_PK = ['kibor', 'real_policy_rate', 'reserves_usd_m', 'inflation_yoy']
FEATURES_GH = ['interbank_rate', 'real_policy_rate', 'reserves_usd_m', 'inflation_yoy']

# ============================================================
# TEST 1: Sensitivity to Random Seed
# ============================================================

print("\n" + "=" * 70)
print("TEST 1: RANDOM SEED SENSITIVITY")
print("=" * 70)
print("\nRunning 3-state HMM with 10 different random seeds...")

def fit_hmm_with_seed(X, n_states, seed):
    X_scaled = (X - X.mean(axis=0)) / X.std(axis=0)
    model = hmm.GaussianHMM(
        n_components=n_states,
        covariance_type="diag",
        n_iter=300,
        random_state=seed
    )
    model.fit(X_scaled)
    states = model.predict(X_scaled)
    return states, model.score(X_scaled)

# Pakistan
X_pk = pk[FEATURES_PK].values
pk_results = []
for seed in range(10):
    states, score = fit_hmm_with_seed(X_pk, 3, seed)
    pk_results.append({
        'seed': seed,
        'score': score,
        'n_transitions': (np.diff(states) != 0).sum(),
        'state_0_pct': (states == 0).mean() * 100,
        'state_1_pct': (states == 1).mean() * 100,
        'state_2_pct': (states == 2).mean() * 100
    })

pk_df = pd.DataFrame(pk_results)
print("\nPAKISTAN - 3-state HMM across 10 seeds:")
print(f"  Log-likelihood range: {pk_df['score'].min():.1f} to {pk_df['score'].max():.1f}")
print(f"  Transitions range: {pk_df['n_transitions'].min()} to {pk_df['n_transitions'].max()}")
print(f"  State 0 % range: {pk_df['state_0_pct'].min():.0f}% to {pk_df['state_0_pct'].max():.0f}%")
print(f"  State 1 % range: {pk_df['state_1_pct'].min():.0f}% to {pk_df['state_1_pct'].max():.0f}%")
print(f"  State 2 % range: {pk_df['state_2_pct'].min():.0f}% to {pk_df['state_2_pct'].max():.0f}%")

# How stable are the assignments?
all_states_pk = []
for seed in range(10):
    states, _ = fit_hmm_with_seed(X_pk, 3, seed)
    all_states_pk.append(states)

all_states_pk = np.array(all_states_pk)  # 10 x 60 matrix
mode_states = np.apply_along_axis(lambda x: np.bincount(x, minlength=3).argmax(), 0, all_states_pk)
agreement = np.mean([np.mean(s == mode_states) for s in all_states_pk]) * 100
print(f"\n  Cross-seed agreement: {agreement:.1f}%")
if agreement < 70:
    print("  ⚠ WARNING: Model is UNSTABLE across seeds")
elif agreement < 85:
    print("  ⚠ MODERATE stability")
else:
    print("  ✓ Good stability")

# Ghana
X_gh = gh[FEATURES_GH].values
gh_results = []
for seed in range(10):
    states, score = fit_hmm_with_seed(X_gh, 3, seed)
    gh_results.append({
        'seed': seed,
        'score': score,
        'n_transitions': (np.diff(states) != 0).sum(),
        'state_0_pct': (states == 0).mean() * 100,
        'state_1_pct': (states == 1).mean() * 100,
        'state_2_pct': (states == 2).mean() * 100
    })

gh_df = pd.DataFrame(gh_results)
print("\nGHANA - 3-state HMM across 10 seeds:")
print(f"  Log-likelihood range: {gh_df['score'].min():.1f} to {gh_df['score'].max():.1f}")
print(f"  Transitions range: {gh_df['n_transitions'].min()} to {gh_df['n_transitions'].max()}")

all_states_gh = []
for seed in range(10):
    states, _ = fit_hmm_with_seed(X_gh, 3, seed)
    all_states_gh.append(states)

all_states_gh = np.array(all_states_gh)
mode_states_gh = np.apply_along_axis(lambda x: np.bincount(x, minlength=3).argmax(), 0, all_states_gh)
agreement_gh = np.mean([np.mean(s == mode_states_gh) for s in all_states_gh]) * 100
print(f"\n  Cross-seed agreement: {agreement_gh:.1f}%")
if agreement_gh < 70:
    print("  ⚠ WARNING: Model is UNSTABLE across seeds")
elif agreement_gh < 85:
    print("  ⚠ MODERATE stability")
else:
    print("  ✓ Good stability")

# ============================================================
# TEST 2: 2-State vs 3-State Model Comparison
# ============================================================

print("\n\n" + "=" * 70)
print("TEST 2: IS 3-STATE ACTUALLY BETTER THAN 2-STATE?")
print("=" * 70)

def compare_models(X, name):
    X_scaled = (X - X.mean(axis=0)) / X.std(axis=0)

    results = []
    for n_states in [2, 3, 4]:
        scores = []
        silhouettes = []
        transitions = []

        for seed in range(5):
            model = hmm.GaussianHMM(
                n_components=n_states,
                covariance_type="diag",
                n_iter=300,
                random_state=seed
            )
            model.fit(X_scaled)
            states = model.predict(X_scaled)

            scores.append(model.score(X_scaled))
            transitions.append((np.diff(states) != 0).sum())

            # Silhouette score (only if states vary)
            if len(np.unique(states)) > 1:
                silhouettes.append(silhouette_score(X_scaled, states))
            else:
                silhouettes.append(np.nan)

        # BIC approximation (penalize complexity)
        n_params = n_states * (4 + 4 + n_states)  # means, diag cov, transition matrix
        bic = -2 * np.mean(scores) + n_params * np.log(len(X))

        results.append({
            'n_states': n_states,
            'avg_score': np.mean(scores),
            'avg_silhouette': np.nanmean(silhouettes),
            'avg_transitions': np.mean(transitions),
            'bic': bic
        })

    return pd.DataFrame(results)

print("\nPAKISTAN:")
pk_model_compare = compare_models(X_pk, 'Pakistan')
print(pk_model_compare.to_string(index=False))
best_pk = pk_model_compare.loc[pk_model_compare['bic'].idxmin(), 'n_states']
print(f"\n→ Best by BIC: {int(best_pk)}-state model")
if best_pk != 3:
    print("  ⚠ 3-state may NOT be optimal for Pakistan!")

print("\nGHANA:")
gh_model_compare = compare_models(X_gh, 'Ghana')
print(gh_model_compare.to_string(index=False))
best_gh = gh_model_compare.loc[gh_model_compare['bic'].idxmin(), 'n_states']
print(f"\n→ Best by BIC: {int(best_gh)}-state model")
if best_gh != 3:
    print("  ⚠ 3-state may NOT be optimal for Ghana!")

# ============================================================
# TEST 3: What if we correct the data?
# ============================================================

print("\n\n" + "=" * 70)
print("TEST 3: IMPACT OF DATA CORRECTION")
print("=" * 70)

# Create "corrected" datasets using World Bank annual values
# Scale our monthly estimates to match annual totals

print("\nApplying World Bank scaling corrections...")

# Ghana correction (biggest issue)
gh_corrected = gh.copy()
# 2022: actual $5.2B, our estimate avg ~$7.3B → scale by 0.71
# 2023: actual $3.6B, our estimate avg ~$5.6B → scale by 0.65
for year, scale in [(2022, 5205/7275), (2023, 3624/5571)]:
    mask = gh_corrected['date'].dt.year == year
    gh_corrected.loc[mask, 'reserves_usd_m'] *= scale

X_gh_corrected = gh_corrected[FEATURES_GH].values

# Compare regime assignments
_, original_score = fit_hmm_with_seed(X_gh, 3, 42)
states_original, _ = fit_hmm_with_seed(X_gh, 3, 42)
states_corrected, corrected_score = fit_hmm_with_seed(X_gh_corrected, 3, 42)

agreement_correction = np.mean(states_original == states_corrected) * 100

print(f"\nGHANA - Original vs Corrected Data:")
print(f"  Regime assignment agreement: {agreement_correction:.1f}%")
print(f"  Original score: {original_score:.1f}")
print(f"  Corrected score: {corrected_score:.1f}")

if agreement_correction < 80:
    print("\n  ⚠ WARNING: Data correction SIGNIFICANTLY changes regime assignments!")
    print("     This means our results are SENSITIVE to data quality.")
else:
    print("\n  ✓ Results relatively robust to data correction")

# ============================================================
# TEST 4: Can the model actually distinguish regimes?
# ============================================================

print("\n\n" + "=" * 70)
print("TEST 4: DO THE REGIMES ACTUALLY DIFFER?")
print("=" * 70)

def analyze_regime_separation(df, features, states, name):
    print(f"\n{name}:")

    # Means by regime
    df_temp = df.copy()
    df_temp['state'] = states

    means = df_temp.groupby('state')[features].mean()
    print("\nMeans by regime:")
    print(means.round(1).to_string())

    # T-tests between regimes
    from scipy import stats

    print("\nT-test p-values (state 0 vs state 2):")
    for feat in features:
        s0 = df_temp[df_temp['state'] == 0][feat].values
        s2 = df_temp[df_temp['state'] == 2][feat].values
        if len(s0) > 0 and len(s2) > 0:
            _, p = stats.ttest_ind(s0, s2)
            sig = "***" if p < 0.001 else "**" if p < 0.01 else "*" if p < 0.05 else "n.s."
            print(f"  {feat:25s}: p = {p:.4f} {sig}")

states_pk, _ = fit_hmm_with_seed(X_pk, 3, 42)
states_gh, _ = fit_hmm_with_seed(X_gh, 3, 42)

analyze_regime_separation(pk, FEATURES_PK, states_pk, "PAKISTAN")
analyze_regime_separation(gh, FEATURES_GH, states_gh, "GHANA")

# ============================================================
# FINAL ASSESSMENT
# ============================================================

print("\n\n" + "=" * 70)
print("STRESS TEST SUMMARY")
print("=" * 70)

print(f"""
ROBUSTNESS ASSESSMENT:

1. SEED STABILITY:
   Pakistan: {agreement:.0f}% agreement across seeds {"- UNSTABLE" if agreement < 70 else "- MODERATE" if agreement < 85 else "- STABLE"}
   Ghana:    {agreement_gh:.0f}% agreement across seeds {"- UNSTABLE" if agreement_gh < 70 else "- MODERATE" if agreement_gh < 85 else "- STABLE"}

2. MODEL SELECTION:
   Pakistan: Best model is {int(best_pk)}-state {"(matches our choice!)" if best_pk == 3 else "(NOT 3-state!)"}
   Ghana:    Best model is {int(best_gh)}-state {"(matches our choice!)" if best_gh == 3 else "(NOT 3-state!)"}

3. DATA SENSITIVITY:
   Ghana regime change on correction: {100-agreement_correction:.0f}% of observations differ
   {"→ HIGH sensitivity to data quality" if agreement_correction < 80 else "→ Moderate sensitivity"}

CONCLUSION:
""")

issues = 0
if agreement < 70 or agreement_gh < 70:
    print("  ⚠ Model instability across random initializations")
    issues += 1
if best_pk != 3 or best_gh != 3:
    print("  ⚠ 3-state model may not be optimal (BIC suggests otherwise)")
    issues += 1
if agreement_correction < 80:
    print("  ⚠ Results highly sensitive to data quality corrections")
    issues += 1

if issues == 0:
    print("  ✓ Model appears robust (but data quality still a concern)")
else:
    print(f"\n  {issues} significant robustness issue(s) identified.")
    print("  The 'methodology generalizes' claim needs qualification.")

print("\n" + "=" * 70)
print("STRESS TEST COMPLETE")
print("=" * 70)
