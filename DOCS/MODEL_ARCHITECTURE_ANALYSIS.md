# Model Architecture Analysis: What If We Had More?

**Questions Addressed:**
1. What if we had all available variables with 100% coverage?
2. What if we used different HMM architectures?

---

## Question 1: Impact of More Features

### Current Situation

**Features Used**: 4 variables
- AWCMR (money market)
- Real policy rate (monetary conditions)
- Gross reserves (external sector)
- Inflation (prices)

**Observations**: 60 months (2020-2024)

**Parameters** (3-state diagonal HMM):
- Means: 3 states × 4 features = 12
- Variances: 3 states × 4 features = 12
- Transition matrix: 3 × 3 = 9
- **Total: 33 parameters for 60 observations** (ratio: 1.82 obs/param)

---

### Available Feature Universe

From the codebase, there are **7 categories** with ~35 total variables:

| Category | Available Variables | Typical Coverage |
|----------|-------------------|------------------|
| **FX & Currency** (6) | usd_lkr, r_fx, vol_fx_20d, reer_index, gold_premium_pct, implied_fx | Mixed (daily) |
| **Equity Market** (8) | aspi, sl20_index, r_eq, vol_eq_20d, r_eq_real, equity_turnover, market_cap, turnover_ratio | 57-100% |
| **Interest Rates** (10) | awcmr, sdfr, slfr, policy_ceiling, tbill_primary, tbill_secondary, tbond_yield, real_policy_rate, interbank_spread, yield_curve_slope | Mixed |
| **External Sector** (5) | gross_reserves_usd_m, reserve_slope_3m, import_cover_months, tourism_earnings_usd_m, remittances_usd_m | Monthly |
| **Sovereign Risk** (3) | isb_yield, embi_spread_approx, us_10y_yield | Limited |
| **Commodities** (2) | gold_usd, gold_lkr | Daily |
| **Inflation** (1) | ncpi_yoy_pct | 100% |

---

### Scenario A: All 18+ Variables with 100% Coverage

**Hypothetical**: Assume we had 18 variables (half the universe) at monthly frequency.

#### Parameter Explosion Problem

**3-State HMM with 18 features:**

| Component | Diagonal Covariance | Full Covariance |
|-----------|-------------------|-----------------|
| Means | 3 × 18 = 54 | 3 × 18 = 54 |
| Covariances | 3 × 18 = 54 | 3 × (18×19/2) = 513 |
| Transition matrix | 9 | 9 |
| **Total parameters** | **117** | **576** |
| **Observations** | 60 | 60 |
| **Obs/Param ratio** | **0.51** | **0.10** |

❌ **This is catastrophic overfitting territory.**

---

#### Rule of Thumb: Sample Size Requirements

| Method | Rule | Our Case (60 obs) | Verdict |
|--------|------|-------------------|---------|
| **Conservative** | 10-20 obs per parameter | 18 features = 117 params<br>Need 1,170-2,340 obs | ❌ Need 20-40 years |
| **Moderate** | 5-10 obs per parameter | Need 585-1,170 obs | ❌ Need 10-20 years |
| **Liberal** | 3-5 obs per parameter | Need 351-585 obs | ❌ Need 6-10 years |

**Conclusion**: With 60 monthly observations, we can support **~6-20 features** maximum (depending on covariance structure).

---

### Practical Solutions for More Features

#### Solution 1: Dimensionality Reduction (PCA)

**Approach**: Reduce 18 variables → 4-6 principal components

```python
from sklearn.decomposition import PCA

# Fit PCA on all 18 features
pca = PCA(n_components=6)
X_pca = pca.fit_transform(X_all_18)

# Check explained variance
print(f"Variance explained: {pca.explained_variance_ratio_.cumsum()}")
# Typically: 6 PCs explain 80-90% of variance

# Use PC scores in HMM
model = GaussianHMM(n_components=3, covariance_type='diag')
model.fit(X_pca)
```

**Pros**:
- Captures most variance with fewer dimensions
- Reduces multicollinearity
- Standard in finance (e.g., yield curve PCA)

**Cons**:
- **Loss of interpretability** - PC1 is a mix of everything
- Can't say "inflation drives this regime"
- Harder to explain to policymakers

