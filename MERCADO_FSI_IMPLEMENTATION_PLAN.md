# Mercado-Park FSI Implementation Plan for Sri Lanka

**Reference**: Park, C.Y. & Mercado, R. (2014). "Determinants of Financial Stress in Emerging Market Economies." *Journal of Banking and Finance*, 45, pp. 199-224.

**Source**: [ADB ARIC FSI Database](https://aric.adb.org/database/fsi)

---

## Executive Summary

The Mercado-Park Financial Stress Index (FSI) is a composite index measuring stress across **4 financial markets** using **5 components**. This is the methodology used by the Asian Development Bank for emerging market FSIs, including Sri Lanka.

**Goal**: Implement the official Mercado FSI methodology for Sri Lanka and compare to our HMM-based regime detection.

---

## Part 1: Methodology Overview

### The 5 Components

| # | Component | Market | Formula | Stress Interpretation |
|---|-----------|--------|---------|----------------------|
| 1 | **Banking Beta (β)** | Banking | β = Cov(r_bank, r_market) / Var(r_market) | Higher β = more stress |
| 2 | **Equity Returns** | Equity | r_t = ln(P_t) - ln(P_{t-1}) | Lower/negative = more stress |
| 3 | **Equity Volatility** | Equity | GARCH(1,1) on returns | Higher σ² = more stress |
| 4 | **Debt Spread** | Debt | Spread = Y_10Y - Y_2Y | Wider spread = more stress |
| 5 | **EMPI** | FX | See formula below | Higher EMPI = more stress |

### Aggregation Method

1. **Standardize** each component (z-score)
2. Apply **variance-equal weights** (simple average) OR
3. Use **Principal Component Analysis** (first PC)

---

## Part 2: Detailed Component Specifications

### Component 1: Banking Sector Beta (β)

**Concept**: Measures banking sector's sensitivity to overall market movements. High beta indicates banks are more exposed to systemic risk.

**Formula**:
```
β_t = Cov(r_bank, r_market)_t / Var(r_market)_t
```

**Implementation**:
```python
def calculate_banking_beta(bank_returns, market_returns, window=36):
    """
    Calculate rolling banking sector beta.

    Parameters:
    - bank_returns: Returns of banking sector index
    - market_returns: Returns of overall market index (ASPI)
    - window: Rolling window in months (default 36 = 3 years)

    Returns:
    - Series of beta values
    """
    beta = []
    for t in range(window, len(bank_returns)):
        r_bank = bank_returns[t-window:t]
        r_market = market_returns[t-window:t]

        cov = np.cov(r_bank, r_market)[0, 1]
        var = np.var(r_market, ddof=1)

        beta.append(cov / var if var > 0 else np.nan)

    return pd.Series(beta, index=bank_returns.index[window:])
```

**Data Required**:
- Banking sector stock index (or bank stock portfolio)
- Overall market index (ASPI for Sri Lanka)

**❓ DECISION POINT**: Do we have a banking sector sub-index for CSE?
- Option A: Use bank stock portfolio (Commercial Bank, Sampath, HNB, etc.)
- Option B: Use financial sector index if available
- Option C: Construct equal-weighted bank index

---

### Component 2: Equity Market Returns

**Concept**: Simple log returns of the equity market. Negative returns indicate stress.

**Formula**:
```
r_t = ln(P_t) - ln(P_{t-1})
```

**Implementation**:
```python
def calculate_equity_returns(prices):
    """
    Calculate log returns of equity index.

    Parameters:
    - prices: Series of equity index values

    Returns:
    - Series of log returns
    """
    returns = np.log(prices) - np.log(prices.shift(1))
    return returns
```

**Data Required**:
- ASPI (All Share Price Index) - monthly closing values

**Note**: For stress index, we often use **inverted returns** (multiply by -1) so higher = more stress.

---

### Component 3: Equity Market Volatility (GARCH)

**Concept**: Time-varying volatility captures uncertainty. Higher volatility = more stress.

**Formula** (GARCH(1,1)):
```
σ²_t = ω + α·ε²_{t-1} + β·σ²_{t-1}
```

where ε_t is the residual from: r_t = μ + ε_t

**Implementation**:
```python
from arch import arch_model

def calculate_garch_volatility(returns):
    """
    Fit GARCH(1,1) model and extract conditional volatility.

    Parameters:
    - returns: Series of equity returns

    Returns:
    - Series of conditional volatility (sigma)
    """
    # Scale returns to percentage for numerical stability
    returns_pct = returns * 100

    # Fit GARCH(1,1)
    model = arch_model(returns_pct, vol='Garch', p=1, q=1, mean='Constant')
    result = model.fit(disp='off')

    # Extract conditional volatility
    cond_vol = result.conditional_volatility / 100  

    return cond_vol
```

**Data Required**:v
- Equity returns (from Component 2)

**Installation**: `pip install arch`

---

### Component 4: Sovereign Debt Spread

**Concept**: Yield curve slope. Wider spread between long and short rates indicates stress (flight to safety, term premium).

**Formula**:
```
Spread_t = Y_{10Y,t} - Y_{2Y,t}
```

**Implementation**:
```python
def calculate_debt_spread(yield_10y, yield_2y):
    """
    Calculate sovereign debt spread (yield curve slope).

    Parameters:
    - yield_10y: 10-year government bond yield
    - yield_2y: 2-year government bond yield

    Returns:
    - Series of spread values
    """
    spread = yield_10y - yield_2y
    return spread
```

**Data Required**:
- 10-year government bond yield (or longest available: 5Y, 15Y)
- 2-year government bond yield (or T-bill rate as proxy)

**Sri Lanka Data Sources**:
- CBSL Treasury bill/bond auction results
- Primary dealer rates
- `tbond_yield` and `tbill_secondary` from our dataset

**❓ DECISION POINT**: Sri Lanka yield curve data availability?
- Option A: Use 10Y bond - 1Y T-bill
- Option B: Use 5Y bond - 3M T-bill

---

## Implementation Notes (Data Hygiene + Fallbacks)

- **ASPI/SL20 zero placeholders**: Zero values in `data/processed/D3_aspi.csv` and `data/processed/D6_D7_sl20_gold.csv` are treated as missing (set to NaN) before merging, since they coincide with non-trading days and break log-return calculations.
- **Sovereign spread fallback**: If the T-bond/T-bill spread has fewer than 36 monthly observations, use `embi_spread_approx` (ISB yield - US 10Y, stored in bps and converted to percent in `mercado_fsi.py`). This improves coverage from late-2022-only to 2021-2024.
- **Monthly sampling**: `mercado_fsi.py` now reads `data/merged/slfsi_monthly_panel.csv` directly to avoid month-start resampling artifacts from daily data.
- Option C: Use available spread approximation

---

### Component 5: Exchange Market Pressure Index (EMPI)

**Concept**: Combines currency depreciation and reserve depletion. Both indicate FX market stress.

**Formula**:
```
EMPI_t = [(Δe_t - μ_Δe) / σ_Δe] - [(ΔRES_t - μ_ΔRES) / σ_ΔRES]
```

where:
- Δe_t = month-on-month % change in exchange rate (LKR/USD)
- ΔRES_t = month-on-month % change in foreign reserves
- μ, σ = historical mean and standard deviation

**Note**: Depreciation (+) adds stress, Reserve increase (-) reduces stress. The minus sign before the reserves term means reserve LOSS adds stress.

**Implementation**:
```python
def calculate_empi(exchange_rate, reserves, lookback=60):
    """
    Calculate Exchange Market Pressure Index.

    Parameters:
    - exchange_rate: LKR per USD (higher = weaker LKR)
    - reserves: Foreign exchange reserves (USD)
    - lookback: Months for calculating mean/std (default 60 = 5 years)

    Returns:
    - Series of EMPI values
    """
    # Calculate month-on-month percent changes
    delta_e = exchange_rate.pct_change() * 100  # % depreciation
    delta_res = reserves.pct_change() * 100      # % reserve change

    # Rolling mean and std (or use full sample)
    mu_e = delta_e.rolling(lookback, min_periods=12).mean()
    sigma_e = delta_e.rolling(lookback, min_periods=12).std()

    mu_res = delta_res.rolling(lookback, min_periods=12).mean()
    sigma_res = delta_res.rolling(lookback, min_periods=12).std()

    # Standardize
    z_e = (delta_e - mu_e) / sigma_e
    z_res = (delta_res - mu_res) / sigma_res

    # EMPI: depreciation adds stress, reserve loss adds stress
    empi = z_e - z_res  # Note: reserve INCREASE (positive) REDUCES empi

    return empi
```

**Data Required**:
- USD/LKR exchange rate (monthly average or end-of-month)
- Foreign exchange reserves (USD millions)

**We have**:
- `usd_lkr` in our dataset ✓
- `gross_reserves_usd_m` in our dataset ✓

---

## Part 3: Aggregation

### Method 1: Variance-Equal Weights (Simple)

```python
def aggregate_fsi_variance_equal(components_df):
    """
    Aggregate FSI components using variance-equal weights.

    Each component is standardized (z-score) then averaged.
    """
    # Standardize each component
    standardized = (components_df - components_df.mean()) / components_df.std()

    # Simple average
    fsi = standardized.mean(axis=1)

    return fsi
```

### Method 2: Principal Component Analysis

```python
from sklearn.decomposition import PCA

def aggregate_fsi_pca(components_df):
    """
    Aggregate FSI components using first principal component.
    """
    # Standardize
    standardized = (components_df - components_df.mean()) / components_df.std()

    # Remove NaN rows for PCA
    valid_data = standardized.dropna()

    # Fit PCA
    pca = PCA(n_components=1)
    pc1 = pca.fit_transform(valid_data)

    # Create series with original index
    fsi = pd.Series(pc1.flatten(), index=valid_data.index)

    # Explained variance
    print(f"PC1 explains {pca.explained_variance_ratio_[0]*100:.1f}% of variance")

    return fsi
```

---

## Part 4: Data Requirements Checklist

### Required Data for Sri Lanka

| Component | Variable | Our Dataset | Coverage | Status |
|-----------|----------|-------------|----------|--------|
| Banking β | Bank stock returns | Need to construct | ? | ⚠️ |
| Banking β | ASPI returns | `aspi` | ✓ | ✓ |
| Equity Returns | ASPI | `aspi` | ✓ | ✓ |
| Equity Volatility | ASPI returns | Derived | ✓ | ✓ |
| Debt Spread | 10Y yield | `tbond_yield` | Partial | ⚠️ |
| Debt Spread | 2Y yield | `tbill_secondary` | ✓ | ✓ |
| EMPI | USD/LKR | `usd_lkr` | ✓ | ✓ |
| EMPI | Reserves | `gross_reserves_usd_m` | ✓ | ✓ |

### Data Gaps to Address

1. **Banking Sector Index**:
   - CSE doesn't publish sector sub-indices easily
   - Solution: Construct from top 5 bank stocks (Commercial Bank, Sampath, HNB, NDB, Seylan)

2. **Long-term Bond Yields**:
   - May have gaps in 10Y yield data
   - Solution: Use longest available (5Y) or T-bill as short end

---

## Part 5: Implementation Steps

### Step 1: Data Preparation (1-2 hours)

```python
# Load existing data
daily = pd.read_csv('data/merged/slfsi_daily_panel.csv', parse_dates=['date'])

# Convert to monthly
monthly = daily.groupby(daily['date'].dt.to_period('M')).last().reset_index()

# Extract required series
aspi = monthly['aspi']
usd_lkr = monthly['usd_lkr']
reserves = monthly['gross_reserves_usd_m']
tbill = monthly['tbill_secondary']
tbond = monthly.get('tbond_yield', monthly['tbill_secondary'])  # fallback
```

### Step 2: Calculate Each Component (2-3 hours)

```python
# Component 1: Banking Beta
bank_returns = ...  # Need to construct
market_returns = np.log(aspi).diff()
banking_beta = calculate_banking_beta(bank_returns, market_returns)

# Component 2: Equity Returns (inverted for stress)
equity_returns = np.log(aspi).diff()
equity_stress = -equity_returns  # Invert so higher = more stress

# Component 3: Equity Volatility
equity_vol = calculate_garch_volatility(equity_returns)

# Component 4: Debt Spread
debt_spread = tbond - tbill

# Component 5: EMPI
empi = calculate_empi(usd_lkr, reserves)
```

### Step 3: Aggregate Components (30 min)

```python
# Combine into DataFrame
components = pd.DataFrame({
    'banking_beta': banking_beta,
    'equity_stress': equity_stress,
    'equity_vol': equity_vol,
    'debt_spread': debt_spread,
    'empi': empi
}, index=monthly['date'])

# Aggregate
fsi_var_equal = aggregate_fsi_variance_equal(components)
fsi_pca = aggregate_fsi_pca(components)
```

### Step 4: Validate Against ARIC Data (1 hour)

```python
# Download official FSI from ARIC
aric_fsi = pd.read_csv('data/external/aric_fsi_sri_lanka.csv')

# Compare
correlation = fsi_var_equal.corr(aric_fsi['fsi'])
print(f"Correlation with official ARIC FSI: {correlation:.3f}")

# Plot comparison
fig, ax = plt.subplots(figsize=(12, 5))
ax.plot(fsi_var_equal, label='Our Implementation')
ax.plot(aric_fsi['fsi'], label='Official ARIC')
ax.legend()
plt.savefig('outputs/fsi_validation.png')
```

### Step 5: Compare to HMM Regimes (1 hour)

```python
# Load HMM regimes
hmm_regimes = pd.read_csv('data/merged/hmm_regimes_3state_monthly.csv')

# Add FSI
hmm_regimes['mercado_fsi'] = fsi_var_equal

# Compare: What is FSI value in each regime?
for regime in ['CALM', 'STRESS', 'CRISIS']:
    mask = hmm_regimes['regime_label'] == regime
    avg_fsi = hmm_regimes[mask]['mercado_fsi'].mean()
    print(f"{regime}: Mean FSI = {avg_fsi:.2f}")

# Correlation between FSI and regime severity
# (regime coded as 0=CALM, 1=STRESS, 2=CRISIS)
corr = hmm_regimes['regime'].corr(hmm_regimes['mercado_fsi'])
print(f"Correlation (HMM regime vs FSI): {corr:.3f}")
```

---

## Part 6: Expected Outcomes

### Validation Criteria

| Criterion | Target | Method |
|-----------|--------|--------|
| Correlation with ARIC | >0.8 | Compare to official |
| Crisis detection | FSI > 1 in crisis | Check 2022 values |
| HMM alignment | Positive correlation | Regime vs FSI |
| Economic sensibility | FSI rises before default | Visual inspection |

### Research Questions

1. **Does Mercado FSI detect crisis early?**
   - When did FSI first exceed 1.0 (or 2 std above mean)?
   - Compare to HMM STRESS detection date (July 2021)

2. **Which component drove the crisis?**
   - Decompose FSI during 2021-2022
   - Hypothesis: EMPI (reserves/FX) led, followed by banking beta

3. **How does continuous FSI compare to discrete HMM regimes?**
   - Mercado FSI: Continuous (good for monitoring)
   - HMM Regimes: Discrete (good for policy triggers)
   - Both have value - complementary approaches

4. **Can we improve the Mercado FSI?**
   - Add AWCMR (interbank stress) - our key HMM feature
   - Create "Mercado+" with 6 components

---

## Part 7: Timeline & Deliverables

### Timeline

| Phase | Task | Time | Output |
|-------|------|------|--------|
| 1 | Data prep & banking index | 2-3 hours | `mercado_data_prep.py` |
| 2 | Implement 5 components | 3-4 hours | `mercado_fsi_components.py` |
| 3 | Aggregation & validation | 1-2 hours | `mercado_fsi_aggregate.py` |
| 4 | Compare to HMM | 1-2 hours | `mercado_vs_hmm.py` |
| 5 | Documentation | 1-2 hours | Updated comprehensive doc |

**Total**: 8-13 hours

### Deliverables

1. **`mercado_fsi_sri_lanka.csv`** - Our implementation of Mercado FSI
2. **`mercado_components.csv`** - Individual component values
3. **Validation report** - Correlation with ARIC official
4. **Comparison analysis** - Mercado FSI vs HMM regimes
5. **Visualization** - Timeline plot with both approaches

---

## Part 8: Decision Points Summary

Before implementing, we need to resolve:

### ❓ Decision 1: Banking Sector Index

**Options**:
- A) Construct from top 5 bank stocks (equal weighted)
- B) Use financial sector proxy if available
- C) Skip banking beta (use 4 components)

