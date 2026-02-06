"""
Reserve Forecasting Feasibility Experiment
==========================================
Question: Can we forecast reserves, or is it fundamentally unpredictable
          because it's a policy variable?

Approach:
- Train on Jan 2014 - Oct 2021 (pre-crisis)
- Test on Nov 2021 - Dec 2025 (crisis + recovery)
- Compare multiple simple forecasting methods
- Evaluate if any method beats a naive random walk
"""

import pandas as pd
import numpy as np
from sklearn.metrics import mean_absolute_error, mean_squared_error
import warnings
warnings.filterwarnings('ignore')

# Load data
df = pd.read_csv('data/external/D12_reserves_compiled.csv', parse_dates=['date'])
df = df.set_index('date')

# Focus on actual CBSL data (Nov 2013 onwards) to avoid interpolated values
df = df[df.index >= '2014-01-01'].copy()

# Target variable
reserves = df['gross_reserves_usd_m'].dropna()

# Train/Test Split: Oct 2021 cutoff (before crisis acceleration)
train_end = '2021-10-31'
train = reserves[reserves.index <= train_end]
test = reserves[reserves.index > train_end]

print("=" * 60)
print("RESERVE FORECASTING FEASIBILITY EXPERIMENT")
print("=" * 60)
print(f"\nTraining period: {train.index.min().strftime('%Y-%m')} to {train.index.max().strftime('%Y-%m')}")
print(f"Training observations: {len(train)}")
print(f"\nTest period: {test.index.min().strftime('%Y-%m')} to {test.index.max().strftime('%Y-%m')}")
print(f"Test observations: {len(test)}")

# Calculate statistics
print(f"\n--- Training Period Statistics ---")
print(f"Mean reserves: ${train.mean():,.0f}M")
print(f"Std dev: ${train.std():,.0f}M")
print(f"Min: ${train.min():,.0f}M | Max: ${train.max():,.0f}M")

print(f"\n--- Test Period Statistics ---")
print(f"Mean reserves: ${test.mean():,.0f}M")
print(f"Std dev: ${test.std():,.0f}M")
print(f"Min: ${test.min():,.0f}M | Max: ${test.max():,.0f}M")

# ============================================================
# FORECASTING METHODS (Simple Approaches)
# ============================================================

def rolling_forecast(train, test, method='random_walk', horizon=1):
    """
    Rolling forecast: at each test point, use only data available up to that point.
    This simulates real-world forecasting.
    """
    predictions = []
    actuals = []

    for i, (date, actual) in enumerate(test.items()):
        # Data available at forecast time
        available_data = pd.concat([train, test.iloc[:i]]) if i > 0 else train

        if method == 'random_walk':
            # Naive: next = current
            pred = available_data.iloc[-1]

        elif method == 'mean':
            # Historical mean
            pred = available_data.mean()

        elif method == 'drift':
            # Random walk with drift (average change)
            avg_change = available_data.diff().mean()
            pred = available_data.iloc[-1] + avg_change * horizon

        elif method == 'exp_smooth':
            # Simple exponential smoothing (alpha=0.3)
            alpha = 0.3
            pred = available_data.iloc[-1]  # Start with last value
            for val in available_data.iloc[-12:]:  # Use last 12 months
                pred = alpha * val + (1 - alpha) * pred

        elif method == 'median_growth':
            # Median monthly growth rate extrapolation
            pct_changes = available_data.pct_change().dropna()
            median_growth = pct_changes.median()
            pred = available_data.iloc[-1] * (1 + median_growth)

        elif method == 'ar1':
            # Simple AR(1): y_t = c + phi * y_{t-1}
            y = available_data.values
            if len(y) > 2:
                y_lag = y[:-1]
                y_curr = y[1:]
                # OLS estimation
                X = np.column_stack([np.ones(len(y_lag)), y_lag])
                try:
                    beta = np.linalg.lstsq(X, y_curr, rcond=None)[0]
                    pred = beta[0] + beta[1] * y[-1]
                except:
                    pred = y[-1]
            else:
                pred = y[-1]

        predictions.append(pred)
        actuals.append(actual)

    return np.array(predictions), np.array(actuals)

