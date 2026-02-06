# Research Proposal

## Regime-Switching Balance of Payments Forecasting for Small Open Economies: Evidence from Sri Lanka

---

### 1. Introduction & Motivation

Balance of payments (BoP) forecasting is a critical input for macroeconomic policy in emerging and frontier markets. Central banks and finance ministries rely on BoP projections to assess external financing needs, calibrate reserve adequacy targets, and design policy responses to external shocks. Yet conventional BoP forecasting approaches—typically based on fixed elasticity models linking trade flows to income and relative prices—perform poorly during periods of economic stress precisely when accurate forecasts matter most.

Sri Lanka's recent experience illustrates this challenge starkly. The 2020-2022 period saw:
- Recorded remittances collapse from $7.1bn (2020) to $3.8bn (2021) as flows shifted to informal channels
- Tourism receipts fall from $3.6bn (2019) to $0.3bn (2020) and struggle to recover
- Import compression far exceeding what standard income elasticities would predict
- A sovereign default despite models suggesting manageable financing gaps

These patterns suggest that the behavioral relationships underlying BoP flows are **regime-dependent**—stable during normal periods but subject to structural breaks during crises. Standard forecasting models that assume parameter stability will systematically underestimate tail risks and provide false comfort to policymakers.

This paper develops a **regime-switching framework for BoP forecasting** that explicitly accounts for structural instability in external sector dynamics. We contribute to the literature by:

1. Documenting regime-dependence in key BoP elasticities using Sri Lankan data
2. Developing a probabilistic forecasting framework that incorporates regime uncertainty
3. Integrating macro-financial stress indicators as regime predictors
4. Demonstrating improved forecast accuracy relative to conventional approaches

---

### 2. Literature Review

#### 2.1 Balance of Payments Forecasting

The standard approach to BoP forecasting follows the IMF's Financial Programming framework, modeling trade flows as functions of income and relative prices:

$$M_t = f(Y_t, \frac{E_t \cdot P^*_t}{P_t})$$
$$X_t = g(Y^*_t, \frac{P_t}{E_t \cdot P^*_t})$$

Elasticities are typically estimated from historical data and assumed stable for forecasting purposes (Goldstein & Khan, 1985; Senhadji, 1998). The IMF's World Economic Outlook projections and Article IV assessments rely heavily on this approach.

Recent work has sought to improve forecast accuracy through:
- Disaggregation by commodity/partner (Bayoumi, 1999)
- Incorporating global value chains (Bussière et al., 2013)
- Machine learning approaches (Soybilgen & Yazgan, 2021)

However, this literature largely maintains the assumption of parameter stability.

#### 2.2 Regime-Switching in Macroeconomic Relationships

A parallel literature documents that macroeconomic relationships are often regime-dependent:
- Hamilton (1989) introduced Markov-switching models for business cycles
- Forbes & Warnock (2012) identify distinct regimes in capital flow dynamics ("surges," "stops," "flight," "retrenchment")
- Goldberg & Krogstrup (2023) show that exchange rate pass-through varies with monetary policy regimes

Applications to trade elasticities remain limited. Bahmani-Oskooee & Hegerty (2007) find evidence of structural breaks in import demand functions but do not develop a forecasting framework.

#### 2.3 Early Warning Systems and Financial Stress Indices

The early warning literature (Kaminsky, Lizondo & Reinhart, 1998; Berg & Pattillo, 1999) identifies leading indicators of balance of payments crises but typically treats crisis as a binary outcome rather than integrating crisis probability into flow projections.

Financial stress indices (FSIs) have been developed for emerging markets (Balakrishnan et al., 2011; Cevik et al., 2013) and shown to predict output contractions and credit crunches. Their potential as regime indicators for BoP forecasting has not been explored.

#### 2.4 Contribution

This paper bridges these literatures by:
- Embedding regime-switching dynamics directly into a BoP forecasting framework
- Using FSI-based regime indicators rather than ex-post crisis dating
- Providing a probabilistic forecast that accounts for both parameter uncertainty and regime uncertainty
- Demonstrating the approach with a comprehensive application to Sri Lanka

---

### 3. Methodology

#### 3.1 Conceptual Framework

We decompose the current account into major components and model each as a regime-switching process:

$$CA_t = TB_t + SB_t + PI_t + SI_t$$