**Recommendation**: Option A - Construct from major banks

---

### ❓ Decision 2: Yield Curve Data

**Options**:
- A) Use 10Y - 2Y if available
- B) Use 5Y - 1Y T-bill
- C) Use available tbond - tbill from dataset

**Recommendation**: Option C - Use what we have

---

### ❓ Decision 3: EMPI Lookback Period

**Options**:
- A) Full sample mean/std (static)
- B) 60-month rolling window (dynamic)
- C) 36-month rolling window

**Recommendation**: Option B - 60-month rolling for consistency with Mercado

---

### ❓ Decision 4: Aggregation Method

**Options**:
- A) Variance-equal weights (simple average)
- B) PCA (first principal component)
- C) Both (report as robustness)

**Recommendation**: Option C - Both, with variance-equal as primary

---

## Appendix: Additional Resources

### Papers
- Park & Mercado (2014): [SSRN](https://papers.ssrn.com/sol3/papers.cfm?abstract_id=2295802)
- ADB Working Paper Series

### Data
- ARIC FSI Database: https://aric.adb.org/database/fsi
- CBSL Statistical Tables: https://www.cbsl.gov.lk/en/statistics

### Code
- Python `arch` package for GARCH: https://arch.readthedocs.io/
- `scikit-learn` for PCA

---

*Implementation Plan Created: January 2026*
*Ready for execution upon decision point resolution*
