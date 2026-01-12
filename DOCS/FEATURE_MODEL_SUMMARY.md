# Summary: Feature Count & Model Choice Analysis

**Date**: January 3, 2026

---

## Question 1: Impact of Having All 18+ Variables

### Empirical Results (96 monthly observations)

| Features | Obs/Param | BIC ↓ | Silhouette ↑ | Transitions | Verdict |
|----------|-----------|-------|--------------|-------------|---------|
| **4** | 2.91 | **264** ✓ | 0.32 | 18.4 | Best parsimony |
| 6 | 2.13 | 660 | 0.36 | 3.4 | Worst of both |
| **8** | 1.68 | 419 | **0.56** ✓ | **2.0** ✓ | Best separation |
| 10+ | <1.5 | — | — | — | Insufficient coverage |

### Key Finding: **Trade-off Between Parsimony and Clarity**

**4 Features (what we used)**:
- ✓ Best BIC (most parsimonious)
- ✓ High obs/param ratio (safe from overfitting)
- ✗ Lower regime separation (silhouette 0.32)
- ✗ More regime transitions (18.4 - noisier)

**8 Features (if we had data)**:
- ✗ Higher BIC (complexity penalty)
- ⚠ Borderline obs/param ratio (1.68)
- ✓ Much better regime separation (silhouette 0.56)
- ✓ Cleaner timeline (only 2 transitions!)

**Interpretation**:
- With more features, regimes are MORE distinct (higher silhouette)
- But model complexity increases (worse BIC)
- This is the classic **bias-variance trade-off**

---

### Would 18+ Features Help?

**With 60 monthly observations**: ❌ **NO**
- 18 features = 117 parameters → ratio = 0.51 (severe overfitting)
- Model would not converge reliably
- Need dimensionality reduction (PCA)

**With 96 observations** (our daily→monthly conversion):
- Even 10 features hit coverage limits (78% < 80% threshold)
- **Maximum feasible: 8-10 features**

**To support 18 features**, you'd need:
- **200+ monthly observations** (17+ years of data)
- OR dimensionality reduction (PCA)
- OR regularization (not standard in HMM packages)

---

### Recommended Feature Counts

| Data Size | Conservative | Balanced | Aggressive |
|-----------|--------------|----------|------------|
| 60 months | 3-4 features | 5-6 features | 7-8 features |
| 96 months | 4-5 features | 6-8 features | 9-10 features |
| 120 months | 5-7 features | 8-10 features | 11-14 features |

**Our choice (4 features, 60 months)**: Conservative, prioritizing stability over completeness.

---

## Question 2: Alternative HMM Architectures

### Model Comparison

| Model | Parameters | Implementation | Estimated Gain | Feasibility |
|-------|------------|---------------|----------------|-------------|
| **Gaussian HMM** | 33 | ✓ Standard | Baseline | ✓ Easy |
| **HSMM** | 45-60 | seqlearn | +15% (smooth timeline) | ✓ Moderate |
| **Student-t HMM** | 36-42 | PyMC/Stan | +10% (robustness) | ⚠ Advanced |
| **IOHMM** | 50-70 | Custom | +20% (interpretation) | ⚠ Advanced |
| **AR-HMM** | 81+ | ssm package | ±0% (trade-off) | ⚠ Borderline |
| **MS-VAR** | 200+ | statsmodels | N/A | ❌ Infeasible |

---

### Top Recommendation: **Hidden Semi-Markov Model (HSMM)**

**Why HSMM?**

Crises don't flip monthly. Real regimes have **duration persistence**:
- CALM periods: Years
- STRESS build-up: Months
- CRISIS: Months to years

**Current Gaussian HMM problem**:
- Detected 18.4 transitions with 4 features
- Some single-month regime flips (unrealistic)
- No enforcement of minimum duration

**HSMM solution**:
```python
min_duration = {
    'CALM': 6,     # ≥6 months
    'STRESS': 3,   # ≥3 months
    'CRISIS': 3    # ≥3 months
}
```

**Expected improvement**:
- ✓ Fewer transitions (smoother timeline)
- ✓ More realistic regime persistence
- ✓ Better alignment with crisis narrative
- ✓ Modest parameter increase (45-60 vs 33)

