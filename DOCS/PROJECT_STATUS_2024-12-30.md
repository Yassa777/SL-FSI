# SL-FSI Project Status Snapshot

**Date**: December 30, 2024
**Assessment By**: Claude Opus 4.5
**Purpose**: Honest assessment of project state against plan.md objectives

---

## Executive Summary

| Metric | Value |
|--------|-------|
| **Overall Completion** | ~30% |
| **Data Pipeline** | Functional but gaps |
| **HMM Implementation** | Basic, not validated |
| **Validation Framework** | Not started |
| **Dashboard** | Working |
| **Research Readiness** | Low |

---

## Progress by Objective

### Objective 1: Data Harmonization & Feature Engineering
**Status**: ⚠️ Partial (~60%)

**Completed**:
- [x] Data pipeline (`merge_all_data.py`, `download_external_data.py`)
- [x] 18 core data streams defined
- [x] Merged daily panel (2,922 rows, 37 columns)
- [x] Merged monthly panel (96 rows, 34 columns)
- [x] 12 derived features calculated
- [x] Coverage documentation

**Not Completed**:
- [ ] Resolution of AWCMR data gap (ends 2020, missing for entire crisis)
- [ ] ISB yield daily coverage
- [ ] T-Bill/T-Bond density improvement
- [ ] Formal missingness pattern documentation

---

### Objective 2: Regime Identification
**Status**: ⚠️ Partial (~40%)

**Completed**:
- [x] Gaussian HMM implementation (hmmlearn)
- [x] Configurable 2-5 regimes
- [x] Transition matrix display
- [x] Basic regime statistics
- [x] Feature overlap validation (just added)

**Not Completed**:
- [ ] Systematic regime characterization
- [ ] Formal specification selection (2 vs 3 vs 4 states)
- [ ] Regime signature documentation
- [ ] Convergence diagnostics

---

### Objective 3: Event-Alignment Validation
**Status**: ❌ Not Started (0%)

**Required Components (from plan)**:
- [ ] Pre-specified event list implementation
- [ ] Tactical window evaluation (±14 days)
- [ ] Strategic window evaluation (±60 days)
- [ ] Sustained crossing detection (prob ≥ τ for K days)
- [ ] Cost-weighted scoring (λ > 1 for missed signals)
- [ ] Z-score baseline benchmark
- [ ] Hit rate calculation
- [ ] False alarm tracking

**Events to Validate Against**:
```
Regime Shift Anchors:
- 2022-01-18: $500M ISB repayment
- 2022-03-07: CBSL abandons defended exchange rate
- 2022-04-12: External debt payment suspension
- 2022-09-01: IMF staff-level agreement
- 2023-03-20: IMF Board approves EFF
- 2023-06-28: Domestic debt restructuring plan
- 2024-06-26: Official Creditor Committee agreement
- 2024-09-19: Agreement with international bondholders
- 2024-11: Single policy rate framework
- 2025-03-07: Debt restructuring deal with Japan

Major Stress Shocks:
- 2019-04-21: Easter Sunday attacks
- 2020-03-20: COVID lockdown begins
- 2021-04-22: Fertilizer import ban
- 2022-07-14: President resigns
```

---

### Objective 4: Minimal Indicator Set Identification
**Status**: ❌ Not Started (0%)

**Required**:
- [ ] Feature ablation experiments
- [ ] Stability analysis across feature subsets
- [ ] Minimum viable feature set determination
- [ ] Coverage vs signal trade-off analysis

---

### Objective 5: Robustness & Sensitivity Analysis
**Status**: ❌ Not Started (0%)

**Required**:
- [ ] Systematic 2/3/4 regime comparison
- [ ] Alternate feature subset testing
- [ ] Scaling sensitivity analysis
- [ ] Sample window stability testing
- [ ] Probability reporting with uncertainty

---

## Data Quality Assessment

### Coverage Analysis (Crisis Period 2020-2024)

