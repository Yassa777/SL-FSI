#!/usr/bin/env python3
"""
SL-FSI Feature Overlap Analysis
================================
Identifies viable feature combinations for HMM based on actual data coverage.

Run: python feature_overlap_analysis.py
"""

import pandas as pd
import numpy as np
from itertools import combinations
from hmmlearn import hmm
import warnings
warnings.filterwarnings('ignore')

# ============================================================
# Configuration
# ============================================================

# Focus on crisis period for analysis
CRISIS_START = '2020-01-01'
CRISIS_END = '2024-12-31'

# Minimum requirements
MIN_OVERLAP_PCT = 50  # Minimum % of days with all features
MIN_OVERLAP_DAYS = 500  # Minimum absolute days
MIN_FEATURES = 3  # Minimum features for HMM

# Features to analyze (exclude date and identifiers)
EXCLUDE_COLS = ['date']

# ============================================================
# Load Data
# ============================================================

print("=" * 70)
print("SL-FSI FEATURE OVERLAP ANALYSIS")
print("=" * 70)

daily = pd.read_csv('data/merged/slfsi_daily_panel.csv', parse_dates=['date'])

# Filter to crisis period
crisis = daily[(daily['date'] >= CRISIS_START) & (daily['date'] <= CRISIS_END)].copy()
total_days = len(crisis)

print(f"\nAnalysis Period: {CRISIS_START} to {CRISIS_END}")
print(f"Total Days: {total_days:,}")

# ============================================================
# Individual Feature Coverage
# ============================================================

print("\n" + "=" * 70)
print("INDIVIDUAL FEATURE COVERAGE")
print("=" * 70)

# Get numeric columns only
numeric_cols = [col for col in crisis.columns
                if col not in EXCLUDE_COLS
                and pd.api.types.is_numeric_dtype(crisis[col])]

coverage = {}
for col in numeric_cols:
    valid = crisis[col].notna().sum()
    pct = (valid / total_days) * 100
    coverage[col] = {'valid_days': valid, 'pct': pct}

# Sort by coverage
coverage_df = pd.DataFrame(coverage).T
coverage_df = coverage_df.sort_values('pct', ascending=False)

print(f"\n{'Feature':<30} {'Days':>8} {'Coverage':>10}")
print("-" * 50)
for feat, row in coverage_df.iterrows():
    status = "✓" if row['pct'] > 70 else "⚠" if row['pct'] > 40 else "✗"
    print(f"{status} {feat:<28} {int(row['valid_days']):>8} {row['pct']:>9.1f}%")

# ============================================================
# Categorize Features by Type
# ============================================================

FEATURE_CATEGORIES = {
    'FX & Currency': ['usd_lkr', 'r_fx', 'vol_fx_20d', 'reer_index', 'gold_premium_pct', 'implied_fx'],
    'Equity Market': ['aspi', 'sl20_index', 'r_eq', 'vol_eq_20d', 'r_eq_real', 'equity_turnover', 'market_cap', 'turnover_ratio'],
    'Interest Rates': ['awcmr', 'sdfr', 'slfr', 'policy_ceiling', 'tbill_primary', 'tbill_secondary', 'tbond_yield', 'real_policy_rate', 'interbank_spread', 'yield_curve_slope'],
    'External Sector': ['gross_reserves_usd_m', 'reserve_slope_3m', 'import_cover_months', 'tourism_earnings_usd_m', 'remittances_usd_m'],
    'Sovereign Risk': ['isb_yield', 'embi_spread_approx', 'us_10y_yield'],
    'Commodities': ['gold_usd', 'gold_lkr'],
    'Inflation': ['ncpi_yoy_pct']
}

print("\n" + "=" * 70)
print("COVERAGE BY CATEGORY")
print("=" * 70)

for category, features in FEATURE_CATEGORIES.items():
    available = [f for f in features if f in coverage]
    if available:
        avg_coverage = np.mean([coverage[f]['pct'] for f in available])
        good_features = [f for f in available if coverage[f]['pct'] > 50]
        print(f"\n{category}:")
        print(f"  Average coverage: {avg_coverage:.1f}%")
        print(f"  Usable features (>50%): {good_features if good_features else 'None'}")

# ============================================================
# Pairwise Overlap Analysis
# ============================================================

print("\n" + "=" * 70)
print("PAIRWISE OVERLAP MATRIX (Top Features)")
print("=" * 70)

# Focus on features with >30% individual coverage
usable_features = [f for f in coverage if coverage[f]['pct'] > 30]
print(f"\nAnalyzing {len(usable_features)} features with >30% coverage")

# Calculate pairwise overlap
def calculate_overlap(df, feat1, feat2):
    """Calculate % of days where both features have values"""
    both_valid = df[[feat1, feat2]].dropna()
    return len(both_valid)

overlap_matrix = pd.DataFrame(index=usable_features, columns=usable_features, dtype=float)
for f1 in usable_features:
    for f2 in usable_features:
        overlap_matrix.loc[f1, f2] = calculate_overlap(crisis, f1, f2)