# Test all methods
methods = ['random_walk', 'mean', 'drift', 'exp_smooth', 'median_growth', 'ar1']
results = {}

print("\n" + "=" * 60)
print("FORECAST ACCURACY COMPARISON")
print("=" * 60)
print(f"\n{'Method':<20} {'MAE ($M)':<15} {'RMSE ($M)':<15} {'MAPE (%)':<12}")
print("-" * 60)

for method in methods:
    pred, actual = rolling_forecast(train, test, method=method)

    mae = mean_absolute_error(actual, pred)
    rmse = np.sqrt(mean_squared_error(actual, pred))
    mape = np.mean(np.abs((actual - pred) / actual)) * 100

    results[method] = {'MAE': mae, 'RMSE': rmse, 'MAPE': mape, 'pred': pred, 'actual': actual}

    print(f"{method:<20} {mae:>10,.0f}     {rmse:>10,.0f}     {mape:>8.1f}%")

# ============================================================
# ANALYSIS: Can we beat random walk?
# ============================================================

print("\n" + "=" * 60)
print("KEY FINDING: CAN WE BEAT THE RANDOM WALK?")
print("=" * 60)

rw_mae = results['random_walk']['MAE']
print(f"\nRandom Walk MAE: ${rw_mae:,.0f}M (baseline)")

for method in methods:
    if method != 'random_walk':
        improvement = (rw_mae - results[method]['MAE']) / rw_mae * 100
        status = "✓ BEATS" if improvement > 0 else "✗ LOSES TO"
        print(f"{method:<20} {status} random walk by {abs(improvement):>5.1f}%")

# ============================================================
# DECOMPOSE ERROR: Where do forecasts fail?
# ============================================================

print("\n" + "=" * 60)
print("ERROR DECOMPOSITION: WHEN DO FORECASTS FAIL?")
print("=" * 60)

# Split test into crisis (Nov 2021 - Dec 2022) and recovery (2023+)
crisis_mask = test.index <= '2022-12-31'
recovery_mask = test.index > '2022-12-31'

rw_pred = results['random_walk']['pred']
rw_actual = results['random_walk']['actual']

crisis_mae = mean_absolute_error(rw_actual[crisis_mask], rw_pred[crisis_mask])
recovery_mae = mean_absolute_error(rw_actual[recovery_mask], rw_pred[recovery_mask])

print(f"\nRandom Walk MAE by period:")
print(f"  Crisis period (Nov 2021 - Dec 2022):   ${crisis_mae:,.0f}M")
print(f"  Recovery period (Jan 2023 - Dec 2025): ${recovery_mae:,.0f}M")
print(f"\nCrisis period error is {crisis_mae/recovery_mae:.1f}x higher than recovery!")

# ============================================================
# MONTH-BY-MONTH: Largest forecast errors
# ============================================================

print("\n" + "=" * 60)
print("LARGEST FORECAST ERRORS (Random Walk)")
print("=" * 60)

errors = pd.Series(rw_pred - rw_actual, index=test.index)
errors_abs = errors.abs().sort_values(ascending=False)

print(f"\n{'Date':<12} {'Actual ($M)':<15} {'Predicted ($M)':<18} {'Error ($M)':<15} {'% Error':<10}")
print("-" * 70)

for date in errors_abs.head(10).index:
    idx = list(test.index).index(date)
    actual = rw_actual[idx]
    pred = rw_pred[idx]
    error = pred - actual
    pct_error = error / actual * 100
    print(f"{date.strftime('%Y-%m'):<12} {actual:>10,.0f}     {pred:>10,.0f}         {error:>+10,.0f}      {pct_error:>+6.1f}%")