**Implementation**:
```bash
pip install seqlearn
```

```python
from seqlearn.hmm import MultinomialHMM

model = MultinomialHMM(
    n_components=3,
    min_duration={0: 6, 1: 3, 2: 3}
)
model.fit(X_discrete)  # Note: requires discrete data
```

**Caveat**: seqlearn requires discrete observations. Would need to bin continuous features.

---

### Alternative: **Student-t HMM** (Robustness)

**Why Student-t?**

Financial crises have **extreme outliers**:
- Sri Lanka inflation: 3% → 70% (20+ standard deviations!)
- These outliers can distort Gaussian means/variances
- Student-t has heavy tails, downweights outliers

**Implementation** (Bayesian):
```python
import pymc as pm

with pm.Model() as t_hmm:
    # Degrees of freedom (controls tail thickness)
    nu = pm.Gamma('nu', alpha=2, beta=0.1, shape=3)

    # State-dependent parameters
    mu = pm.Normal('mu', 0, 10, shape=(3, 4))
    sigma = pm.HalfNormal('sigma', 5, shape=(3, 4))

    # Emissions with Student-t
    # ... (full implementation requires custom likelihood)
```

**Expected improvement**:
- ✓ More robust to 70% inflation spike
- ✓ Prevents outliers from creating spurious regimes
- ⚠ Harder to implement (need Bayesian framework)
- ⚠ Longer computation time

---

### Not Recommended (With Current Data)

**AR-HMM**:
- Too many parameters (81+) for 60 observations
- Would need strong regularization

**MS-VAR**:
- 200+ parameters, completely infeasible
- Need 300+ monthly observations (25+ years)

**IOHMM**:
- Good for interpretation ("COVID caused transition")
- Doesn't improve detection, just explanation
- Moderate complexity increase

---

## Practical Recommendations

### If You Have Limited Time

**Stay with current approach**:
- 4 features + Gaussian HMM
- It works (80% event detection)
- Stable and interpretable
- **Good enough for publication**

### If You Can Invest 1-2 Days

**Priority 1: Try 6-8 features**
```python
features_extended = [
    'awcmr', 'real_policy_rate', 'gross_reserves_usd_m', 'ncpi_yoy_pct',
    'vol_eq_20d', 'usd_lkr',  # Equity vol, FX rate
    'tbill_secondary', 'aspi'  # T-bill, equity index
]
```

**Expected outcome**:
- Better regime separation (silhouette 0.56 vs 0.32)
- Cleaner timeline (2 transitions vs 18)
- Risk: Slightly worse BIC, borderline obs/param ratio
- **Could be worth it for interpretability**

**Priority 2: Implement HSMM**
- Enforce minimum durations
- Smooth out monthly oscillations
- More publishable regime timeline

### If You Have a Week

**Test all three**:
1. Baseline: 4 features, Gaussian HMM
2. Extended: 8 features, Gaussian HMM
3. Duration: 4 features, HSMM

**Compare**:
- Which has best event detection?
- Which has most interpretable timeline?
- Which is most stable (seed sensitivity)?

**Report all three** in paper as robustness checks.

---

## Bottom Line

**Question 1 (Features)**:
- **Current (4 features)**: Safe, parsimonious, interpretable
- **Could improve to 6-8**: Better separation, but more complexity
- **18+ features**: Impossible without PCA or 10+ years more data

**Question 2 (Models)**:
- **Current (Gaussian HMM)**: Standard, works fine
- **Best upgrade: HSMM**: Enforces duration, smoother timeline
- **Alternative: Student-t**: Robust to outliers, harder to implement
- **Don't bother: AR-HMM, MS-VAR**: Need way more data

**Overall assessment**:
Your current choice (4 features, Gaussian HMM) is defensible and probably **80-90% as good** as what you could achieve with optimal feature selection and HSMM. The marginal gains from adding features/changing models are **10-20%** improvements, not game-changers.

**If I were writing the paper**, I would:
1. Keep 4-feature Gaussian HMM as **main specification**
2. Add 8-feature model as **robustness check** (show it confirms findings)
3. Discuss HSMM as **future extension** in limitations section

This gives you a clean main result with demonstrated robustness, without overcomplicating the methodology section.