# Show as percentage of total days
overlap_pct = (overlap_matrix / total_days * 100).round(1)

# Print top 15 features
top_features = coverage_df.head(15).index.tolist()
top_features = [f for f in top_features if f in usable_features]

print("\nPairwise Overlap (% of crisis period):")
print(overlap_pct.loc[top_features[:10], top_features[:10]].to_string())

# ============================================================
# Find Viable Feature Combinations
# ============================================================

print("\n" + "=" * 70)
print("VIABLE FEATURE COMBINATIONS FOR HMM")
print("=" * 70)

def calculate_combo_overlap(df, features):
    """Calculate overlap for a combination of features"""
    subset = df[list(features)].dropna()
    return len(subset), len(subset) / len(df) * 100

# Test combinations of 3, 4, 5 features
viable_combos = []

# Start with high-coverage features
high_coverage = [f for f in coverage if coverage[f]['pct'] > 50]
print(f"\nHigh-coverage features (>50%): {len(high_coverage)}")
print(f"  {high_coverage}")

# Test 3-feature combinations
print("\n--- Testing 3-Feature Combinations ---")
for combo in combinations(high_coverage, 3):
    days, pct = calculate_combo_overlap(crisis, combo)
    if pct >= MIN_OVERLAP_PCT and days >= MIN_OVERLAP_DAYS:
        viable_combos.append({
            'features': combo,
            'n_features': 3,
            'overlap_days': days,
            'overlap_pct': pct
        })

# Test 4-feature combinations
print("--- Testing 4-Feature Combinations ---")
for combo in combinations(high_coverage, 4):
    days, pct = calculate_combo_overlap(crisis, combo)
    if pct >= MIN_OVERLAP_PCT and days >= MIN_OVERLAP_DAYS:
        viable_combos.append({
            'features': combo,
            'n_features': 4,
            'overlap_days': days,
            'overlap_pct': pct
        })

# Test 5-feature combinations
print("--- Testing 5-Feature Combinations ---")
for combo in combinations(high_coverage, 5):
    days, pct = calculate_combo_overlap(crisis, combo)
    if pct >= MIN_OVERLAP_PCT and days >= MIN_OVERLAP_DAYS:
        viable_combos.append({
            'features': combo,
            'n_features': 5,
            'overlap_days': days,
            'overlap_pct': pct
        })

# Sort by overlap
viable_combos = sorted(viable_combos, key=lambda x: (-x['overlap_pct'], -x['n_features']))

print(f"\nFound {len(viable_combos)} viable combinations (>={MIN_OVERLAP_PCT}% overlap, >={MIN_OVERLAP_DAYS} days)")

# ============================================================
# Best Combinations by Category Diversity
# ============================================================

def categorize_features(features):
    """Return which categories are represented"""
    cats = set()
    for feat in features:
        for cat, feats in FEATURE_CATEGORIES.items():
            if feat in feats:
                cats.add(cat)
    return cats

print("\n" + "=" * 70)
print("TOP VIABLE COMBINATIONS (Ranked by Overlap)")
print("=" * 70)

# Show top 20
for i, combo in enumerate(viable_combos[:20]):
    cats = categorize_features(combo['features'])
    print(f"\n{i+1}. {combo['features']}")
    print(f"   Overlap: {combo['overlap_days']} days ({combo['overlap_pct']:.1f}%)")
    print(f"   Categories: {cats}")

# ============================================================
# Recommended Feature Sets
# ============================================================

print("\n" + "=" * 70)
print("RECOMMENDED FEATURE SETS")
print("=" * 70)

# Find best combo with most category diversity
def score_combo(combo):
    """Score = overlap_pct * (1 + 0.1 * n_categories)"""
    cats = len(categorize_features(combo['features']))
    return combo['overlap_pct'] * (1 + 0.1 * cats)

scored_combos = [(c, score_combo(c)) for c in viable_combos]
scored_combos = sorted(scored_combos, key=lambda x: -x[1])

print("\n### BEST OVERALL (Overlap + Diversity Score) ###")
for i, (combo, score) in enumerate(scored_combos[:5]):
    cats = categorize_features(combo['features'])
    print(f"\n{i+1}. Score: {score:.1f}")
    print(f"   Features: {combo['features']}")
    print(f"   Overlap: {combo['overlap_days']} days ({combo['overlap_pct']:.1f}%)")
    print(f"   Categories ({len(cats)}): {cats}")

# ============================================================
# Test HMM on Best Combinations
# ============================================================

print("\n" + "=" * 70)
print("HMM TESTING ON TOP COMBINATIONS")
print("=" * 70)

