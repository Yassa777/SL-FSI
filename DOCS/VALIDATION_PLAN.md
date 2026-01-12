# SL-FSI Validation Plan + Model Roadmap

Date: 2026-01-XX
Scope: Sri Lanka only (cross-country excluded)

This document lays out a validation plan and a model roadmap that explicitly address the known failure modes of HMMs (Gaussian emissions, conditional independence, Markov/ stationarity assumptions, local optima, and duration bias). It is designed to be academically defensible while remaining feasible with the current dataset size and coverage constraints.

---

## 1) Objectives and Scientific Claims

Primary objective: produce a reliable, interpretable timeline of financial stress regimes for Sri Lanka.

Secondary objective: evaluate whether the regime signals provide a meaningful early-warning window relative to known crisis milestones.

This plan focuses on validation against explicit events and internal consistency checks, not on causal claims. Any forecasting claims must be clearly separated from regime characterization.

---

## 2) Data and Feature Strategy (Justification)

### 2.1 Feature tiers
- Core features (high coverage, monthly, macro-financial outcomes):
  - `awcmr`, `real_policy_rate`, `gross_reserves_usd_m`, `ncpi_yoy_pct`
  - Justification: 100% coverage in the crisis window; stable measurement; interpretable by policymakers.
- Market stress features (lower coverage, higher frequency):
  - `vol_eq_20d`, `r_eq`, `gold_premium_pct`, `embi_spread_approx`
  - Justification: closer to market stress mechanics but sparse and regime-limited.

### 2.2 Data quality decisions
- Monthly panel is used directly (`data/merged/slfsi_monthly_panel.csv`) to avoid daily forward-fill artifacts.
- Zero placeholders in ASPI/SL20 are treated as missing, not as valid prices.
- Historical extension (2005-2017) uses interpolated macro series and is explicitly flagged as low-fidelity for volatility-driven inference.

Rationale: regime models are sensitive to spurious variance; higher-quality monthly macro data is more reliable than artificially dense daily series.

---

## 3) Model Roadmap (with Justifications)

### Stage A: Baseline HMM (current)
- 3-state Gaussian HMM with diagonal covariance.
- Justification: minimal parameter count, interpretable regimes, stable with small N (~60-100 months).
- Role: descriptive regime timeline, not forecasting proof.

### Stage B: Duration-aware upgrade (HSMM or sticky HMM)
- Replace HMM with HSMM (explicit duration) or sticky HMM (high self-transition prior).
- Justification: addresses rapid switching / state fragmentation observed in daily models.
- Expected benefit: more stable regimes, fewer unrealistic oscillations.

### Stage C: Robust emissions
- Student-t emissions or mixture-of-Gaussians per state.
- Justification: macro/market series are fat-tailed; Gaussian assumption underestimates tail risk.
- Expected benefit: lower sensitivity to crisis outliers.

### Stage D: Covariate-dependent transitions
- Transition probabilities depend on external variables (e.g., reserves trend, global rates).
- Justification: pure Markov assumption is too rigid; transition drivers are observable.
- Expected benefit: improved narrative consistency and less overfitting to local noise.

### Stage E: Alternative models for sensitivity
- Change-point detection (for structural break timing).
- MS-VAR / AR-HMM (if sample size supports) for dynamic dependence.
- Simple supervised baseline (logit) for early-warning comparison only.

---

## 4) Validation Plan (Quantitative and Qualitative)

### 4.1 Event-alignment validation (primary)
Use pre-specified events (policy and market milestones) and evaluate alignment:
- FX float (2022-03), default (2022-04), peak inflation (2022-09), IMF EFF (2023-03).
- Windows: +/- 1 month (tactical) and +/- 2 months (strategic).
- Metrics: hit rate, false alarms, lead time to default.

Justification: ties regime shifts to observable real-world events without overfitting the model to those dates.

### 4.2 Regime stability tests
- Multiple random restarts; compare regime agreement (% overlap).
- Rolling refits (expanding window) to detect regime instability over time.
- If agreement < 80%, regimes are considered unstable and results are downgraded to exploratory.

Justification: HMM is sensitive to initialization and local optima; stability is a minimum requirement for defensible claims.

### 4.3 Internal consistency tests
- Regime ordering checks: CRISIS should have lower reserves, higher inflation, worse real rates.
- Feature monotonicity across states (CALM -> STRESS -> CRISIS).

Justification: prevents regimes from being statistical artifacts without economic meaning.

### 4.4 Sensitivity to feature set
- Compare 4-feature baseline vs 6-8 features where coverage allows.
- Track transition count, regime duration, and event alignment.

Justification: ensures results are not an artifact of a single feature configuration.

### 4.5 Robustness to data revisions
- Re-run with alternate reserve measure (net usable reserves).
- Compare with and without interpolated historical data.

Justification: structural breaks in reserves and policy series are central to crisis identification.

---

## 5) Evaluation Criteria (Go / No-Go)

The model is considered usable for a Sri Lanka-only descriptive paper if:
- Regime timeline is stable across seeds (>80% agreement).
- Event alignment hit rate >= 60% in strategic windows.
- CRISIS regime aligns with known 2022 events and is economically coherent.

The model is not to be used for forecasting claims if:
- Lead time fluctuates materially across seeds or feature sets.
- Regime order is not monotonic in macro stress variables.

---

## 6) Deliverables and Timeline

### Phase 1: Baseline validation (1-2 days)
- Re-run baseline 3-state monthly HMM with multiple seeds.
- Produce event-alignment table and regime summary.

### Phase 2: HSMM / sticky HMM (2-4 days)
- Implement duration constraint, compare transitions and alignment.
- Decide whether to promote as main spec.

### Phase 3: Robust emissions (2-3 days)
- Fit Student-t emission model; compare regime stability.

### Phase 4: Sensitivity and reporting (2-3 days)
- Feature set comparisons and data revision tests.
- Produce final narrative and limitations.

---

## 7) Summary: Why This Roadmap is Defensible

- It starts from the most parsimonious model suited to the data size.
- It directly addresses each HMM failure mode with a targeted upgrade.
- It separates descriptive regime identification from predictive claims.
- It emphasizes stability and interpretability over marginal fit gains.

This positions the project as a credible Sri Lanka stress-regime analysis while creating a clear path to future early-warning or predictive extensions.