```
CRITICAL ISSUES:
────────────────────────────────────────────────────────
✗ awcmr (interbank rate)    :    9.6%  ← DATA ENDS 2020
✗ interbank_spread          :    9.6%  ← DEPENDENT ON AWCMR
✗ embi_spread_approx        :   10.6%  ← ISB MONTHLY ONLY
✗ tbill_primary             :   13.8%  ← SPARSE AUCTIONS
✗ tbond_yield               :    4.8%  ← SPARSE AUCTIONS
✗ yield_curve_slope         :    4.0%  ← DERIVED FROM SPARSE

POOR COVERAGE (30-50%):
────────────────────────────────────────────────────────
⚠ gold_premium_pct          :   29.1%
⚠ r_fx                      :   38.8%
⚠ r_eq_real                 :   36.9%
⚠ r_eq                      :   46.6%

MARGINAL COVERAGE (50-70%):
────────────────────────────────────────────────────────
⚠ usd_lkr                   :   51.3%
⚠ vol_fx_20d                :   51.5%
⚠ vol_eq_20d                :   57.6%
⚠ aspi                      :   62.3%
⚠ equity_turnover           :   62.3%
⚠ market_cap                :   62.3%
⚠ sl20_index                :   62.3%
⚠ turnover_ratio            :   62.3%
⚠ gold_usd                  :   68.9%
⚠ us_10y_yield              :   68.9%

GOOD COVERAGE (>70%):
────────────────────────────────────────────────────────
✓ sdfr                      :   93.5%
✓ slfr                      :   93.5%
✓ policy_ceiling            :  100.0%
✓ reer_index                :  100.0%  (monthly forward-filled)
✓ gross_reserves_usd_m      :  100.0%  (monthly forward-filled)
✓ ncpi_yoy_pct              :  100.0%  (monthly forward-filled)
✓ tourism_earnings_usd_m    :  100.0%  (monthly forward-filled)
✓ remittances_usd_m         :  100.0%  (monthly forward-filled)
✓ real_policy_rate          :  100.0%
✓ reserve_slope_3m          :  100.0%
✓ import_cover_months       :  100.0%
```

### Critical Gap: AWCMR

The Average Weighted Call Money Rate (interbank rate) is a **key financial stress indicator** that shows bank-to-bank lending stress. Per DATA_INVENTORY.md:

> "AWCMR ends 2020 - Need updated interbank rates from CBSL"

**Impact**: Cannot calculate `interbank_spread` for the entire crisis period (2021-2024).

---

## Infrastructure Status

### Files Structure
```
SL-FSI/
├── data/
│   ├── external/           # Raw external data (6 sources)
│   ├── processed/          # CBSL processed data (10 files)
│   └── merged/             # Final panels
│       ├── slfsi_daily_panel.csv    (2,922 rows, 37 cols)
│       └── slfsi_monthly_panel.csv  (96 rows, 34 cols)
├── scripts/
│   ├── merge_all_data.py           # Data pipeline
│   └── download_external_data.py   # External data fetcher
├── app_regime_analysis.py          # Streamlit dashboard
├── plan.md                         # Research proposal
├── requirements_regime.txt         # Dependencies
└── *.md                            # Documentation
```

### Dependencies
```
streamlit>=1.28.0
pandas>=2.0.0
numpy>=1.24.0
plotly>=5.17.0
hmmlearn>=0.3.0
scipy>=1.11.0
ruptures>=1.1.0  # Added 2024-12-30
```

### Dashboard Features
- [x] Data Explorer (18 indicators + 12 derived)
- [x] Correlation Matrix
- [x] HMM Regime Detection (with overlap validation)
- [x] Change Point Detection (PELT algorithm)
- [x] Combined View
- [x] Crisis event markers

---

## Recent Fixes (December 30, 2024)

### 1. Schema Consistency
Fixed mismatch between `DATA_STREAMS` dictionary and actual column names:
```python
# Examples of fixes:
'turnover_lkr_mn' → 'equity_turnover'
'market_cap_lkr_bn' → 'market_cap'
'inflation_yoy' → 'ncpi_yoy_pct'
# ... 12 total mappings corrected
```

