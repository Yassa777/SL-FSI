# SL-FSI Project Tutorial: Building a Financial Stress Index from Scratch

**Prerequisites**: Python, pandas, numpy, basic statistics, familiarity with time series
**Assumed**: Data gathering phase is complete - you have raw data files
**Outcome**: A working Financial Stress Index with regime detection for Sri Lanka

---

## Table of Contents

1. [Phase 1: Project Setup & Data Inventory](#phase-1-project-setup--data-inventory)
2. [Phase 2: Data Exploration & Quality Assessment](#phase-2-data-exploration--quality-assessment)
3. [Phase 3: Feature Engineering](#phase-3-feature-engineering)
4. [Phase 4: Model Selection](#phase-4-model-selection)
5. [Phase 5: HMM Implementation](#phase-5-hmm-implementation)
6. [Phase 6: Validation Framework](#phase-6-validation-framework)
7. [Phase 7: Cross-Country Extension](#phase-7-cross-country-extension)
8. [Phase 8: Robustness Testing](#phase-8-robustness-testing)
9. [Phase 9: Documentation & Synthesis](#phase-9-documentation--synthesis)

---

# Phase 1: Project Setup & Data Inventory

## Task 1.1: Create Project Structure

```
SL-FSI/
├── data/
│   ├── external/      # Raw data from sources (CBSL, DCS, CSE)
│   ├── merged/        # Processed panel datasets
│   └── cross_country/ # Pakistan, Ghana data (later)
├── scripts/           # Analysis scripts
├── docs/              # Documentation
└── outputs/           # Figures, tables
```

**Action**: Create this directory structure.

---

## Task 1.2: Inventory Your Raw Data

List all data files you have. For each file, document:

| File | Source | Frequency | Date Range | Variables |
|------|--------|-----------|------------|-----------|
| ? | ? | ? | ? | ? |

**❓ DECISION POINT 1.2.1**: What is your target analysis period?

- [ ] Full historical data (as far back as available)
- [ ] Crisis-focused period (e.g., 2020-2024 for Sri Lanka)
- [ ] Other: _______________

*Our choice*: 2020-01-01 to 2024-12-31 (covers pre-crisis, crisis, and recovery)

---

## Task 1.3: Identify Data Sources

For Sri Lanka FSI, we used:

| Category | Variable | Source | Notes |
|----------|----------|--------|-------|
| Money Market | AWCMR | CBSL | Average Weighted Call Money Rate |
| External Sector | FX Reserves | CBSL | Gross official reserves |
| Prices | Inflation | DCS | NCPI Year-over-Year |
| Interest Rates | Policy Rate | CBSL | Standing Lending Facility Rate |
| Equity Market | CSE Index | CSE | All Share Price Index |

**❓ DECISION POINT 1.3.1**: What categories should your FSI cover?

- [ ] Money market stress
- [ ] External sector vulnerability
- [ ] Price stability
- [ ] Banking sector health
- [ ] Equity market volatility
- [ ] Sovereign risk
- [ ] Other: _______________

*Our choice*: Money market, external sector, prices, interest rates (4 categories)

---

# Phase 2: Data Exploration & Quality Assessment

## Task 2.1: Load and Inspect Each Dataset

For EACH data file:

### Sub-task 2.1.1: Basic inspection
```python
df = pd.read_csv('your_file.csv')
print(f"Shape: {df.shape}")
print(f"Columns: {df.columns.tolist()}")
print(f"Date range: {df['date'].min()} to {df['date'].max()}")
print(f"Missing values:\n{df.isnull().sum()}")
```

### Sub-task 2.1.2: Check frequency
```python
df['date'] = pd.to_datetime(df['date'])
df = df.sort_values('date')
date_diffs = df['date'].diff().dt.days.value_counts()
print(f"Date differences:\n{date_diffs.head()}")
```

**❓ DECISION POINT 2.1.1**: What is the native frequency of each variable?

| Variable | Native Frequency |
|----------|------------------|
| AWCMR | Monthly |
| Reserves | Monthly |
| Inflation | Monthly |
| Equity prices | Daily |
| ? | ? |

---

## Task 2.2: Visualize Each Series

### Sub-task 2.2.1: Time series plots
```python
import matplotlib.pyplot as plt

fig, axes = plt.subplots(len(variables), 1, figsize=(12, 3*len(variables)))
for i, var in enumerate(variables):
    axes[i].plot(df['date'], df[var])
    axes[i].set_title(var)
    axes[i].axvline(pd.Timestamp('2022-04-12'), color='red', linestyle='--', label='Default')
plt.tight_layout()
plt.savefig('outputs/raw_series.png')
```

### Sub-task 2.2.2: Identify anomalies
Look for:
- [ ] Missing periods (gaps in data)
- [ ] Obvious outliers
- [ ] Structural breaks
- [ ] Data entry errors (e.g., decimal point issues)

**❓ DECISION POINT 2.2.1**: How will you handle missing data?

- [ ] Drop observations with any missing values
- [ ] Forward fill (carry last observation)
- [ ] Linear interpolation
- [ ] Leave as-is and handle in modeling
- [ ] Other: _______________

*Our choice*: Forward fill for monthly data (appropriate for slow-moving macro variables)

---

## Task 2.3: Assess Coverage During Crisis Period

### Sub-task 2.3.1: Calculate coverage
```python
crisis_start = '2022-01-01'
crisis_end = '2023-12-31'

crisis_data = df[(df['date'] >= crisis_start) & (df['date'] <= crisis_end)]

for var in variables:
    coverage = crisis_data[var].notna().mean() * 100
    print(f"{var}: {coverage:.1f}% coverage during crisis")
```

**❓ DECISION POINT 2.3.1**: What is your minimum acceptable coverage?

- [ ] 100% (no missing allowed)
- [ ] 90%+
- [ ] 80%+
- [ ] 50%+
- [ ] Any coverage is fine

*Our choice*: 100% coverage for core features (this eliminated some variables)

---

## Task 2.4: Document Data Quality Issues

Create a data quality log:

| Variable | Issue | Dates Affected | Resolution |
|----------|-------|----------------|------------|
| ? | ? | ? | ? |

---

# Phase 3: Feature Engineering

## Task 3.1: Decide on Analysis Frequency

**❓ DECISION POINT 3.1.1**: What frequency will you use for analysis?

- [ ] Daily (maximum granularity)
- [ ] Weekly (balance of granularity and noise)
- [ ] Monthly (matches most macro data)
- [ ] Quarterly (matches GDP, other quarterly data)

*Our choice*: Monthly - because most variables are monthly, and daily would require forward-filling which creates spurious autocorrelation

**Rationale for monthly**:
- Daily data had only ~60 unique observations (monthly data forward-filled)
- HMM detected noise, not regimes, on daily data
- Monthly gives 60 genuine observations for 5-year period

---

## Task 3.2: Create Derived Features

### Sub-task 3.2.1: Real policy rate
```python
df['real_policy_rate'] = df['policy_rate'] - df['inflation_yoy']
```

**❓ DECISION POINT 3.2.1**: What derived features make economic sense?

| Derived Feature | Formula | Economic Interpretation |
|-----------------|---------|------------------------|
| Real policy rate | Policy rate - Inflation | Monetary tightness |
| Reserve coverage | Reserves / Monthly imports | External buffer |
| Yield spread | Long rate - Short rate | Term structure stress |
| ? | ? | ? |

*Our choice*: Real policy rate (captures monetary conditions relative to inflation)

---

### Sub-task 3.2.2: Volatility measures (if using daily data)
```python
df['vol_equity_20d'] = df['equity_return'].rolling(20).std() * np.sqrt(252)
```

**❓ DECISION POINT 3.2.2**: If using volatility, what lookback period?

- [ ] 5 days (1 week)
- [ ] 20 days (1 month)
- [ ] 60 days (1 quarter)
- [ ] Other: _______________

*Our choice*: 20 days (standard for financial volatility)

---

## Task 3.3: Merge Into Panel Dataset

### Sub-task 3.3.1: Align all series to common dates
```python
# Create date range
dates = pd.date_range(start='2020-01-01', end='2024-12-31', freq='MS')

# Initialize panel
panel = pd.DataFrame({'date': dates})

# Merge each series
for name, df in data_sources.items():
    panel = panel.merge(df[['date', variable]], on='date', how='left')
```

### Sub-task 3.3.2: Handle remaining missing values
```python
# Check missingness
print(panel.isnull().sum())

# Forward fill
panel = panel.fillna(method='ffill')

# Check if any NaN remain at start
print(panel.head())
```

### Sub-task 3.3.3: Save merged panel
```python
panel.to_csv('data/merged/slfsi_monthly_panel.csv', index=False)
```

---

## Task 3.4: Select Final Feature Set

### Sub-task 3.4.1: Check correlations
```python
import seaborn as sns

corr = panel[feature_candidates].corr()
sns.heatmap(corr, annot=True, cmap='coolwarm')
plt.savefig('outputs/feature_correlations.png')
```

**❓ DECISION POINT 3.4.1**: How will you handle highly correlated features?

- [ ] Keep all (let model handle multicollinearity)
- [ ] Remove if correlation > 0.9
- [ ] Remove if correlation > 0.7
- [ ] Use PCA to combine
- [ ] Other: _______________

### Sub-task 3.4.2: Select features based on coverage and relevance

**❓ DECISION POINT 3.4.2**: What is your final feature set?

| Feature | Category | Coverage | Rationale |
|---------|----------|----------|-----------|
| ? | ? | ? | ? |

*Our choice*:
| Feature | Category | Coverage | Rationale |
|---------|----------|----------|-----------|
| awcmr | Money Market | 100% | Interbank stress signal |
| real_policy_rate | Interest Rates | 100% | Monetary conditions |
| gross_reserves_usd_m | External | 100% | FX buffer |
| ncpi_yoy_pct | Prices | 100% | Inflation pressure |

---

# Phase 4: Model Selection

## Task 4.1: Define What You're Trying to Detect

**❓ DECISION POINT 4.1.1**: What is a "financial stress regime"?

Write your definition:
> A financial stress regime is characterized by...

*Our definition*: A financial stress regime is characterized by elevated interbank rates, depleting reserves, high inflation, and deeply negative real interest rates - conditions that indicate loss of monetary control and external vulnerability.

---

## Task 4.2: Consider Alternative Approaches

### Sub-task 4.2.1: List candidate methodologies

| Method | Pros | Cons |
|--------|------|------|
| Simple threshold rules | Interpretable, no training | Arbitrary thresholds |
| Composite index (weighted average) | Easy to compute | Weights are arbitrary |
| Principal Component Analysis | Data-driven weights | No regime detection |
| Hidden Markov Model | Data-driven regimes, probabilistic | Harder to interpret |
| K-means clustering | Simple, interpretable | No temporal structure |
| Markov-switching regression | Regime-dependent relationships | More complex |

**❓ DECISION POINT 4.2.1**: Which method(s) will you use?

- [ ] Simple thresholds only
- [ ] Composite index only
- [ ] HMM only
- [ ] Combination (specify): _______________

*Our choice*: HMM as primary method, with threshold analysis for validation

**Rationale**: HMM captures:
1. Latent regimes (we don't observe "stress" directly)
2. Temporal persistence (regimes tend to last)
3. Probabilistic transitions (gradual not sudden)

---

## Task 4.3: Decide Number of States

### Sub-task 4.3.1: What states make economic sense?

**❓ DECISION POINT 4.3.1**: How many regimes should exist?

- [ ] 2 states: Normal vs Crisis
- [ ] 3 states: Calm vs Stress vs Crisis
- [ ] 4 states: Calm vs Mild Stress vs Severe Stress vs Crisis
- [ ] Let data decide (information criteria)

*Our choice*: 3 states (CALM, STRESS, CRISIS)

**Rationale**:
- 2 states conflates "building stress" with "acute crisis"
- 3 states allows early warning (detect STRESS before CRISIS)
- More states may overfit with limited data

### Sub-task 4.3.2: Test empirically
```python
from sklearn.metrics import silhouette_score

for n_states in [2, 3, 4]:
    model = GaussianHMM(n_components=n_states, ...)
    model.fit(X)
    states = model.predict(X)

    # BIC
    bic = -2 * model.score(X) + n_params * np.log(n_obs)

    # Silhouette
    sil = silhouette_score(X, states)

    print(f"{n_states} states: BIC={bic:.0f}, Silhouette={sil:.3f}")
```

---

## Task 4.4: Decide on Covariance Structure

**❓ DECISION POINT 4.4.1**: What covariance type for HMM?

- [ ] Full (separate covariance matrix per state)
- [ ] Diagonal (features independent within state)
- [ ] Spherical (equal variance across features)
- [ ] Tied (same covariance across states)

*Our choice*: Diagonal

**Rationale**:
- Full covariance: n_states × (n_features² + n_features)/2 parameters
- Diagonal: n_states × n_features parameters
- With 60 observations and 4 features, diagonal is more stable

---

# Phase 5: HMM Implementation

## Task 5.1: Prepare Data for HMM

### Sub-task 5.1.1: Extract feature matrix
```python
features = ['awcmr', 'real_policy_rate', 'gross_reserves_usd_m', 'ncpi_yoy_pct']
X = panel[features].values
```

### Sub-task 5.1.2: Scale features

**❓ DECISION POINT 5.1.1**: How will you scale?

- [ ] No scaling
- [ ] Z-score standardization (mean=0, std=1)
- [ ] Min-max normalization (0 to 1)
- [ ] Robust scaling (median, IQR)

*Our choice*: Z-score standardization

```python
X_scaled = (X - X.mean(axis=0)) / X.std(axis=0)
```

---

## Task 5.2: Fit HMM

### Sub-task 5.2.1: Initialize and fit model
```python
from hmmlearn import hmm

model = hmm.GaussianHMM(
    n_components=3,          # Number of states
    covariance_type="diag",  # Diagonal covariance
    n_iter=300,              # Max iterations
    random_state=42          # For reproducibility
)

model.fit(X_scaled)
```

### Sub-task 5.2.2: Check convergence
```python
print(f"Converged: {model.monitor_.converged}")
print(f"Final log-likelihood: {model.score(X_scaled):.2f}")
```

**❓ DECISION POINT 5.2.1**: What if model doesn't converge?

- [ ] Increase n_iter
- [ ] Try different random_state
- [ ] Simplify model (fewer states, simpler covariance)
- [ ] Check data for issues

---

## Task 5.3: Extract and Interpret Results

### Sub-task 5.3.1: Get state assignments
```python
states = model.predict(X_scaled)
panel['regime'] = states
```

### Sub-task 5.3.2: Calculate state characteristics
```python
for state in range(3):
    mask = panel['regime'] == state
    print(f"\nState {state} (n={mask.sum()}):")
    for feat in features:
        print(f"  {feat}: {panel[mask][feat].mean():.2f}")
```

### Sub-task 5.3.3: Label states by severity

**❓ DECISION POINT 5.3.1**: How will you assign labels to states?

- [ ] Manual inspection of means
- [ ] Sort by single variable (e.g., inflation)
- [ ] Sort by composite severity score
- [ ] Other: _______________

*Our choice*: Sort by severity score = inflation - real_policy_rate (higher = worse)

```python
severity = {}
for state in range(3):
    mask = panel['regime'] == state
    severity[state] = (panel[mask]['ncpi_yoy_pct'].mean() -
                       panel[mask]['real_policy_rate'].mean())

# Map: lowest severity = CALM, highest = CRISIS
sorted_states = sorted(severity.items(), key=lambda x: x[1])
label_map = {
    sorted_states[0][0]: 'CALM',
    sorted_states[1][0]: 'STRESS',
    sorted_states[2][0]: 'CRISIS'
}
panel['regime_label'] = panel['regime'].map(label_map)
```

---

## Task 5.4: Visualize Regime Timeline

### Sub-task 5.4.1: Create timeline plot
```python
fig, ax = plt.subplots(figsize=(14, 4))

colors = {'CALM': 'green', 'STRESS': 'orange', 'CRISIS': 'red'}
for regime in ['CALM', 'STRESS', 'CRISIS']:
    mask = panel['regime_label'] == regime
    ax.scatter(panel[mask]['date'], [1]*mask.sum(),
               c=colors[regime], label=regime, s=100)

ax.set_title('Detected Regimes Over Time')
ax.legend()
plt.savefig('outputs/regime_timeline.png')
```

### Sub-task 5.4.2: Identify regime transitions
```python
transitions = panel[panel['regime'].diff() != 0][['date', 'regime_label']]
print("Regime transitions:")
print(transitions.to_string(index=False))
```

---

## Task 5.5: Extract Transition Matrix

### Sub-task 5.5.1: Get transition probabilities
```python
print("Transition matrix:")
print(model.transmat_.round(3))
```

### Sub-task 5.5.2: Interpret
```
From/To   CALM   STRESS   CRISIS
CALM      0.95   0.05     0.00
STRESS    0.10   0.85     0.05
CRISIS    0.00   0.10     0.90
```

**❓ DECISION POINT 5.5.1**: Does the transition matrix make sense?

- [ ] Yes - regimes are persistent and transitions are gradual
- [ ] Partially - some unexpected transitions
- [ ] No - transitions seem random

*Sanity checks*:
- Diagonal should be high (regimes persist)
- CALM → CRISIS directly should be rare/zero
- CRISIS → CALM directly should be rare/zero

---

# Phase 6: Validation Framework

## Task 6.1: Define Ground Truth Events

### Sub-task 6.1.1: List known crisis events
```python
events = pd.DataFrame({
    'date': pd.to_datetime([
        '2022-03-07',  # FX float
        '2022-04-12',  # Debt default announcement
        '2022-07-14',  # President resignation
        '2022-09-15',  # Peak inflation
        '2023-03-20',  # IMF program approval
    ]),
    'event': [
        'Currency float',
        'Debt default',
        'President resigns',
        'Peak inflation (69.8%)',
        'IMF EFF approved'
    ],
    'expected_regime': ['CRISIS', 'CRISIS', 'CRISIS', 'CRISIS', 'STRESS']
})
```

**❓ DECISION POINT 6.1.1**: What events should the model detect?

List your events:
| Date | Event | Expected Regime |
|------|-------|-----------------|
| ? | ? | ? |

---

## Task 6.2: Calculate Event Detection Rate

### Sub-task 6.2.1: Match events to regimes
```python
def get_regime_at_date(date, panel):
    # Find closest date
    idx = (panel['date'] - date).abs().idxmin()
    return panel.loc[idx, 'regime_label']

events['detected_regime'] = events['date'].apply(
    lambda d: get_regime_at_date(d, panel)
)

events['hit'] = events['detected_regime'] == events['expected_regime']
hit_rate = events['hit'].mean() * 100
print(f"Event detection rate: {hit_rate:.0f}%")
```

**❓ DECISION POINT 6.2.1**: What is acceptable detection rate?

- [ ] 100% (must catch everything)
- [ ] 80%+ (good)
- [ ] 60%+ (acceptable)
- [ ] Any improvement over random

*Our target*: 80%+ event detection

---

## Task 6.3: Calculate Early Warning Lead Time

### Sub-task 6.3.1: Find first crisis detection
```python
# When did model first detect CRISIS?
first_crisis = panel[panel['regime_label'] == 'CRISIS']['date'].min()

# When did actual default occur?
default_date = pd.Timestamp('2022-04-12')

# Lead time
lead_days = (default_date - first_crisis).days
print(f"Early warning: {lead_days} days before default")
```

### Sub-task 6.3.2: Find first stress detection
```python
first_stress = panel[panel['regime_label'] == 'STRESS']['date'].min()
stress_lead = (default_date - first_stress).days
print(f"STRESS detected {stress_lead} days before default")
```

**❓ DECISION POINT 6.3.1**: Is the early warning useful?

- [ ] Yes - sufficient time for policy action
- [ ] Partially - some warning but short
- [ ] No - too late to be useful

---

## Task 6.4: Check for False Positives

### Sub-task 6.4.1: Were there CRISIS detections during calm periods?
```python
calm_period = panel[panel['date'] < '2021-01-01']  # Definitely calm
false_crises = (calm_period['regime_label'] == 'CRISIS').sum()
print(f"False CRISIS detections in calm period: {false_crises}")
```

**❓ DECISION POINT 6.4.1**: How many false positives are acceptable?

- [ ] Zero (no false alarms)
- [ ] 1-2 (rare)
- [ ] Any, as long as true positives are high

---

# Phase 7: Cross-Country Extension

## Task 7.1: Identify Comparison Countries

**❓ DECISION POINT 7.1.1**: What countries have similar crises?

Criteria for selection:
- [ ] Similar crisis type (balance of payments)
- [ ] Similar time period (2020-2024)
- [ ] Data availability
- [ ] IMF program involvement

*Our choice*: Pakistan (2022-2023), Ghana (2022-2023)

**Rationale**: Both had reserve crises, high inflation, IMF programs during similar period.

---

## Task 7.2: Assess Data Availability

### Sub-task 7.2.1: Map equivalent variables

| Sri Lanka Variable | Pakistan Equivalent | Ghana Equivalent | Source |
|--------------------|--------------------|--------------------|--------|
| AWCMR | KIBOR | BoG Interbank Rate | SBP / BoG |
| Gross Reserves | SBP Reserves | BoG Gross Reserves | SBP / BoG |
| NCPI YoY | CPI YoY | CPI YoY | PBS / GSS |
| Policy Rate | SBP Policy Rate | BoG Policy Rate | SBP / BoG |

### Sub-task 7.2.2: Assess actual data quality

**❓ CRITICAL DECISION POINT 7.2.1**: Do you have actual monthly data or estimates?

- [ ] Actual monthly data from official sources
- [ ] Quarterly data interpolated to monthly
- [ ] Annual data with monthly estimates
- [ ] Mix of actual and estimated

**⚠️ WARNING**: If using estimates/interpolation, your claims about cross-country validation will be LIMITED.

*Our experience*: We used interpolated data and found:
- 25-34% error vs World Bank annual data
- This undermined our "methodology generalizes" claim

---

## Task 7.3: Apply Same Methodology

### Sub-task 7.3.1: Prepare country data
```python
# Same features, same scaling, same model
X_pk = pakistan[features].values
X_pk_scaled = (X_pk - X_pk.mean(axis=0)) / X_pk.std(axis=0)
```

### Sub-task 7.3.2: Fit HMM with same specification
```python
model_pk = hmm.GaussianHMM(
    n_components=3,
    covariance_type="diag",
    n_iter=300,
    random_state=42
)
model_pk.fit(X_pk_scaled)
```

**❓ DECISION POINT 7.3.1**: Should you use same random seed or let model find best fit?

- [ ] Same seed (for comparability)
- [ ] Multiple seeds, take best (for best fit)
- [ ] Multiple seeds, report variation (for robustness)

*Our recommendation*: Multiple seeds, report variation - this revealed our model was unstable.

---

## Task 7.4: Validate Cross-Country Results

### Sub-task 7.4.1: Compare against actual data
```python
# Get World Bank annual data as ground truth
wb_data = fetch_world_bank_data(country, indicators)

# Compare to your estimates
error = (your_estimate - wb_actual) / wb_actual * 100
print(f"Mean absolute error: {abs(error).mean():.1f}%")
```

**❓ CRITICAL DECISION POINT 7.4.1**: Is data quality sufficient for claims?

| Error Level | Implication |
|-------------|-------------|
| <10% | Can make quantitative claims |
| 10-20% | Qualitative claims only |
| >20% | Proof of concept only |

---

# Phase 8: Robustness Testing

## Task 8.1: Test Seed Sensitivity

### Sub-task 8.1.1: Run with multiple seeds
```python
all_states = []
for seed in range(10):
    model = hmm.GaussianHMM(..., random_state=seed)
    model.fit(X_scaled)
    states = model.predict(X_scaled)
    all_states.append(states)

# Calculate agreement
all_states = np.array(all_states)
mode_states = np.apply_along_axis(
    lambda x: np.bincount(x, minlength=3).argmax(),
    0, all_states
)
agreement = np.mean([np.mean(s == mode_states) for s in all_states])
print(f"Cross-seed agreement: {agreement*100:.1f}%")
```

**❓ DECISION POINT 8.1.1**: What agreement level is acceptable?

- [ ] >90% (highly stable)
- [ ] >80% (reasonably stable)
- [ ] >70% (marginally stable)
- [ ] <70% (UNSTABLE - reconsider approach)

*Our finding*: 66-70% agreement - model was UNSTABLE

---

## Task 8.2: Test Model Specification

### Sub-task 8.2.1: Compare 2, 3, 4 state models
```python
for n_states in [2, 3, 4]:
    model = hmm.GaussianHMM(n_components=n_states, ...)
    model.fit(X_scaled)

    # Calculate BIC
    n_params = n_states * (n_features + n_features + n_states)
    bic = -2 * model.score(X_scaled) + n_params * np.log(len(X))

    print(f"{n_states} states: BIC = {bic:.0f}")
```

**❓ DECISION POINT 8.2.1**: Does BIC support your choice?

- [ ] Yes - chosen model has lowest BIC
- [ ] No - different model has lower BIC
- [ ] Ambiguous - models are similar

*Our finding*: BIC suggested 4 states, not 3 - our choice was imposed, not data-driven.

---

## Task 8.3: Test Data Sensitivity

### Sub-task 8.3.1: Perturb data and re-estimate
```python
# Add noise to reserves (simulate measurement error)
for noise_pct in [5, 10, 20]:
    X_noisy = X.copy()
    X_noisy[:, reserves_col] *= (1 + np.random.normal(0, noise_pct/100, len(X)))

    model.fit(scale(X_noisy))
    new_states = model.predict(scale(X_noisy))

    agreement = np.mean(new_states == original_states)
    print(f"{noise_pct}% noise: {agreement*100:.1f}% agreement")
```

**❓ DECISION POINT 8.3.1**: How sensitive are results to data quality?

| Sensitivity | Implication |
|-------------|-------------|
| <20% change with 10% noise | Robust |
| 20-50% change | Moderately sensitive |
| >50% change | HIGHLY sensitive |

---

## Task 8.4: Document Robustness Findings

Create robustness summary:

| Test | Result | Implication |
|------|--------|-------------|
| Seed sensitivity | ?% agreement | ? |
| Model selection | ? state optimal | ? |
| Data sensitivity | ?% change | ? |

**❓ CRITICAL DECISION POINT 8.4.1**: Are your claims supported by robustness tests?

- [ ] Yes - results are stable across tests
- [ ] Partially - some sensitivity identified
- [ ] No - results are highly sensitive

*Our finding*: Results were NOT robust. Claims needed significant qualification.

---

# Phase 9: Documentation & Synthesis

## Task 9.1: Document What Works

### Sub-task 9.1.1: Summarize validated findings
```
SUPPORTED CLAIMS:
1. [Claim with evidence]
2. [Claim with evidence]
...
```

### Sub-task 9.1.2: Summarize limitations
```
LIMITATIONS:
1. [Limitation and impact]
2. [Limitation and impact]
...
```

---

## Task 9.2: Create Final Outputs

### Sub-task 9.2.1: Save regime assignments
```python
panel[['date', 'regime', 'regime_label'] + features].to_csv(
    'data/merged/final_regime_assignments.csv', index=False
)
```

### Sub-task 9.2.2: Create summary statistics table
```python
summary = panel.groupby('regime_label')[features].agg(['mean', 'std'])
summary.to_csv('outputs/regime_characteristics.csv')
```

### Sub-task 9.2.3: Generate figures for paper
- [ ] Regime timeline figure
- [ ] Feature evolution during crisis
- [ ] Transition probability heatmap
- [ ] Cross-country comparison (if valid)

---

## Task 9.3: Write Methods Section

Document your choices:

```
We employ a [N]-state Gaussian Hidden Markov Model with [covariance type]
covariance. Features include [list features] at [frequency] frequency
over the period [date range]. Data is standardized using [method].

Model selection was performed using [criteria]. Regime labels were
assigned based on [method].

Validation includes: [list validation approaches].

Limitations: [list key limitations].
```

---

## Task 9.4: Final Checklist

Before claiming results:

- [ ] Model converged
- [ ] Regime labels make economic sense
- [ ] Key events detected
- [ ] Results stable across random seeds (>80% agreement)
- [ ] Model specification supported by BIC/AIC
- [ ] Data quality sufficient for claims
- [ ] Limitations documented

**If any box is unchecked, qualify your claims accordingly.**

---

# Appendix: Our Actual Results Summary

## What Worked (Sri Lanka)

| Aspect | Finding |
|--------|---------|
| Model | 3-state HMM on monthly data |
| Features | AWCMR, real policy rate, reserves, inflation |
| Early warning | STRESS detected July 2021 (9 months before default) |
| Event detection | 4/4 key events correctly classified |
| Regime persistence | Only 4 transitions (clean, interpretable) |

## What Didn't Work (Cross-Country)

| Aspect | Finding |
|--------|---------|
| Data quality | 25-34% error vs World Bank |
| Model stability | 66-70% agreement across seeds |
| Model selection | BIC suggested 4 states, not 3 |
| Data sensitivity | 80% regime changes with correction |
| Conclusion | Proof of concept only, not validation |

## Honest Claims

**Can claim**:
- HMM methodology works for Sri Lanka FSI
- Same features appear relevant across EMs
- Similar crisis patterns exist (qualitatively)

**Cannot claim**:
- Methodology validated across countries
- Specific event detection rates for Pakistan/Ghana
- Early warning lead times for other countries

---

*End of Tutorial*

**Total estimated time**: 20-40 hours depending on data availability and familiarity with tools.

**Key lesson**: Rigorous validation often reveals limitations. This is valuable - better to know than to overclaim.
