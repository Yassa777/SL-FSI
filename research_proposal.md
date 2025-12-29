# Research Proposal: Sri Lanka Financial Stress Regime Analysis

## 1. Research Topic
Detecting and interpreting financial stress regimes in Sri Lanka using multi-source market and macroeconomic data with probabilistic regime-switching and structural break detection techniques.

## 2. Background of the Research
Sri Lanka experienced sharp macro-financial stress during 2021–2023, marked by exchange-rate dislocations, depletion of reserves, inflation surges, and sovereign credit distress. This repository provides a consolidated dataset of 18 core market and macro streams (37 columns total, 2010–2025 coverage) along with derived financial-stress indicators. The dataset includes FX rates, policy and market rates, equity indices, reserves, inflation, external sector flows (tourism, remittances), and global anchors (gold, US 10Y yields). The project already implements a Streamlit dashboard for exploratory analysis and applies Hidden Markov Models (HMM) and Bayesian online change point detection to identify stress regimes and structural breaks. This proposal formalizes a research plan that leverages these data and methods to produce an empirically grounded, policy-relevant financial stress regime framework for Sri Lanka.

## 3. Research Aim
To construct a robust, interpretable regime-classification framework for Sri Lanka’s financial stress using multi-frequency macro-financial data and probabilistic change-detection techniques, enabling early warning and policy diagnostics.

## 4. Research Approach / Objectives
1. **Data harmonization and validation**
   - Use merged daily and monthly panels (`data/merged/slfsi_daily_panel.csv`, `data/merged/slfsi_monthly_panel.csv`).
   - Validate completeness and gaps across key series (FX, rates, equities, reserves, inflation, external flows).
2. **Feature engineering and stress indicators**
   - Employ derived indicators already defined in the dataset (e.g., FX/equity returns, volatility, spreads, real rates, reserve metrics).
   - Assess feature coverage and robustness, prioritizing indicators with higher continuity.
3. **Regime identification**
   - Apply Gaussian HMMs (2–5 regimes) on selected feature subsets to classify latent stress regimes.
   - Evaluate regime stability and transition probabilities against known crisis events.
4. **Structural break detection**
   - Apply Bayesian online change point detection to detect mean/variance shifts in key indicators.
   - Cross-validate change points with HMM regime shifts and macro events.
5. **Interpretation and policy mapping**
   - Map regimes to observable policy periods (pre-crisis, crisis escalation, stabilization).
   - Provide a narrative linking regime states to policy and external sector dynamics.

## 5. Research Questions
1. Which combination of Sri Lankan macro-financial indicators best discriminates between low-, medium-, and high-stress regimes?
2. Do HMM-inferred regimes align with documented crisis events (FX float, sovereign default, inflation peak, IMF agreement)?
3. How do Bayesian change points in key indicators correlate with regime transitions?
4. Which indicators provide the strongest early-warning signals of regime shifts?
5. How robust are regime classifications to data gaps and mixed-frequency data integration?

## 6. Research Outcomes
- **A validated regime classification** for Sri Lanka’s financial stress, with probabilistic regime labels over 2010–2025.
- **A ranked set of stress indicators** highlighting the most predictive features for regime transitions.
- **Event-aligned diagnostics** showing the timing of structural breaks and regime shifts around major macro events.
- **A reproducible analytics pipeline** (data merge + HMM + change point detection) suitable for extension to other EM contexts.
- **Interactive visualization outputs** in the Streamlit dashboard to support policy analysis.

## 7. Plans for Sustainability
- Maintain a modular data ingestion pipeline for periodic updates (external downloads + manual templates).
- Use transparent feature engineering and documented formulas to ensure reproducibility.
- Provide a lightweight Streamlit interface for dissemination and internal use by analysts.
- Encourage periodic model recalibration as new data (e.g., AWCMR updates, improved bond yield coverage) becomes available.

## 8. Plans for Commercialisation
- Package the regime analytics as a subscription-based monitoring tool for financial institutions and risk advisory firms.
- Offer customized dashboards for investors and policymakers, with alerting on regime shifts and stress thresholds.
- Provide consulting services around stress testing, early-warning indicators, and policy impact evaluation using the model outputs.
- Explore partnerships with regional data providers or central banks to integrate additional proprietary indicators and expand coverage.