### 2. Changepoint Detection
Replaced broken pseudo-BOCPD with proper `ruptures` library:
- PELT algorithm (optimal for multiple changepoints)
- Binary Segmentation option
- Window-based option
- Multiple cost models (L2, RBF, Linear, Rank)
- Honest labeling as "offline" detection

### 3. HMM Feature Overlap
Added comprehensive overlap validation:
- Per-feature coverage display
- Total overlap percentage
- Traffic light warnings (red < 30%, yellow < 60%, green > 60%)
- Minimum 100-observation requirement
- Date range display

---

## Plan.md Assessment

### Strengths
1. Excellent motivation (Jan 18 → Apr 12 story)
2. Sound methodological framing
3. Well-designed validation framework (dual windows, cost-weighted)
4. Clear research questions
5. Realistic scope (deferred MS-VAR)

### Weaknesses
1. **Overconfident about data quality** - Plan claims data is ready, but AWCMR ends 2020
2. **No missing data strategy** - What to do with 10% coverage features?
3. **Aggressive timeline** - 8 weeks for data fixes + validation + robustness + paper
4. **Missing statistical rigor** - No CIs, bootstrap, or significance testing
5. **Vague parameters** - What exactly is λ, τ, K?
6. **No baseline specification** - Z-score on which features?

### Recommended Additions
1. Data quality contingency section
2. Specified validation parameters
3. Minimum viable feature set definition
4. Statistical validation methods
5. Timeline contingencies

---

## Realistic Assessment

### What's Actually Working
- Data pipeline runs end-to-end
- Dashboard displays correctly
- Basic HMM fits and shows regimes
- Change points detected (with proper algorithm)
- Crisis markers display

### What's NOT Working
- Can't use interbank stress (no data)
- Can't compute EMBI spread reliably
- HMM on "recommended" features has <50% overlap
- No validation of whether regimes match reality
- No evidence regimes are statistically meaningful

### What's Missing for Research
1. **Validation framework** - The core methodological contribution is unbuilt
2. **Statistical tests** - No way to say if results are significant
3. **Robustness evidence** - No sensitivity analysis
4. **Baseline comparison** - Can't claim HMM beats simple alternatives

---

## Recommended Next Steps

### Immediate (Before Proceeding)
1. **Resolve AWCMR gap** - Either get data or document as limitation
2. **Define minimum viable features** - What works with good coverage?
3. **Specify validation parameters** - τ, K, λ values

### Short-term (Week 1-2)
1. Build event-alignment validation framework
2. Implement z-score baseline
3. Run systematic 2/3/4 regime comparison

### Medium-term (Week 3-4)
1. Feature ablation experiments
2. Robustness testing
3. Bootstrap confidence intervals

### Documentation Needed
1. Updated plan.md with contingencies
2. Data quality report with limitations
3. Methodology specification with exact parameters

---

## Questions to Resolve

1. **Can we get updated AWCMR data?** If not, what's the proxy?
2. **What's the minimum feature set?** Which 3-4 features with >80% coverage?
3. **What are the validation thresholds?** τ=?, K=?, λ=?
4. **What's the baseline exactly?** Z-score of [which features]?
5. **Is 8 weeks realistic?** Given current state, probably not for full scope.

---

## Conclusion

The project has a solid foundation (data pipeline, dashboard, basic HMM) but is far from research-ready. The critical missing piece is the **validation framework** (Objective 3), which is where the actual research contribution lies.

Data quality issues (especially AWCMR ending in 2020) need honest acknowledgment and either resolution or documented workarounds.

The plan is well-conceived but optimistic. A realistic path forward requires:
1. Accepting data limitations
2. Building the validation framework
3. Demonstrating HMM value vs baseline
4. Potentially reducing scope to achievable timeline

---

*This snapshot reflects project state as of December 30, 2024.*
