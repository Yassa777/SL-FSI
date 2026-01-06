# Hidden Markov Models (HMMs): A Deep Dive via the Sri Lanka Financial Stress Index (SL‑FSI) Project

**Date**: January 2, 2026  
**Running case study**: **Sri Lanka Financial Stress Index (SL‑FSI) regime detection**  
**Model in the repo today**: **3‑state Gaussian HMM (diagonal covariance) on monthly macro‑financial data**  
**States (interpreted)**: **CALM → STRESS → CRISIS**  

This is a **theory-first HMM guide** that continuously maps every concept back to a concrete, real pipeline:
- observations are the **4 monthly SL‑FSI features** (AWCMR, real policy rate, reserves, NCPI inflation),
- hidden states are **financial stress regimes**,
- inference outputs are **regime probabilities + decoded regime path** you can validate against crisis events.

---

## Table of Contents

0. [Project Snapshot: what exactly you built](#0-project-snapshot-what-exactly-you-built)  
1. [Foundations: Markov chains → HMMs](#1-foundations-markov-chains--hmms)  
2. [Formal definition: parameters and assumptions](#2-formal-definition-parameters-and-assumptions)  
3. [Rabiner’s 3 problems (and which ones you use in SL‑FSI)](#3-rabiners-3-problems-and-which-ones-you-use-in-sl-fsi)  
4. [Core algorithms](#4-core-algorithms)  
   - [Forward (likelihood + filtered probabilities)](#41-forward-likelihood--filtered-probabilities)  
   - [Backward + smoothing](#42-backward--smoothing)  
   - [Viterbi decoding](#43-viterbi-decoding)  
   - [Baum–Welch / EM training](#44-baumwelch--em-training)  
5. [Practical issues that mattered in SL‑FSI](#5-practical-issues-that-mattered-in-sl-fsi)  
6. [Model design choices (states, covariance, scaling)](#6-model-design-choices-states-covariance-scaling)  
7. [Model selection with small samples (AIC/BIC + sanity checks)](#7-model-selection-with-small-samples-aicbic--sanity-checks)  
8. [Validation in the real world: event alignment + false alarms](#8-validation-in-the-real-world-event-alignment--false-alarms)  
9. [Extensions worth caring about for SL‑FSI](#9-extensions-worth-caring-about-for-sl-fsi)  
10. [Implementation patterns & code you can drop into the repo](#10-implementation-patterns--code-you-can-drop-into-the-repo)  
11. [Cheat sheets](#11-cheat-sheets)  
12. [References](#12-references)

---

## 0. Project Snapshot: what exactly you built

### 0.1 The economic question (the *latent variable*)
You’re not trying to predict a single number. You’re trying to infer a **hidden regime**:

- **CALM**: routine shocks, policy tools still effective  
- **STRESS**: vulnerabilities rising, buffers eroding, policy effectiveness degrading  
- **CRISIS**: breakdown (default / hyperinflation / market freeze), policy tools exhausted  

**Key modeling decision**: treat “financial stress” as **latent** and infer it from symptoms.

### 0.2 Observations (the emissions): your 4 monthly features
At each month \(t\), you observe a 4‑dimensional vector:

\[
x_t = [\text{AWCMR}_t,\ \text{real\_policy\_rate}_t,\ \text{gross\_reserves}_t,\ \text{NCPI\_inflation}_t] \in \mathbb{R}^4
\]

These are the only features you kept because they have **100% monthly coverage** across the window you care about.

### 0.3 Hidden states: your 3 regimes
\[
s_t \in \{0,1,2\} \quad \text{(later mapped to CALM/STRESS/CRISIS)}
\]

### 0.4 What the fitted model produces
Once trained, the HMM gives you:

1. **Transition matrix** \(A\): persistence + how regimes change
2. **Emission parameters** \((\mu_k, \Sigma_k)\) per regime \(k\)
3. **Decoded path** (Viterbi) \(s_{1:T}^\*\): a single best regime timeline
4. **State probabilities** (posterior) \(P(s_t=k \mid x_{1:T})\): “soft” regime assignment

### 0.5 Why monthly aggregation was non‑negotiable in your case
Your raw panel has daily rows, but most macro series are monthly and were forward‑filled. A daily HMM sees artificial month-boundary steps and can hallucinate hundreds of transitions. Aggregating to true information frequency (monthly) restores the intended problem.

### 0.6 The fitted numbers you currently report (so you can sanity-check future refits)

These are **not universal truths**; they’re what you learned on your current sample and preprocessing choices.  
They’re still extremely useful as a “does my pipeline still behave?” regression test.

#### Transition matrix (sticky, sequential)
\[
A =
\begin{bmatrix}
0.973 & 0.027 & 0.000 \\
0.083 & 0.833 & 0.083 \\
0.000 & 0.083 & 0.917
\end{bmatrix}
\]

**Interpretation**:
- CALM is very persistent (~97% chance to remain CALM month to month).
- You basically never jump CALM→CRISIS; you pass through STRESS.
- CRISIS is sticky (~92% chance to remain CRISIS).

#### Regime timeline (Viterbi decode)
- 2020‑01 → 2021‑06: **CALM**
- 2021‑07 → 2022‑03: **STRESS**
- 2022‑04 → 2023‑03: **CRISIS**
- 2023‑04 → 2023‑06: **STRESS**
- 2023‑07 → 2024‑12: **CALM**

Only **4 transitions** over ~60 months — which is exactly what you want if you’re building a policy signal.

#### Regime “faces” (means in original units; illustrative values you reported)

| Regime | AWCMR | Real policy rate | Gross reserves (USD m) | NCPI YoY inflation |
|---|---:|---:|---:|---:|
| **CALM** | ~7.3% | ~+4.9% | ~5,507 | ~3.0% |
| **STRESS** | ~8.5% | ~‑6.2% | ~2,502 | ~14.0% |
| **CRISIS** | ~15.3% | ~‑40.2% | ~1,957 | ~54.7% |

The ordering is consistent across features: stress/crisis corresponds to **higher rates, worse real stance, lower reserves, higher inflation**.

#### The daily-data failure mode (why monthly aggregation isn’t optional)
- Daily forward-filled panel: ~1,827 rows but only ~60 unique monthly observations.
- Daily HMM: ~844 regime transitions (pure artifact).
- Monthly HMM: 4 transitions (signal).

This is a rare case where “fix the data frequency” is not a best practice — it’s the difference between nonsense and a usable model.

---

## 1. Foundations: Markov chains → HMMs

A **Markov chain** is about the *hidden state dynamics*:

\[
P(s_t \mid s_{1:t-1}) = P(s_t \mid s_{t-1})
\]

An **HMM** adds an observation process:

- first you transition in the hidden chain,
- then you emit an observation conditioned on the current hidden state.

### SL‑FSI mapping
- Hidden chain \(s_t\): “the economy is in CALM/STRESS/CRISIS”
- Emission \(x_t\): the 4‑feature macro‑financial snapshot you observe that month

---

## 2. Formal definition: parameters and assumptions

An HMM is typically written as \(\lambda = (\pi, A, B)\):

- \(\pi_i = P(s_1=i)\) initial state distribution
- \(A_{ij} = P(s_t=j \mid s_{t-1}=i)\) transition probabilities
- \(B\) emission model: \(p(x_t \mid s_t)\)

### 2.1 Gaussian HMM (what you actually use)
Because SL‑FSI observations are continuous, your emissions are Gaussian:

\[
x_t \mid (s_t = k) \sim \mathcal{N}(\mu_k,\ \Sigma_k)
\]

with \(d=4\) features.

**Diagonal covariance** (your choice) means:

\[
\Sigma_k = \mathrm{diag}(\sigma^2_{k,1}, \ldots, \sigma^2_{k,4})
\]

so the emission likelihood factors:

\[
p(x_t \mid s_t=k)=\prod_{m=1}^{4}\mathcal{N}(x_{t,m} \mid \mu_{k,m},\ \sigma^2_{k,m})
\]

### 2.2 The two independence assumptions (and how they bite in SL‑FSI)
1) **First‑order Markov**: the regime only “remembers” last month’s regime.  
2) **Output independence given state**: given the regime, the month’s observation is generated without depending on other months.

**In SL‑FSI terms**:
- the model does *not* explicitly know “we’ve been in STRESS for 9 months” (duration dependence),
- and with diagonal \(\Sigma_k\) it can’t express “in CRISIS, inflation and AWCMR co‑move more strongly”.

You partly compensate via:
- high diagonal entries of \(A\) (sticky regimes),
- standardized features so no single series dominates.

---

## 3. Rabiner’s 3 problems (and which ones you use in SL‑FSI)

Rabiner frames HMM usage as three core tasks:

1) **Evaluation**: compute \(P(x_{1:T}\mid \lambda)\)  
2) **Decoding**: infer most likely hidden path \(s_{1:T}^\*\)  
3) **Learning**: fit \(\lambda\) to maximize \(P(x_{1:T}\mid \lambda)\)

### SL‑FSI: which ones matter day‑to‑day
- **Learning**: `model.fit(X_scaled)` (Baum–Welch / EM)
- **Decoding**: `model.predict(X_scaled)` (Viterbi) → your clean 4‑transition regime timeline
- **Evaluation**: `model.score(X_scaled)` is useful for model selection & restarts, but your main “evaluation” is *policy‑relevant validation* (event alignment + false alarms)

---

## 4. Core algorithms

For SL‑FSI you mainly *use* Viterbi and EM, but you should understand forward/backward because they’re what you need for real-time probabilities.

### 4.1 Forward (likelihood + filtered probabilities)

**Forward variable**:
\[
\alpha_t(j)=P(x_{1:t},\ s_t=j\mid \lambda)
\]

Recurrence:
\[
\alpha_t(j)=\left[\sum_{i=1}^{K}\alpha_{t-1}(i)A_{ij}\right]\cdot p(x_t\mid s_t=j)
\]

The total likelihood:
\[
P(x_{1:T}\mid \lambda)=\sum_{j=1}^{K}\alpha_T(j)
\]

#### SL‑FSI: the “real-time” regime probability you actually want
Policymakers don’t get to condition on the future. Real-time monitoring uses:

\[
P(s_t=j\mid x_{1:t})=\frac{\alpha_t(j)}{\sum_\ell \alpha_t(\ell)}
\]

That’s *filtered* probability. It answers: “given data up to this month, what regime are we in?”

> If you only ever look at Viterbi (full‑sequence decode), you’re doing **ex‑post explanation**.  
> If you compute filtered probabilities, you can build an **early warning dashboard**.

**Numerical stability note**: multiplying many small probabilities underflows fast. Use scaling or log-space.

### 4.2 Backward + smoothing

Backward variable:
\[
\beta_t(i)=P(x_{t+1:T}\mid s_t=i,\lambda)
\]

Smoothed posterior (uses future information):
\[
\gamma_t(i)=P(s_t=i\mid x_{1:T},\lambda)\propto \alpha_t(i)\beta_t(i)
\]

#### SL‑FSI interpretation
- **Filtered**: \(P(s_t\mid x_{1:t})\) → what you’d know *at time t*  
- **Smoothed**: \(P(s_t\mid x_{1:T})\) → best retrospective reconstruction of stress history

Your event-alignment validation is inherently closer to *smoothed* or Viterbi outputs (because you’re evaluating history).

### 4.3 Viterbi decoding

Viterbi finds a single most likely regime path:

\[
s_{1:T}^\*=\arg\max_{s_{1:T}} P(s_{1:T}\mid x_{1:T},\lambda)
\]

It’s forward-like DP, but with \(\max\) instead of \(\sum\).

#### SL‑FSI: why Viterbi “feels” so clean
Because your fitted \(A\) is diagonally dominant, switching regimes is expensive unless emissions strongly support it. That’s exactly what you want to avoid “cry wolf” transitions.

### 4.4 Baum–Welch / EM training

You want parameters \(\lambda\) that maximize likelihood:

\[
\lambda^\*=\arg\max_\lambda P(x_{1:T}\mid \lambda)
\]

EM alternates:

- **E‑step**: infer expected state occupancies / transitions under current params
- **M‑step**: update \(\pi, A, (\mu_k,\Sigma_k)\) using those expectations

For Gaussian emissions:

\[
\mu_k = \frac{\sum_t \gamma_t(k) x_t}{\sum_t \gamma_t(k)},\quad
\Sigma_k = \frac{\sum_t \gamma_t(k) (x_t-\mu_k)(x_t-\mu_k)^\top}{\sum_t \gamma_t(k)}
\]

(With diagonal covariance, keep only diagonal entries.)

#### SL‑FSI practical reminder
EM finds a **local optimum**. If you change `random_state`, you can get different regime segmentations, especially with small samples. That’s why multiple restarts + picking best log-likelihood is not optional if you care about robustness.

---

## 5. Practical issues that mattered in SL‑FSI

This section is the “why your first attempts broke” section.

### 5.1 Mixed frequency + forward-fill artifacts
If monthly series are forward-filled to daily:
- you get many repeated identical values,
- then a step change at month boundaries,
- which the HMM misreads as “many regime shifts”.

**Fix**: aggregate daily to monthly before fitting.

### 5.2 Coverage-first feature selection isn’t a compromise; it’s a constraint
In your dataset, some theoretically “best” indicators vanish in the crisis (thin markets freeze). In practice, an indicator that disappears when the system is stressed is unusable for regime monitoring.

### 5.3 Standardization is part of the model
Because the Gaussian likelihood uses squared distances, features with large scales dominate unless standardized. With reserves in USD millions and rates in % points, z-scoring isn’t hygiene — it changes the fitted regimes.

### 5.4 Diagonal covariance is a statistical budget decision
With about ~60 monthly observations, you’re in a small-sample regime.
Diagonal covariance is a disciplined choice: fewer parameters, less overfitting.

---

## 6. Model design choices (states, covariance, scaling)

### 6.1 Why 3 regimes is not arbitrary
In SL‑FSI, “STRESS” behaves differently from both CALM and CRISIS:
- reserves are falling,
- real policy rate becomes negative,
- inflation rises but is not yet hyperinflation,
- funding stress begins to appear (AWCMR drifting up).

2 states forces you to merge stress + crisis and gives you a less actionable signal.  
4 states is easy to overfit with your sample size.

### 6.2 Interpreting the transition matrix \(A\)

Given \(A\), the expected duration in regime \(k\) (in time steps) is:

\[
\mathbb{E}[D_k] = \frac{1}{1 - A_{kk}}
\]

This is extremely useful for sanity-checking.

**SL‑FSI gut-check**:
- If you estimate \(A_{CRISIS,CRISIS}=0.92\), expected crisis duration is \(1/(1-0.92)=12.5\) months — that’s in the same ballpark as your crisis segment.
- If you got 0.50, expected duration 2 months — that would be suspicious (it would say crises are short blips).

### 6.3 Diagonal vs full covariance: parameter count (your exact numbers)
Let \(K\) = number of states, \(d\) = number of features.

- Transition params: \(K(K-1)\) (each row sums to 1)
- Initial distribution: \(K-1\)
- Means: \(Kd\)
- Covariances:
  - diagonal: \(Kd\)
  - full: \(K\cdot d(d+1)/2\)

So total parameters:

\[
p_{\text{diag}}=(K-1)+K(K-1)+Kd+Kd
\]
\[
p_{\text{full}}=(K-1)+K(K-1)+Kd+K\cdot \frac{d(d+1)}{2}
\]

For SL‑FSI \(K=3\), \(d=4\):

- \(p_{\text{diag}} = 2 + 6 + 12 + 12 = 32\)
- \(p_{\text{full}} = 2 + 6 + 12 + 30 = 50\)

(Depending on implementation details you may see +1 here or there, but the point stands: **full covariance costs ~18 more parameters** with only ~60 observations.)

---

## 7. Model selection with small samples (AIC/BIC + sanity checks)

### 7.1 Information criteria (useful, not sovereign)
\[
\text{AIC} = -2\log \mathcal{L} + 2p,\qquad
\text{BIC} = -2\log \mathcal{L} + p\log(T)
\]

With small \(T\) (like ~60), BIC penalizes complexity hard.

**SL‑FSI practice**:
- use AIC/BIC to reject obviously overfit models,
- but your real arbiter is interpretability + stability + event alignment.

### 7.2 A selection protocol that’s actually defensible for SL‑FSI
For each \(K \in \{2,3,4\}\) and covariance \(\in\{\text{diag},\text{full}\}\):

1) run 20 restarts (different seeds), pick best log-likelihood  
2) compute AIC/BIC  
3) check decoded regimes:
   - Are there absurd “flickers” (CALM↔STRESS monthly ping-pong)?
   - Is there a meaningful stress build-up period?
   - Does CRISIS occur in 2022 and persist plausibly?
4) run event alignment metrics  
5) keep the simplest model that is stable and policy-interpretable

---

## 8. Validation in the real world: event alignment + false alarms

Unsupervised models don’t have labels. So you need a **validation proxy** that is:
- pre-specified (not cherry-picked),
- aligned with real decisions,
- robust to small timing errors.

### 8.1 Event alignment as a classification test
You define events \(t_0\) (e.g., default date) and a window \(W\) months.

A **hit** can be defined as:

\[
\exists t \in [t_0-W,\ t_0]\ \text{such that}\ P(s_t=\text{CRISIS}) \ge \tau
\]

- \(W\): tolerance window (policy relevance)
- \(\tau\): probability threshold (decision rule)

#### Why “early” is not always better
If you fire a CRISIS signal 9 months early, you may cause:
- unnecessary controls,
- credibility loss (“model always screams crisis”),
- political economy pushback.

For some decisions, being “just-in-time” (e.g., ~2 months) is more valuable than being wildly early.

### 8.2 False alarms (the “cry wolf” test)
You should track:
- number of transitions not near any event,
- fraction of months with high crisis probability in historically calm periods.

In your run, you got **very few transitions** and they aligned with major events — which is the *main* reason your result is compelling.

### 8.3 The uncomfortable truth: 100% hit rate can be suspicious
If you test on 12 events that are all in the same crisis arc, high hit rates are possible even with mediocre models.

What keeps SL‑FSI honest:
- you explicitly had competing baselines (z-score thresholds),
- daily HMM failed badly (844 transitions), monthly fixed it,
- the 3-state structure yields plausible durations.

---

### 8.4 Your pre-specified event set (example table)

You tested against **12 events** (chosen up front in the research plan) with a **strategic alignment window of ±2 months**.
Here’s the compact view:

| Date | Event | Expected regime | Detected regime | Hit? |
|---|---|---|---|:--:|
| 2019‑04‑21 | Easter attacks | CALM | CALM | ✓ |
| 2020‑03‑20 | COVID lockdown | CALM | CALM | ✓ |
| 2021‑04‑22 | Fertilizer ban | CALM | CALM | ✓ |
| 2022‑01‑18 | $500M ISB repayment | STRESS | STRESS | ✓ |
| 2022‑03‑07 | FX float | STRESS | STRESS | ✓ |
| 2022‑04‑12 | Sovereign default | CRISIS | CRISIS | ✓ |
| 2022‑07‑14 | President resigns | CRISIS | CRISIS | ✓ |
| 2022‑09‑01 | IMF staff agreement | CRISIS | CRISIS | ✓ |
| 2023‑03‑20 | IMF EFF approval | CRISIS | CRISIS | ✓ |
| 2023‑06‑28 | Debt restructuring plan | STRESS | STRESS | ✓ |
| 2024‑06‑26 | Creditor agreement | CALM | CALM | ✓ |
| 2024‑09‑19 | Bondholder agreement | CALM | CALM | ✓ |

You reported **12/12 hits** under that window. That’s strong — and it raises the right follow-up question:
*“Is this robust to refits, seeds, and feature variants?”* (See Section 7.2 and Section 10.2.)



## 9. Extensions worth caring about for SL‑FSI

These are not “future work” fluff. They directly target your known limitations.

### 9.1 Hidden Semi‑Markov Models (HSMM): explicit duration modeling
HMM implies geometric duration in each state. If you believe “the longer we stay in STRESS, the higher the chance of CRISIS”, HSMM is a better inductive bias.

### 9.2 Heavy-tailed emissions (Student‑t HMM)
Inflation jumps like 3% → 70% are not Gaussian. A Student‑t emission handles fat tails and can reduce the incentive to create extra states just to soak outliers.

### 9.3 Autoregressive HMM (AR‑HMM)
Your observations are not i.i.d. within a regime; they trend and mean-revert. AR‑HMM lets:
\[
x_t = c_{s_t} + \Phi_{s_t} x_{t-1} + \epsilon_t
\]
so regimes differ in dynamics, not just mean/variance.

### 9.4 IOHMM: transitions depend on covariates
You might want:
- higher probability of STRESS→CRISIS when reserves are below a threshold,
- or when real rates are deeply negative.

That’s “transition with inputs”.

### 9.5 Missing data models (instead of dropping rows)
If you later re‑introduce indicators with gaps, you’ll want an HMM that can marginalize missing dimensions rather than deleting months.

---

## 10. Implementation patterns & code you can drop into the repo

### 10.1 Your core monthly pipeline (clean version)

```python
import numpy as np
import pandas as pd
from hmmlearn.hmm import GaussianHMM

FEATURES = ["awcmr", "real_policy_rate", "gross_reserves_usd_m", "ncpi_yoy_pct"]

def to_monthly_panel(daily: pd.DataFrame) -> pd.DataFrame:
    df = daily.copy()
    df["year_month"] = df["date"].dt.to_period("M")
    monthly = df.groupby("year_month")[FEATURES + ["date"]].first().reset_index(drop=True)
    monthly = monthly.dropna(subset=FEATURES)
    return monthly

def zscore(X: np.ndarray) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    mu = X.mean(axis=0)
    sig = X.std(axis=0, ddof=0)
    return (X - mu) / sig, mu, sig

def fit_hmm(X_scaled: np.ndarray, n_states: int = 3, seed: int = 42) -> GaussianHMM:
    model = GaussianHMM(
        n_components=n_states,
        covariance_type="diag",
        n_iter=300,
        random_state=seed,
    )
    model.fit(X_scaled)
    return model
```

### 10.2 Multiple restarts (critical with small samples)

```python
def fit_best_of_n(X_scaled: np.ndarray, n_states: int, n_restarts: int = 20):
    best_model, best_ll = None, -np.inf
    for seed in range(n_restarts):
        m = fit_hmm(X_scaled, n_states=n_states, seed=seed)
        ll = m.score(X_scaled)
        if ll > best_ll:
            best_ll, best_model = ll, m
    return best_model, best_ll
```

### 10.3 Labeling states (your inflation-sorting trick, generalized)

```python
def label_states_by_feature(monthly: pd.DataFrame, raw_states: np.ndarray, feature: str):
    tmp = monthly.copy()
    tmp["state"] = raw_states
    state_means = tmp.groupby("state")[feature].mean().to_dict()

    order = sorted(state_means.keys(), key=lambda s: state_means[s])  # low → high
    labels = {order[0]: "CALM", order[1]: "STRESS", order[2]: "CRISIS"}
    return labels, state_means
```

### 10.4 Real-time probabilities (filtered) vs retrospective (smoothed)
`hmmlearn` gives:
- `predict()` = Viterbi decoded path (hard)
- `predict_proba()` = posterior state probabilities (implementation-dependent; for GaussianHMM it is typically *smoothed*)

If you want strict filtered probabilities \(P(s_t\mid x_{1:t})\), implement the forward recursion with scaling.

### 10.5 Do you need a train/test split?
For SL‑FSI the honest answer is: **not in the way supervised ML does**, but you still want *some* out-of-sample discipline.

What’s meaningful:
- **likelihood holdout**: fit on early period, compare log-likelihood on later period (walk-forward)
- **event holdout**: don’t tune \(K\), \(\tau\), window \(W\) using the same events you report
- **stability tests**: refit on rolling windows and check if the 2021 STRESS onset remains roughly stable

What is *not* meaningful:
- random shuffle split (breaks time structure)
- claiming “generalization” from one crisis without additional countries or earlier crisis periods

---

## 11. Cheat sheets

### 11.1 What each parameter “means” in SL‑FSI
- \(\pi\): where your sample starts (almost surely CALM if you begin pre-crisis)
- \(A\): persistence and escalation/de-escalation pathways (CALM→STRESS→CRISIS)
- \(\mu_k\): “typical” feature levels in each regime
- \(\Sigma_k\): within-regime volatility (how noisy symptoms are in that regime)

### 11.2 A debugging checklist (when regimes look wrong)
1. Did you aggregate to the *true* information frequency?  
2. Are you accidentally fitting on forward-filled duplicates?  
3. Did you standardize?  
4. Are there enough observations per state (or did one state collapse to 1–2 months)?  
5. Did you run multiple restarts?  
6. Does the transition matrix imply absurd durations?  
7. Are regime means economically coherent (reserves lower in stress/crisis, inflation higher, etc.)?

### 11.3 What to add next if you want more “leading” behavior
- add FX pressure measures *if* you can avoid administered-price masking,
- add external financing conditions with robust coverage,
- or model the transition probabilities as a function of reserves / real rate (IOHMM style).

---

## 12. References

**Foundational**
- Rabiner, L.R. (1989). “A Tutorial on Hidden Markov Models and Selected Applications in Speech Recognition.” *Proceedings of the IEEE*.
- Baum, L.E. & Petrie, T. (1966). “Statistical Inference for Probabilistic Functions of Finite State Markov Chains.” *Annals of Mathematical Statistics*.

**Econometrics / regime switching**
- Hamilton, J.D. (1989). “A New Approach to the Economic Analysis of Nonstationary Time Series and the Business Cycle.” *Econometrica*.

**Extensions**
- HSMM and IOHMM literature (duration modeling; covariate-conditioned transitions)
- Heavy-tailed state space models (Student-t emissions)

---

*This doc is intentionally written so “HMM theory” and “SL‑FSI practice” are the same object. If you later change the repo model (e.g., HSMM, AR‑HMM), update Sections 2, 4, 6, and 9 first.*