Where:
- $TB_t$ = Trade balance (goods)
- $SB_t$ = Services balance  
- $PI_t$ = Primary income (interest, dividends)
- $SI_t$ = Secondary income (remittances, transfers)

For each flow component $i$, we specify:

$$y_{i,t} = \mu_{i,S_t} + \mathbf{X}'_{i,t}\boldsymbol{\beta}_{i,S_t} + \sigma_{i,S_t}\varepsilon_{i,t}$$

Where $S_t \in \{0, 1\}$ denotes the regime (normal vs. stress) and parameters $(\mu, \boldsymbol{\beta}, \sigma)$ are regime-specific.

#### 3.2 Regime Identification

We consider three approaches to regime identification:

**Approach A: Markov-Switching (Endogenous)**

Regime transitions follow a Markov process with transition probabilities:
$$P(S_t = j | S_{t-1} = i) = p_{ij}$$

Estimated jointly with the flow equations via maximum likelihood or Bayesian MCMC.

**Approach B: Threshold Model (FSI-Based)**

Regime determined by an observable stress indicator:
$$S_t = \mathbb{1}[FSI_t > \tau]$$

Where $FSI_t$ is a financial stress index and $\tau$ is an estimated or calibrated threshold.

**Approach C: Time-Varying Probability (Bayesian)**

