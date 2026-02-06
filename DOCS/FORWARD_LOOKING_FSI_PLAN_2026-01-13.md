# Forward-Looking Financial Stress Index Enhancement Plan

**Created**: 2026-01-13 (Tuesday)
**Status**: DRAFT - NOT YET IMPLEMENTED
**Author**: AI Planning Session

---

## Table of Contents

1. [Executive Summary](#executive-summary)
2. [Current State Assessment](#current-state-assessment)
3. [Strategic Enhancements](#strategic-enhancements)
4. [Why This Beats Composite FSI](#why-this-beats-composite-fsi)
5. [Implementation Architecture](#implementation-architecture)
6. [Phased Implementation](#phased-implementation)
7. [Expected Outcomes](#expected-outcomes)
8. [Critical Weaknesses & Risks](#critical-weaknesses--risks)
9. [Open Questions Requiring Decision](#open-questions-requiring-decision)

---

## Executive Summary

Transform the current retrospective HMM-based FSI into a forward-looking early warning system that predicts future stress regimes using leading indicators, transition probability forecasting, and predictive modeling - going beyond what simple composite indices can achieve.

**Key Shift**: From "What regime are we in?" to "What is the probability of crisis in 3/6/12 months?"

---

## Current State Assessment

### What Works Well

Your current system successfully detects stress **coincident with or shortly before** crises (9-month lead for Sri Lanka). Key achievements:

- 3-state HMM (CALM → STRESS → CRISIS) with clean regime separation
- 100% event detection rate for Sri Lanka crisis events
- 9-month early warning before April 2022 default
- Combined FSI-HMM framework already exists

### Current Limitations

| Limitation | Impact |
|------------|--------|
| **Coincident indicators** | AWCMR, inflation, reserves show stress when stress is happening |
| **No explicit forecasting** | HMM identifies current regime, not future regime probability |
| **Static composite** | Mercado FSI aggregates current values, not trajectories |
| **Missing time dynamics** | No modeling of how fast stress is building |
| **No duration modeling** | Standard HMM allows unrealistic single-month regime flips |
| **No exogenous conditioning** | Can't model "what if Fed raises rates?" |

---

## Strategic Enhancements

### Enhancement 1: Leading Indicator Feature Engineering

**Current features** (coincident/lagging):
- `awcmr` - Shows stress when interbank market is stressed
- `real_policy_rate` - Reflects current monetary conditions
- `gross_reserves_usd_m` - Current level
- `ncpi_yoy_pct` - Lagging inflation

**Proposed leading features** (predict future stress):

| Feature | Formula | Lead Time | Economic Logic |
|---------|---------|-----------|----------------|
| Reserve Velocity | `d(reserves)/dt` (3mo rolling) | 3-6 months | Acceleration predicts depletion |
| Yield Curve Inversion | 10Y - 2Y spread | 6-12 months | Classic recession predictor |
| Real Rate Trajectory | `d(real_rate)/dt` | 3 months | Monetary policy losing control |
| ISB Spread Momentum | `d(spread)/dt` | 2-4 months | Market pricing in default risk |
| Tourism/Remittance Trend | 3mo vs 12mo moving avg | 3-6 months | FX inflow deterioration |
| Global VIX | External risk appetite | 1-3 months | Emerging market capital flows |
| Credit-to-GDP Growth | Private sector leverage | 12-24 months | Financial buildup |
| Net Import Cover Velocity | `d(reserve_months)/dt` | 3-6 months | Sustainability trajectory |

**Implementation**: Add to `configs/hmm.yml` and extend `src/slfsi/features/monthly.py`

---

### Enhancement 2: Transition Probability Forecasting

**Current approach**: HMM gives `P(regime_t | data_t)` - what regime are we in NOW?

**Forward-looking approach**: Calculate `P(regime_{t+h} | regime_t, data_t)` - what regime will we be in?

```
Key outputs:
- P(CRISIS in 3 months | currently CALM) 
- P(CRISIS in 6 months | currently STRESS)
- Expected time-to-crisis from current state
```

**Implementation approach**:

```python
# Using transition matrix from fitted HMM
def forecast_regime_probabilities(current_probs, transition_matrix, horizon_months):
    """Forecast regime distribution h steps ahead."""
    future_probs = current_probs
    for _ in range(horizon_months):
        future_probs = future_probs @ transition_matrix
    return future_probs

# Time-to-crisis estimation
def expected_time_to_crisis(transition_matrix, current_state):
    """Expected months until entering CRISIS state."""
    # Uses first-passage time calculation from Markov chain theory
    ...
```

**Enhanced version**: Condition on current indicator values, not just current regime.

---

### Enhancement 3: Hidden Semi-Markov Model (HSMM)

**Why HSMM is better than HMM for early warning**:

| Feature | HMM | HSMM |
|---------|-----|------|
| Duration modeling | None (geometric) | Explicit (negative binomial) |
| "Time in regime" | Not tracked | Key predictor |
| Transition timing | Random | Duration-dependent |
| Realism | Regimes can flip monthly | Minimum durations enforced |

**Key insight**: The probability of transitioning OUT of a regime depends on how long you've been in it:
- CALM for 24 months: Low crisis probability
- CALM for 60 months: Higher crisis probability (complacency builds)
- STRESS for 6 months: High crisis probability (unstable state)

**Implementation**: Use `hsmm` or `pyhsmm` packages

```python
# Conceptual HSMM with duration distributions
duration_params = {
    'CALM': {'distribution': 'negative_binomial', 'r': 24, 'p': 0.5},    # Mean ~24 months
    'STRESS': {'distribution': 'negative_binomial', 'r': 6, 'p': 0.5},   # Mean ~6 months
    'CRISIS': {'distribution': 'negative_binomial', 'r': 12, 'p': 0.5},  # Mean ~12 months
}
```

---

### Enhancement 4: Input-Output HMM (IOHMM) for Exogenous Shocks

**Current limitation**: HMM treats all dynamics as endogenous

**Enhancement**: Model how external factors affect transition probabilities

```
P(regime_t | regime_{t-1}, external_factors_t)
```

**External factors to incorporate**:
- US Federal Reserve policy stance (rate hikes affect EM capital flows)
- Global commodity prices (oil shocks)
- Regional contagion indicators (other EM stress)
- COVID/geopolitical shock dummies

**Value-add**: Enables counterfactual analysis ("What if Fed raises rates 2%?")

---

### Enhancement 5: Multi-Horizon Stress Probability Dashboard

**Current output**: Single regime label per period

**Enhanced output**: Probability surface across horizons

```
                1mo    3mo    6mo    12mo
P(stay CALM)    0.95   0.85   0.70   0.50
P(→ STRESS)     0.05   0.12   0.22   0.35
P(→ CRISIS)     0.00   0.03   0.08   0.15
```

**Implementation**: Extend `app_regime_analysis.py` with forecast visualization

---

## Why This Beats Composite FSI

| Dimension | Composite FSI | Enhanced HMM-FSI |
|-----------|---------------|------------------|
| **Timing** | Coincident | Forward-looking (1-12 month forecasts) |
| **Output** | Single stress number | Probability distribution over regimes |
| **Dynamics** | Static aggregation | Transition modeling |
| **Thresholds** | Arbitrary cutoffs | Data-driven regime boundaries |
| **Uncertainty** | None | Full probabilistic output |
| **Non-linearity** | Linear combination | Regime-dependent relationships |
| **Early warning** | "Stress is high" | "60% chance of crisis in 6 months" |
| **Policy use** | Monitor | Actionable trigger with lead time |
| **Scenario analysis** | None | "If X happens, crisis prob = Y" |

---

## Implementation Architecture

```
┌─────────────────────────────────────────────────────────────────────┐
│                         DATA LAYER                                   │
├─────────────────┬─────────────────────┬─────────────────────────────┤
│   Raw Data      │  Leading Indicators │   External Factors          │
│   (Current)     │  (Momentum/Velocity)│   (VIX, Fed, Oil)           │
└────────┬────────┴──────────┬──────────┴──────────────┬──────────────┘
         │                   │                          │
         ▼                   ▼                          ▼
┌─────────────────────────────────────────────────────────────────────┐
│                     FEATURE ENGINEERING                              │
├─────────────────┬─────────────────────┬─────────────────────────────┤
│ Current Levels  │ Trajectories/Slopes │ Cross-correlations          │
│ (reserves, etc) │ (d/dt features)     │ (lead-lag relationships)    │
└────────┬────────┴──────────┬──────────┴──────────────┬──────────────┘
         │                   │                          │
         ▼                   ▼                          ▼
┌─────────────────────────────────────────────────────────────────────┐
│                        MODEL LAYER                                   │
├─────────────────┬─────────────────────┬─────────────────────────────┤
│    HSMM         │      IOHMM          │   Model Ensemble            │
│ (with duration) │ (with exogenous)    │   (weighted combination)    │
└────────┬────────┴──────────┬──────────┴──────────────┬──────────────┘
         │                   │                          │
         ▼                   ▼                          ▼
┌─────────────────────────────────────────────────────────────────────┐
│                   FORWARD-LOOKING OUTPUTS                            │
├─────────────────┬─────────────────────┬─────────────────────────────┤
│ Transition      │ Time-to-Crisis      │ Scenario Analysis           │
│ Probabilities   │ Estimates           │ ("What if Fed...")          │
└────────┬────────┴──────────┬──────────┴──────────────┬──────────────┘
         │                   │                          │
         ▼                   ▼                          ▼
┌─────────────────────────────────────────────────────────────────────┐
│                        DASHBOARD                                     │
│   Multi-horizon probability surface + alerts + scenarios             │
└─────────────────────────────────────────────────────────────────────┘
```

---

## Key Files to Modify/Create

| File | Purpose | Effort |
|------|---------|--------|
| `src/slfsi/features/leading.py` | New leading indicator calculations | Medium |
| `src/slfsi/models/hsmm.py` | HSMM implementation | High |
| `src/slfsi/models/forecast.py` | Transition probability forecasting | Medium |
| `src/slfsi/models/iohmm.py` | Exogenous factor conditioning | High |
| `configs/forecast.yml` | Forecasting configuration | Low |
| `app_regime_analysis.py` | Dashboard with forecast visualization | Medium |

---

## Phased Implementation

### Phase 1: Leading Indicators (1-2 weeks)
- Add momentum/velocity features for reserves, rates, spreads
- Add external risk factors (VIX, Fed funds, oil)
- Test if they improve regime separation
- **Deliverable**: Enhanced feature set with demonstrated lead time

### Phase 2: Transition Forecasting (1 week)
- Implement multi-step transition probability calculation
- Add time-to-crisis estimates
- Create forecast visualization in dashboard
- **Deliverable**: Multi-horizon probability forecasts

### Phase 3: HSMM Integration (2 weeks)
- Replace Gaussian HMM with HSMM
- Add duration modeling
- Compare early warning performance
- **Deliverable**: Duration-aware regime detection

### Phase 4: Exogenous Factors (1-2 weeks)
- Implement IOHMM for Fed/global conditions
- Enable scenario analysis
- Build stress testing framework
- **Deliverable**: Scenario-based stress testing

---

## Expected Outcomes

1. **Longer lead times**: Currently 9 months (STRESS detection). Target: 12-18 months with probability forecasts
2. **Actionable signals**: "40% probability of CRISIS within 6 months" vs "we are in STRESS"
3. **Scenario planning**: "If Fed raises 100bp, crisis probability increases to 65%"
4. **Reduced false alarms**: Duration constraints prevent spurious regime flips
5. **Better than composite FSI**: Probabilistic, dynamic, forward-looking vs static aggregation

---

## Critical Weaknesses & Risks

### Weakness 1: Data Scarcity for Complex Models

**Issue**: You have ~60 monthly observations. HSMM and IOHMM require MORE parameters than standard HMM.

| Model | Parameters (approx) | Obs/Param Ratio | Feasibility |
|-------|---------------------|-----------------|-------------|
| Current HMM (4 features, 3 states) | 33 | 1.8 | ✓ Feasible |
| HSMM (4 features, 3 states + duration) | 45-60 | 1.0-1.3 | ⚠️ Borderline |
| IOHMM (4 features, 3 exogenous) | 50-70 | 0.9-1.2 | ⚠️ Borderline |
| Combined HSMM+IOHMM | 80+ | <0.75 | ❌ Overfitting |

**Mitigation Options**:
- Use longer historical data (extend back to 2010-2015 if data available)
- Use Bayesian priors to regularize parameter estimates
- Focus on EITHER HSMM OR IOHMM, not both
- Use simpler duration models (e.g., fixed minimum durations vs full distributions)

---

### Weakness 2: Leading Indicators May Not Exist

**Issue**: The claim that "leading indicators predict crises" assumes such patterns exist. They may not.

**Evidence from your own analysis**:
- AWCMR only breached crisis levels AFTER the FX float (lagging, not leading)
- Reserves were the only true leading indicator (October 2021)
- Inflation was coincident, not leading

**Risk**: Adding more "leading indicators" may just add noise if the underlying pattern doesn't exist.

**Mitigation**:
- Conduct rigorous lead-lag analysis BEFORE adding features
- Use Granger causality tests to verify predictive power
- Accept that some crises are unpredictable (sudden stops, political shocks)

---

### Weakness 3: Overfitting to Sri Lanka 2022

**Issue**: The entire model is validated against ONE crisis event. Even if forecasts work in-sample, they may fail out-of-sample.

**Specific concerns**:
- Cross-country validation already failed (Pakistan, Ghana)
- No out-of-sample testing on Sri Lanka (would need to hold out data)
- Different crisis types may have different leading indicators

**Mitigation**:
- Implement proper time-series cross-validation (rolling origin)
- Test on historical SL stress episodes (2008 GFC impact, 2019 Easter bombing)
- Be explicit about limitations: "Validated for reserve-depletion crises"

---

### Weakness 4: Transition Matrix Stationarity Assumption

**Issue**: Multi-horizon forecasts assume the transition matrix is stable over time. It's not.

**Problem**: 
- `P(STRESS→CRISIS)` was probably 10% in 2019
- `P(STRESS→CRISIS)` was probably 60%+ in 2021 (structural break)
- Using average transition matrix gives meaningless forecasts

**Mitigation**:
- Use time-varying transition probabilities (adds complexity)
- Only forecast 1-3 months ahead (shorter horizons more stable)
- Report uncertainty bands that widen with horizon

---

### Weakness 5: HSMM Package Limitations

**Issue**: The suggested packages (`hsmm`, `pyhsmm`) have limitations.

| Package | Status | Issue |
|---------|--------|-------|
| `hsmm` | Unmaintained | Last update 2018, Python 2 era |
| `pyhsmm` | Complex | Bayesian, requires MCMC, slow |
| `seqlearn` | Limited | Discrete observations only |
| Custom | Required | Significant development effort |

**Mitigation**:
- Consider simpler approaches first (post-hoc duration constraints on HMM)
- Use `pomegranate` or `hmmlearn` with manual duration penalties
- Accept reduced functionality vs theoretical ideal

---

### Weakness 6: Exogenous Data Availability

**Issue**: Global risk factors (VIX, Fed funds, oil) require external data sources that may have:
- Licensing restrictions
- API rate limits
- Missing historical data
- Frequency mismatches (daily VIX vs monthly model)

**Mitigation**:
- Use FRED for Fed funds, VIX (freely available)
- Use monthly averages to match model frequency
- Build robust fallback for missing data

---

### Weakness 7: Interpretability vs Accuracy Trade-off

**Issue**: More complex models (HSMM, IOHMM) may be harder to explain to policymakers.

**Current HMM communication**: "We detect 3 regimes based on 4 indicators"

**Enhanced model communication**: "We use a Hidden Semi-Markov Model with negative binomial duration distributions and exogenous inputs affecting the transition matrix, which produces multi-horizon probability forecasts"

**Mitigation**:
- Keep simple HMM as baseline for communication
- Use complex model for forecasts but explain outputs simply
- Focus on "probability of crisis in X months" not model internals

---

### Weakness 8: No Benchmark Comparison

**Issue**: The plan claims to be "better than composite FSI" but doesn't define how to measure this.

**Questions unanswered**:
- What metric compares them? (AUC? Precision? Lead time?)
- Is 12-month lead with 50% accuracy better than 6-month lead with 80% accuracy?
- How do we avoid hindsight bias in evaluation?

**Mitigation**:
- Define explicit success metrics upfront
- Use proper backtesting (out-of-sample evaluation)
- Compare against naive benchmarks (random walk, threshold rules)

---

## Open Questions Requiring Decision

Before implementation, the following decisions are needed:

### Q1: Scope - Full Enhancement or Focused?

- **Option A**: Implement all 5 enhancements (6-8 weeks, high risk)
- **Option B**: Focus on Phase 1-2 only (2-3 weeks, lower risk)
- **Option C**: Pilot one enhancement, evaluate, then decide

**Recommendation**: Option C - Start with leading indicators, prove value, then expand

---

### Q2: Model Choice - HSMM vs Simpler Duration Constraints?

- **Option A**: Full HSMM with estimated duration distributions
- **Option B**: Standard HMM with post-hoc minimum duration rules
- **Option C**: HMM with duration as a feature (time-in-regime variable)

**Recommendation**: Option C first (least risk), then Option A if data supports it

---

### Q3: Exogenous Factors - Which Ones?

Need to select 2-3 key external factors:
- US Fed funds rate (monetary policy)
- VIX (risk appetite)
- Oil price (commodity dependence)
- China growth (trade partner)
- Global EM stress index (contagion)

**Recommendation**: Start with Fed funds + VIX (most data availability)

---

### Q4: Forecast Horizon - How Far Ahead?

- **Option A**: 1-12 months (full spectrum)
- **Option B**: 3-6 months (sweet spot for policy)
- **Option C**: 1-3 months (highest accuracy)

**Recommendation**: Option B - 3-6 months balances accuracy and usefulness

---

### Q5: Validation Approach - How to Test?

- **Option A**: Full out-of-sample (hold out 2022 data, predict forward)
- **Option B**: Rolling origin cross-validation
- **Option C**: Pseudo-out-of-sample (recursive estimation)

**Recommendation**: Option B - Most rigorous for time series

---

### Q6: Paper vs Product Focus?

- **Option A**: Academic paper (focus on methodology, robustness, caveats)
- **Option B**: Policy tool (focus on usability, real-time deployment)
- **Option C**: Both (but with clear separation)

**Recommendation**: Clarify primary audience before implementation

---

## Next Steps

1. **Review this plan** and address open questions
2. **Decide on scope** (full vs focused implementation)
3. **Validate leading indicator hypothesis** before building complex models
4. **Establish success metrics** for comparison
5. **Begin Phase 1** only after decisions are made

---

*Document created: 2026-01-13*
*Status: AWAITING REVIEW - DO NOT IMPLEMENT YET*