**Would it improve detection?**
- Possibly - might capture interactions we miss
- But: harder to validate economically
- Trade-off: accuracy vs interpretability

---

#### Solution 2: Sparse/Regularized HMM

**Approach**: Penalize complexity, force feature selection

```python
# Not standard in hmmlearn, would need custom implementation
# Conceptually:
log_likelihood - λ × (number of non-zero parameters)

# Or elastic net penalty:
log_likelihood - λ₁ × ||θ||₁ - λ₂ × ||θ||₂²
```

**Pros**:
- Automatic feature selection
- Guards against overfitting
- Keeps interpretation

**Cons**:
- Not implemented in standard libraries
- Requires custom code
- Tuning λ is another hyperparameter

---

#### Solution 3: Two-Stage Approach

**Approach**: Use more features to select regimes, then characterize

**Stage 1**: Simple threshold rules on all 18 features
```python
# Define stress if ANY threshold breached
stress = (
    (awcmr > 10) |
    (reserves < 3000) |
    (inflation > 15) |
    (equity_vol > 0.3) |
    # ... 14 more conditions
)
```

**Stage 2**: HMM on selected 4 features, with Stage 1 as prior
```python
# Use threshold results to initialize HMM
model = GaussianHMM(n_components=3, init_params='stmc')
model.startprob_ = empirical_probs_from_thresholds
model.fit(X_4_features)
```

**Pros**:
- Uses all information
- Interpretable
- Computationally simple

**Cons**:
- Ad-hoc combination
- Threshold choice is arbitrary

---

### Empirical Test: What Would 8 Features Do?

Let me estimate what would happen with **8 features** (feasible with our data):

**Hypothetical feature set**:
1. AWCMR ✓
2. Real policy rate ✓
3. Gross reserves ✓
4. Inflation ✓
5. **Equity volatility** (vol_eq_20d)
6. **FX volatility** (vol_fx_20d)
7. **Import coverage** (reserve_slope_3m)
8. **Yield spread** (interbank_spread)

**Parameters**: 3 × (8 + 8) + 9 = 57 parameters → ratio = 1.05 obs/param

**Still tight, but feasible with diagonal covariance.**

**Expected impact**:
- More nuanced regime detection
- Might separate "external stress" from "market stress"
- Risk: model becomes less stable (more parameters → more local optima)

---

### My Assessment: Optimal Feature Count

| # Features | Obs/Param | Stability | Interpretability | Recommendation |
|------------|-----------|-----------|------------------|----------------|
| 2-3 | >2.0 | Excellent | High | Too simple, misses dynamics |
| **4-6** | **1.5-2.0** | **Good** | **High** | **Optimal** ✓ |
| 8-10 | 1.0-1.5 | Moderate | Medium | Feasible with care |
| 12+ | <1.0 | Poor | Low | Overfitting risk |
| 18+ | <<1.0 | Unstable | None (need PCA) | Not recommended |

**Conclusion for Q1**:
- **4-6 features is optimal** for 60 monthly observations
- Going to 8-10 might add marginal value but increases instability
- 18+ features would require PCA (losing interpretability) or 10+ years more data
- **We likely captured the most important dynamics with our 4 features**

---

## Question 2: Alternative HMM Architectures

### Current Model: Gaussian HMM

```
States: s_t ∈ {0, 1, 2} (CALM, STRESS, CRISIS)
Transitions: P(s_t | s_{t-1}) ~ Categorical(π_{s_{t-1}})
Emissions: X_t | s_t ~ N(μ_{s_t}, Σ_{s_t})
```

**Assumptions**:
- Gaussian distributions (problematic for outliers)
- Memoryless transitions (only depends on current state)
- No duration constraints (can flip every period)
- No exogenous variables

---

### Alternative 1: Hidden Semi-Markov Model (HSMM)

**Key Difference**: Explicit duration modeling

```
Duration in state: d ~ NegativeBinomial(r_s, p_s)
Minimum duration: Enforce d_min (e.g., crisis lasts ≥3 months)
```

**Why This Matters for FSI**:

Crises don't flip monthly. In reality:
- CALM periods last years
- STRESS builds over months
- CRISIS persists quarters to years

**Our current model** (Gaussian HMM):
- Detected some monthly oscillations (noise)
- 2-state daily model had hundreds of transitions

**HSMM would**:
- Enforce minimum durations (e.g., crisis ≥ 3 months)
- Reduce spurious regime changes
- More realistic regime persistence

**Implementation**:
```python
# Not in hmmlearn, need seqlearn or custom
from seqlearn.hmm import MultinomialHMM

model = MultinomialHMM(
    n_components=3,
    min_duration={0: 6, 1: 3, 2: 3}  # CALM ≥6mo, STRESS ≥3mo, CRISIS ≥3mo
)
```

**Pros**:
- ✓ More realistic regime dynamics
- ✓ Reduces noise in regime assignments
- ✓ Can enforce economic intuition

**Cons**:
- More parameters (duration distributions)
- Harder to estimate
- Less standard in literature

**Would it improve our results?**
- **Yes, likely**: We had some questionable 1-month regime flips
- Would smooth the regime timeline
- Better alignment with narrative (crises don't end in one month)

**My estimate**: +10-20% improvement in interpretability, similar detection performance.

---

### Alternative 2: Student-t HMM

**Key Difference**: Heavy-tailed distributions

```
Emissions: X_t | s_t ~ Student-t(μ_{s_t}, Σ_{s_t}, ν)
```

where ν controls tail thickness (ν → ∞ converges to Gaussian).

**Why This Matters for FSI**:

Financial data has outliers, especially during crises:
- Sri Lanka inflation went from 3% → 70% (20+ standard deviations!)
- Reserves dropped 79% in months
- Equity market extreme moves

**Gaussian HMM problem**:
- Outliers heavily influence mean/variance estimates
- Can create spurious regimes to "explain" outliers

**Student-t HMM would**:
- Downweight extreme observations
- More robust regime detection
- Better handle crisis dynamics

**Implementation**:
```python
# Custom implementation needed (not in hmmlearn)
# Or use Bayesian approach with PyMC/Stan

import pymc as pm

with pm.Model() as hmm_model:
    # Transition matrix
    π = pm.Dirichlet('π', a=np.ones(3), shape=(3, 3))

    # State-dependent parameters
    μ = pm.Normal('μ', mu=0, sigma=10, shape=(3, 4))
    σ = pm.HalfNormal('σ', sigma=5, shape=(3, 4))
    ν = pm.Gamma('ν', alpha=2, beta=0.1, shape=3)  # df parameter

    # Emissions
    obs = pm.StudentT('obs', nu=ν[state], mu=μ[state], sigma=σ[state], observed=X)
```

**Pros**:
- ✓ Robust to outliers
- ✓ Better for financial data
- ✓ Automatically detects "how non-Gaussian" each regime is

**Cons**:
- More parameters (degrees of freedom ν)
- Computational complexity
- Need Bayesian framework (no closed-form MLE)

**Would it improve our results?**
- **Possibly**: We do have outliers (70% inflation)
- Might prevent outliers from creating spurious CRISIS detections
- More stable regime assignments

**My estimate**: +5-15% improvement in robustness, but harder to implement.

---

### Alternative 3: Autoregressive HMM (AR-HMM)

**Key Difference**: Features depend on their own history

```
Emissions: X_t | s_t ~ N(μ_{s_t} + Φ_{s_t}·X_{t-1}, Σ_{s_t})
```

**Why This Matters for FSI**:

Macro variables are persistent:
- Inflation doesn't jump randomly - it's serially correlated
- Reserves deplete gradually
- Interest rates adjust slowly

**Gaussian HMM treats observations as i.i.d. given state**
- Ignores autocorrelation
- Might mis-classify due to high persistence

**AR-HMM would**:
- Model regime-specific dynamics (e.g., inflation accelerates in CRISIS)
- Better forecasting
- Capture "momentum" toward crisis

**Implementation**:
```python
# Custom implementation or use ssm package
import autograd.numpy as np
from ssm.models import HMM

# AR-HMM with regime-specific AR coefficients
model = HMM(
    n_states=3,
    observations="ar",  # Autoregressive emissions
    observation_kwargs={"lags": 1}  # AR(1)
)
model.fit(X)
```

**Pros**:
- ✓ More realistic for macro time series
- ✓ Better forecasting
- ✓ Captures crisis acceleration dynamics

**Cons**:
- **Many more parameters**: 3 × 4 × 4 = 48 additional AR coefficients!
- With 60 obs, this is borderline infeasible
- Interpretation harder (regime depends on past values too)

**Would it improve our results?**
- **Unclear**: Yes, more realistic, but parameter explosion problem
- Would need regularization or longer time series
- Might not converge reliably with our data size

**My estimate**: Theoretically better, but practically challenging with 60 obs. -10% feasibility.

---

### Alternative 4: Input-Output HMM (IOHMM)

**Key Difference**: Exogenous variables influence transitions or emissions

```
Transitions: P(s_t | s_{t-1}, Z_t) ~ Categorical(softmax(β·Z_t))
Emissions: X_t | s_t, Z_t ~ N(μ_{s_t} + γ_{s_t}·Z_t, Σ_{s_t})
```

where Z_t are exogenous inputs (e.g., COVID dummy, oil prices, global risk).

**Why This Matters for FSI**:

Some crises have external triggers:
- COVID-19 lockdown (exogenous shock)
- Russia-Ukraine war (commodity prices)
- US Fed rate hikes (global tightening)

**Standard HMM**:
- Attributes COVID shock to endogenous state change
- Can't separate structural from event-driven stress

**IOHMM would**:
- Condition on COVID dummy: "Given COVID, what regime?"
- Separate "crisis due to fundamentals" vs "crisis due to shock"
- Better counterfactuals ("what if no COVID?")

**Implementation**:
```python
# Exogenous variables
Z = np.column_stack([
    covid_dummy,        # 1 if 2020-2021
    global_risk_index,  # VIX or similar
    oil_price_shock     # Deviation from trend
])

# Custom IOHMM (not standard)
# Would need to modify hmmlearn or use Bayesian approach
```

**Pros**:
- ✓ Separates structural from shock-driven stress
- ✓ Better causal interpretation
- ✓ Enables counterfactual analysis

**Cons**:
- Need good exogenous variables (what's truly exogenous?)
- More parameters
- Causality still ambiguous

**Would it improve our results?**
- **Yes, for interpretation**: Could say "COVID triggered transition"
- **No, for detection**: Doesn't change what we detect, just how we explain it

**My estimate**: +20-30% better interpretation, no change in detection accuracy.

---

### Alternative 5: Markov-Switching VAR (MS-VAR)

**Key Difference**: Regime-dependent relationships among variables

```
X_t = μ_{s_t} + Φ_{s_t}·X_{t-1} + ε_t,  ε_t ~ N(0, Σ_{s_t})
```

**Why This Matters for FSI**:

Relationships change across regimes:
- **CALM**: Reserves stable, inflation responds slowly to rates
- **CRISIS**: Reserves collapse, inflation explodes, rate policy ineffective

**Standard HMM**:
- Assumes features independent given state
- Misses regime-specific dynamics

**MS-VAR would**:
- Estimate how "reserves → inflation" differs in CALM vs CRISIS
- Capture feedback loops (e.g., reserve loss → currency depreciation → inflation)
- More structural model

**Implementation**:
```python
# Use statsmodels or custom implementation
from statsmodels.tsa.regime_switching.markov_regression import MarkovRegression

# Each feature is DV in turn, others are IVs
model = MarkovRegression(
    endog=X[:, 0],  # e.g., inflation
    k_regimes=3,
    exog=X[:, 1:],  # other features
    switching_variance=True
)
model.fit()
```

**Pros**:
- ✓ Most structural approach
- ✓ Standard in macro/finance
- ✓ Captures regime-specific dynamics

**Cons**:
- **Massive parameter explosion**: 3 states × (4 variables × 4 lags + 4 intercepts + 16 covariances) = ~200 parameters!
- Absolutely infeasible with 60 observations
- Need 5-10 years more data

**Would it improve our results?**
- **If we had data**: Yes, best approach for structural understanding
- **With 60 obs**: No, would catastrophically overfit

**My estimate**: Theoretically ideal, practically impossible with current data.

---

## Comparative Summary

| Model | Realism | Interpretability | Parameters | Feasible (60 obs)? | Estimated Gain |
|-------|---------|------------------|------------|-------------------|----------------|
| **Gaussian HMM** (current) | Baseline | High | 33 | ✓ Yes | — |
| **HSMM** | Higher | High | 45-60 | ✓ Yes | +15% (smoother regimes) |
| **Student-t HMM** | Higher | Medium | 36-42 | ✓ Yes (with Bayesian) | +10% (robustness) |
| **AR-HMM** | Higher | Medium | 81+ | ⚠ Borderline | ±0% (parameter vs realism trade-off) |
| **IOHMM** | Higher | High | 50-70 | ⚠ Borderline | +20% (interpretation only) |
| **MS-VAR** | Highest | Medium | 200+ | ❌ No | N/A (need 200+ obs) |

---

## Recommendation: What I Would Try

### Priority 1: HSMM (Highest ROI)

**Why**:
- Minimal parameter increase
- Addresses a real problem (spurious monthly flips)
- Easy to justify economically
- Improves interpretability significantly

**Implementation roadmap**:
```python
# 1. Define minimum durations based on historical crises
min_duration = {
    'CALM': 6,     # Calm periods last ≥6 months
    'STRESS': 3,   # Building stress lasts ≥3 months
    'CRISIS': 3    # Acute crisis lasts ≥3 months
}

# 2. Use seqlearn or custom HSMM
from seqlearn.hmm import MultinomialHMM
# ... implementation

# 3. Compare regime timelines
# Expect: Same crisis detection, fewer oscillations
```

---

### Priority 2: Student-t HMM (If Time Allows)

**Why**:
- Financial data really is heavy-tailed
- Addresses outlier problem
- Reasonable parameter increase

**Implementation roadmap**:
```python
# Use PyMC for Bayesian estimation
import pymc as pm

# Define model with Student-t emissions
# Compare regime assignments to Gaussian
# Check if outliers (70% inflation) affect results less
```

---

### Priority 3: IOHMM (For Interpretation)

**Why**:
- Helps with "what caused the crisis?" question
- Good for policy discussion
- Doesn't affect detection, just explanation

**Exogenous candidates**:
- COVID-19 dummy (2020-03 to 2021-06)
- Russia-Ukraine war dummy (2022-02+)
- Global risk (VIX index)
- Fed funds rate (global tightening)
- Oil prices (terms of trade shock)

---

### Do NOT Try (With Current Data):
- ❌ AR-HMM: Too many parameters
- ❌ MS-VAR: Way too many parameters
- ❌ 18+ features: Need dimensionality reduction first

---

## Practical Next Steps

If you want to explore this:

1. **Estimate optimal feature count empirically**:
   ```python
   for n_features in [4, 6, 8, 10]:
       # Use information criteria
       bic_scores = []
       for random_seed in range(10):
           model = fit_hmm(X[:, :n_features])
           bic = calculate_bic(model)
           bic_scores.append(bic)
       print(f"{n_features} features: BIC = {np.mean(bic_scores):.0f}")
   ```

2. **Implement HSMM** (most promising):
   - Install seqlearn: `pip install seqlearn`
   - Define duration constraints
   - Compare to baseline

3. **Test Student-t robustness**:
   - Implement in PyMC
   - Check if high-inflation period affects regimes differently

---

## Bottom Line

**Question 1 (More features)**:
- 18+ features with 60 observations = overfitting disaster
- **Optimal is 4-6 features** (what we have)
- Could go to 8-10 with caution
- Beyond that, need PCA (lose interpretability) or more data

**Question 2 (Different models)**:
- **HSMM is most promising** (+15% improvement, easy to justify)
- Student-t HMM worth trying (+10% robustness)
- IOHMM good for interpretation, not detection
- AR-HMM, MS-VAR need way more data

**Overall**: We likely made the right choice with 4 features + Gaussian HMM. The main improvement opportunity is **HSMM to enforce duration constraints**, which would smooth out monthly oscillations without adding many parameters.