Regime probability evolves based on stress indicators:
$$P(S_t = 1 | \mathbf{Z}_t) = \Phi(\boldsymbol{\gamma}'\mathbf{Z}_t)$$

Where $\mathbf{Z}_t$ includes FSI components, global risk indicators (VIX, EMBI), and domestic leading indicators.

#### 3.3 Component-Specific Models

**Merchandise Exports**

Regime-switching export supply function:
$$\ln X_t = \alpha_{S_t} + \beta^Y_{S_t} \ln Y^*_t + \beta^P_{S_t} \ln REER_t + \beta^{CAP}_{S_t} \ln K_t + \varepsilon_t$$

Hypothesis: During stress regimes, foreign demand elasticity declines (importers diversify away from stressed suppliers) and supply constraints bind (input availability, credit access).

**Merchandise Imports**

Regime-switching import demand:
$$\ln M_t = \alpha_{S_t} + \beta^Y_{S_t} \ln Y_t + \beta^P_{S_t} \ln (E_t P^M_t / P_t) + \varepsilon_t$$

Hypothesis: Income elasticity increases during stress (imports compressed beyond what income decline implies due to credit constraints, import restrictions). Price elasticity may also shift.

Disaggregation:
- Fuel: Largely inelastic, price-driven
- Intermediate inputs: Linked to export production
- Consumer goods: Most elastic, most compressed during stress
- Capital goods: Linked to investment, FDI

**Tourism**

Arrivals model with regime-switching:
$$\ln A_t = \alpha_{S_t} + \beta^Y_{S_t} \ln Y^{source}_t + \beta^P_{S_t} \ln RER_t + \beta^{COMP}_{S_t} \ln A^{comp}_t + \gamma' \mathbf{D}_t + \varepsilon_t$$

Where $\mathbf{D}_t$ captures episodic shocks (Easter attacks, COVID, civil unrest).

Hypothesis: Recovery dynamics differ by regime—stress regimes show slower mean reversion due to reputational persistence.

**Remittances**

Regime-switching remittance function:
$$\ln R_t = \alpha_{S_t} + \beta^{OIL}_{S_t} \ln P^{oil}_t + \beta^{ER}_{S_t} \ln E_t + \beta^{PREM}_{S_t} \ln(1 + \pi_t) + \varepsilon_t$$

Where $\pi_t$ is the parallel market premium.

Hypothesis: During stress, exchange rate channel dominates—depreciation expectations and parallel premia induce channel-switching (formal → informal), causing recorded remittances to collapse disproportionately.

**Primary Income**

Interest payments modeled as:
$$INT_t = \sum_i r_{i,t} \cdot D_{i,t-1}$$

Not regime-switching per se, but debt dynamics and restructuring enter via stock evolution.

#### 3.4 Forecasting Procedure

**Step 1: Estimate regime-specific parameters**
Using historical data, estimate $(\mu_{i,s}, \boldsymbol{\beta}_{i,s}, \sigma_{i,s})$ for each component $i$ and regime $s$.

**Step 2: Project regime probabilities**
Given current FSI and stress indicators, compute:
$$\hat{P}(S_{t+h} = 1 | \mathcal{I}_t)$$

For each forecast horizon $h$.

**Step 3: Generate conditional forecasts**
For each regime, project component flows:
$$\hat{y}_{i,t+h|S=s} = \hat{\mu}_{i,s} + \hat{\mathbf{X}}'_{i,t+h}\hat{\boldsymbol{\beta}}_{i,s}$$

Where $\hat{\mathbf{X}}_{t+h}$ contains projected covariates (WEO forecasts, oil futures, etc.)

**Step 4: Combine via regime probabilities**
$$\hat{y}_{i,t+h} = \sum_s \hat{P}(S_{t+h} = s) \cdot \hat{y}_{i,t+h|S=s}$$

**Step 5: Aggregate to current account**
Sum components to get CA forecast and compute financing gap:
$$\widehat{GAP}_{t+h} = -\widehat{CA}_{t+h} - \widehat{FA}^{known}_{t+h}$$

**Step 6: Construct prediction intervals**
Using simulation or analytical methods, generate prediction intervals that account for:
- Parameter uncertainty
- Regime uncertainty
- Shock uncertainty

#### 3.5 Evaluation

**Point forecast accuracy:**
- RMSE, MAE relative to naive and random walk benchmarks
- Diebold-Mariano tests for forecast comparison

**Density forecast evaluation:**
- Probability integral transform (PIT) tests
- Continuous ranked probability score (CRPS)

**Regime forecast evaluation:**
- ROC curves for stress regime prediction
- Brier scores

**Comparison models:**
1. Constant-parameter baseline (standard IMF approach)
2. Time-varying parameter (TVP) without discrete regimes
3. Simple threshold model
4. Full regime-switching specification

---

### 4. Data

#### 4.1 Sample Period
1990Q1 – 2024Q4 (subject to availability)

Extended sample captures multiple stress episodes:
- 1998-2001: Civil war intensification
- 2004-2005: Tsunami shock
- 2008-2009: Global financial crisis
- 2018-2019: Political instability, Easter attacks
- 2020-2022: COVID, sovereign debt crisis

#### 4.2 Balance of Payments Data
Source: Central Bank of Sri Lanka

| Component | Frequency | Coverage |
|-----------|-----------|----------|
| Trade (goods) | Monthly | 1990– |
| Services | Quarterly | 1995– |
| Remittances | Monthly | 2000– |
| Tourism arrivals | Monthly | 1990– |
| Primary income | Quarterly | 1995– |
| Financial account | Quarterly | 1995– |
| Reserves | Monthly | 1990– |

#### 4.3 Covariates

**Domestic:**
- Real GDP (quarterly, interpolated)
- CPI, WPI
- Exchange rates (official, parallel where available)
- Interest rates
- Credit growth
- CBSL policy variables

**External:**
- Trading partner GDP (US, EU, India, China, Middle East)
- Oil prices (Brent)
- Food price indices (FAO)
- Global tea prices
- VIX, EMBI Global spreads
- US Treasury yields

#### 4.4 Financial Stress Index

We construct an FSI for Sri Lanka following Balakrishnan et al. (2011), incorporating:
- Banking sector stress (NPLs, credit growth, bank equity)
- Exchange market pressure
- Sovereign spreads
- Equity market volatility
- External financing conditions

Alternatively, we use the FSI developed in [prior/companion work] on macro-financial regime detection.

---

### 5. Expected Results

#### 5.1 Regime Identification
We expect to identify distinct "normal" and "stress" regimes with:
- Clear separation in FSI distributions
- Regime persistence (low transition probabilities)
- Clustering around known crisis periods

#### 5.2 Parameter Shifts
Hypothesized regime differences:

| Parameter | Normal Regime | Stress Regime |
|-----------|---------------|---------------|
| Import income elasticity | ~1.5 | ~2.5+ (sharper compression) |
| Export demand elasticity | ~1.0 | ~0.5 (importers diversify) |
| Tourism recovery speed | Fast | Slow (reputational drag) |
| Remittance ER sensitivity | Moderate | High (channel-switching) |
| Forecast uncertainty | Lower | Higher |

#### 5.3 Forecast Performance
We expect the regime-switching model to:
- Outperform constant-parameter models, especially during stress periods
- Provide better-calibrated prediction intervals
- Offer earlier warning of financing gaps widening

#### 5.4 Policy Implications
- Reserve adequacy assessment should account for regime-dependent dynamics
- Early warning indicators can be integrated into forecasting (not just crisis prediction)
- Parameter estimates from normal periods understate vulnerability

---

### 6. Policy Relevance

This research directly addresses practical challenges faced by:

**Central Bank of Sri Lanka:**
- BoP forecasting for monetary policy and reserve management
- Stress testing external sector
- IMF program monitoring (projections vs. actuals)

**Ministry of Finance:**
- External financing strategy
- Debt sustainability analysis
- Fiscal implications of external shocks

**IMF and development partners:**
- Program design and conditionality
- Debt restructuring negotiations
- Technical assistance in BoP forecasting

The framework can be adapted to other small open economies with similar structural features (commodity dependence, remittance reliance, tourism exposure, external debt burden).

---

### 7. Research Plan & Timeline

| Phase | Activities | Timeline |
|-------|------------|----------|
| 1. Data compilation | Collect BoP components, construct FSI, compile covariates | Months 1-2 |
| 2. Preliminary analysis | Descriptive statistics, structural break tests, regime dating | Months 2-3 |
| 3. Model estimation | Estimate regime-switching models for each component | Months 3-5 |
| 4. Forecasting evaluation | Out-of-sample forecast comparison, density evaluation | Months 5-6 |
| 5. Policy applications | Scenario analysis, stress testing, reserve adequacy | Months 6-7 |
| 6. Writing & revision | Draft paper, internal review, revision | Months 7-9 |
| 7. Dissemination | CBSL presentation, conference submission, journal submission | Months 9-12 |

---

### 8. Potential Extensions

1. **Nowcasting module**: High-frequency indicators (trade data, tourism arrivals, remittances) for real-time regime detection and short-term forecasting

2. **Regional application**: Extend to South Asian panel (India, Bangladesh, Pakistan, Nepal) to improve regime identification through cross-country information

3. **Capital flow integration**: Model financial account flows with regime-switching (FDI persistence, portfolio flow reversals, debt rollover risk)

4. **General equilibrium feedback**: Integrate with exchange rate and reserve dynamics for fully endogenous projections

5. **Machine learning augmentation**: Use ML for regime classification, combine with structural model for interpretability

---

### 9. References

Bahmani-Oskooee, M., & Hegerty, S. W. (2007). Exchange rate volatility and trade flows: A review article. *Journal of Economic Studies*, 34(3), 211-255.

Balakrishnan, R., Danninger, S., Elekdag, S., & Tytell, I. (2011). The transmission of financial stress from advanced to emerging economies. *Emerging Markets Finance and Trade*, 47(sup2), 40-68.

Berg, A., & Pattillo, C. (1999). Predicting currency crises: The indicators approach and an alternative. *Journal of International Money and Finance*, 18(4), 561-586.

Bussière, M., Callegari, G., Ghironi, F., Sestieri, G., & Yamano, N. (2013). Estimating trade elasticities: Demand composition and the trade collapse of 2008-2009. *American Economic Journal: Macroeconomics*, 5(3), 118-51.

Forbes, K. J., & Warnock, F. E. (2012). Capital flow waves: Surges, stops, flight, and retrenchment. *Journal of International Economics*, 88(2), 235-251.

Goldberg, L. S., & Krogstrup, S. (2023). International capital flow pressures and global factors. *Journal of International Economics*, 146, 103749.

Goldstein, M., & Khan, M. S. (1985). Income and price effects in foreign trade. *Handbook of International Economics*, 2, 1041-1105.

Hamilton, J. D. (1989). A new approach to the economic analysis of nonstationary time series and the business cycle. *Econometrica*, 57(2), 357-384.

Kaminsky, G., Lizondo, S., & Reinhart, C. M. (1998). Leading indicators of currency crises. *IMF Staff Papers*, 45(1), 1-48.

Senhadji, A. (1998). Time-series estimation of structural import demand equations: A cross-country analysis. *IMF Staff Papers*, 45(2), 236-268.

---

### 10. Author Information

[To be completed]

**Affiliation:** Data Analytics & Visualization Lab, University of Colombo

**Collaborating Institution:** Central Bank of Sri Lanka

---

*Draft: January 2025*