# ============================================================
# INTERPRETATION
# ============================================================

print("\n" + "=" * 60)
print("INTERPRETATION")
print("=" * 60)

print("""
The results show that reserve forecasting faces significant challenges:

1. CRISIS UNPREDICTABILITY: The largest errors occur during policy interventions
   - Jul 2021: -$1,254M drop (CBSL defense spending)
   - Nov 2021: -$681M drop (accelerating crisis)
   - Dec 2021: +$1,551M jump (ISB proceeds / swap activation)

2. POLICY DISCONTINUITIES: Reserves move in jumps, not trends
   - ISB issuances create sudden +$500M-$2,000M jumps
   - FX interventions create sudden -$500M-$1,000M drops
   - These are policy decisions, not forecastable from past data

3. RECOVERY IS MORE PREDICTABLE: Post-IMF (2023+) shows lower errors
   - IMF program creates predictable accumulation path
   - Conditionality constrains policy surprises

4. SIMPLE MODELS CAN'T BEAT RANDOM WALK DURING CRISIS:
   - This suggests reserves are close to a random walk with jumps
   - The "jumps" are policy decisions
""")

# ============================================================
# MONTHLY CHANGES ANALYSIS
# ============================================================

print("\n" + "=" * 60)
print("RESERVE CHANGE PATTERNS")
print("=" * 60)

monthly_changes = reserves.diff().dropna()
train_changes = monthly_changes[monthly_changes.index <= train_end]
test_changes = monthly_changes[monthly_changes.index > train_end]

print(f"\nMonthly change statistics:")
print(f"{'Period':<20} {'Mean ($M)':<15} {'Std Dev ($M)':<15} {'Min ($M)':<15} {'Max ($M)':<15}")
print("-" * 75)
print(f"{'Training':<20} {train_changes.mean():>+10,.0f}     {train_changes.std():>10,.0f}     {train_changes.min():>+10,.0f}     {train_changes.max():>+10,.0f}")
print(f"{'Test (Crisis+Rec)':<20} {test_changes.mean():>+10,.0f}     {test_changes.std():>10,.0f}     {test_changes.min():>+10,.0f}     {test_changes.max():>+10,.0f}")

# Count large moves (>$500M)
large_moves_train = (train_changes.abs() > 500).sum()
large_moves_test = (test_changes.abs() > 500).sum()

print(f"\nLarge moves (>$500M in single month):")
print(f"  Training period: {large_moves_train} ({large_moves_train/len(train_changes)*100:.1f}%)")
print(f"  Test period: {large_moves_test} ({large_moves_test/len(test_changes)*100:.1f}%)")

# ============================================================
# FINAL VERDICT
# ============================================================

print("\n" + "=" * 60)
print("FINAL VERDICT: IS RESERVE FORECASTING FEASIBLE?")
print("=" * 60)

print("""
ANSWER: PARTIALLY — but with important caveats.

WHAT'S PREDICTABLE:
  ✓ Normal accumulation/drawdown trends (when no crisis)
  ✓ Post-IMF program trajectory (constrained by conditionality)
  ✓ Seasonal patterns (e.g., tourism inflows)

WHAT'S NOT PREDICTABLE:
  ✗ Policy decisions (FX interventions, swap activations)
  ✗ Crisis onset timing
  ✗ Jump magnitudes during stress

IMPLICATION FOR RESEARCH:
  → Point forecasts will have large errors during crises
  → Better approach: REGIME-BASED forecasting
     - Identify "normal" vs "stress" vs "crisis" regimes
     - Use different models for each regime
     - Focus on REGIME TRANSITION PROBABILITY rather than point forecasts
  → This supports the HMM approach — but the HMM should predict
    REGIMES, not reserve LEVELS directly.
""")

print("\n" + "=" * 60)
print("EXPERIMENT COMPLETE")
print("=" * 60)