def test_hmm(df, features, n_states=3, n_iter=100):
    """Test HMM fit and return basic diagnostics"""
    # Prepare data
    data = df[['date'] + list(features)].dropna()
    X = data[list(features)].values

    # Standardize
    X_mean = X.mean(axis=0)
    X_std = X.std(axis=0)
    X_scaled = (X - X_mean) / (X_std + 1e-8)

    # Fit HMM
    model = hmm.GaussianHMM(
        n_components=n_states,
        covariance_type="full",
        n_iter=n_iter,
        random_state=42
    )

    model.fit(X_scaled)
    states = model.predict(X_scaled)

    # Calculate diagnostics
    log_likelihood = model.score(X_scaled)

    # State distribution
    state_counts = np.bincount(states, minlength=n_states)
    state_pcts = state_counts / len(states) * 100

    # Transition matrix
    trans_mat = model.transmat_

    # Check for degenerate states (states with <5% of data)
    degenerate = np.sum(state_pcts < 5)

    return {
        'n_observations': len(data),
        'log_likelihood': log_likelihood,
        'aic': -2 * log_likelihood + 2 * (n_states * len(features) + n_states * n_states),
        'state_distribution': state_pcts,
        'degenerate_states': degenerate,
        'converged': model.monitor_.converged,
        'dates': data['date'].values,
        'states': states,
        'model': model
    }

# Test top 5 combinations with 2, 3, and 4 states
test_results = []

for combo, score in scored_combos[:5]:
    print(f"\nTesting: {combo['features']}")
    print(f"  Overlap: {combo['overlap_days']} days")

    for n_states in [2, 3]:
        try:
            result = test_hmm(crisis, combo['features'], n_states=n_states)
            result['features'] = combo['features']
            result['n_states'] = n_states
            result['overlap_pct'] = combo['overlap_pct']
            test_results.append(result)

            print(f"  {n_states}-state: LL={result['log_likelihood']:.1f}, "
                  f"AIC={result['aic']:.1f}, "
                  f"Converged={result['converged']}, "
                  f"Degen={result['degenerate_states']}")
            print(f"    State dist: {result['state_distribution'].round(1)}")
        except Exception as e:
            print(f"  {n_states}-state: FAILED - {e}")

# ============================================================
# Select Best Configuration
# ============================================================

print("\n" + "=" * 70)
print("BEST HMM CONFIGURATIONS")
print("=" * 70)

# Filter to good results (converged, no degenerate states)
good_results = [r for r in test_results if r['converged'] and r['degenerate_states'] == 0]

if good_results:
    # Sort by AIC (lower is better)
    good_results = sorted(good_results, key=lambda x: x['aic'])

    print("\nTop configurations by AIC:")
    for i, r in enumerate(good_results[:5]):
        print(f"\n{i+1}. Features: {r['features']}")
        print(f"   States: {r['n_states']}, AIC: {r['aic']:.1f}")
        print(f"   Observations: {r['n_observations']}, Overlap: {r['overlap_pct']:.1f}%")
        print(f"   State distribution: {r['state_distribution'].round(1)}")

# ============================================================
# Export Best Configuration
# ============================================================

print("\n" + "=" * 70)
print("RECOMMENDED WORKING FEATURE SET")
print("=" * 70)

if good_results:
    best = good_results[0]

    print(f"""
RECOMMENDED CONFIGURATION:
==========================
Features: {list(best['features'])}
Number of States: {best['n_states']}
Overlap: {best['overlap_pct']:.1f}% ({best['n_observations']} days)

State Distribution:
{' | '.join([f'State {i}: {p:.1f}%' for i, p in enumerate(best['state_distribution'])])}

Why this configuration:
- Best AIC score among converged models
- No degenerate states (all states have >5% of observations)
- Sufficient temporal coverage for meaningful analysis
""")

    # Save regime assignments
    regime_df = pd.DataFrame({
        'date': best['dates'],
        'regime': best['states']
    })
    regime_df.to_csv('data/merged/hmm_regimes_working.csv', index=False)
    print("Saved: data/merged/hmm_regimes_working.csv")

# ============================================================
# Summary Report
# ============================================================

print("\n" + "=" * 70)
print("SUMMARY")
print("=" * 70)

print(f"""
DATA QUALITY:
- Crisis period: {CRISIS_START} to {CRISIS_END} ({total_days} days)
- Features with >70% coverage: {len([f for f in coverage if coverage[f]['pct'] > 70])}
- Features with >50% coverage: {len([f for f in coverage if coverage[f]['pct'] > 50])}
- Features with >30% coverage: {len([f for f in coverage if coverage[f]['pct'] > 30])}

VIABLE COMBINATIONS:
- Total viable (>={MIN_OVERLAP_PCT}% overlap): {len(viable_combos)}
- HMM configurations tested: {len(test_results)}
- Successful configurations: {len(good_results)}

KEY FINDINGS:
- Monthly macro features (reserves, inflation, policy) have 100% coverage (forward-filled)
- Daily market features (FX, equity) have 50-65% coverage
- Interbank/ISB features have <15% coverage - NOT VIABLE
- Best combinations use mix of forward-filled macro + equity volatility
""")

# Final recommendation
if good_results:
    best = good_results[0]
    print(f"""
FINAL RECOMMENDATION:
Use these {len(best['features'])} features for HMM analysis:
{chr(10).join(['  - ' + f for f in best['features']])}

With {best['n_states']} regimes, giving:
  - {best['n_observations']} overlapping observations
  - {best['overlap_pct']:.1f}% coverage of crisis period
  - Well-distributed states (no degenerate regimes)
""")
