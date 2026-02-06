# Enhancing CBSL's Financial Stress Index with Leading Indicator Properties

**Created**: 2026-01-13 (Tuesday)  
**Last Updated**: 2026-01-13 (v3 - CBSL-Aligned)  
**Status**: DRAFT - AWAITING APPROVAL  
**Scope**: 1 month  
**Audience**: CBSL Macroprudential Surveillance Department + Academic publication

---

## Executive Summary

**Core Thesis**: The Park-Mercado (2014) Financial Stress Index used by CBSL measures stress **levels** but not stress **trajectories**. We propose a velocity-enhanced extension that provides **earlier warning signals** while remaining fully compatible with CBSL's existing framework.

**Three Deliverables**:
1. **Technical paper**: "Enhancing the Park-Mercado FSI with Leading Indicator Properties: Evidence from Sri Lanka 2008-2022"
2. **Policy tool**: Forward-Looking Stress Monitor for CBSL's Macroprudential Surveillance Department
3. **Methodology contribution**: Velocity-enhanced FSI components that integrate with existing FSR reporting

**Key Finding Preview**: Reserve velocity (rate of depletion) signaled stress approximately **60-90 days earlier** than reserve levels during the 2022 crisis.

---

## Part 1: Background & Alignment with CBSL Framework

### CBSL's Current FSI Methodology

Per the [Financial System Stability Review 2022](https://www.cbsl.gov.lk/sites/default/files/cbslweb_documents/publications/fssr/fssr_2022e.pdf) and [FSR 2025](https://www.cbsl.gov.lk/sites/default/files/cbslweb_documents/publications/fssr/fssr_2023e.pdf), CBSL uses the Park-Mercado (2014) framework:

**Reference**: Park, C.Y. & Mercado, R. (2014). "Determinants of Financial Stress in Emerging Market Economies." *Journal of Banking and Finance*, 45, pp. 199-224.

**Source**: [ADB ARIC FSI Database](https://aric.adb.org/database/fsi)

### The 5 Park-Mercado Components

| # | Component | Market | Formula | Stress Interpretation |
|---|-----------|--------|---------|----------------------|
| 1 | **Banking Beta (β)** | Banking | β = Cov(r_bank, r_market) / Var(r_market) | Higher β = more stress |
| 2 | **Equity Returns** | Equity | r_t = ln(P_t) - ln(P_{t-1}) | Negative = more stress |
| 3 | **Equity Volatility** | Equity | GARCH(1,1) conditional variance | Higher σ² = more stress |
| 4 | **Debt Spread** | Sovereign | Spread = Y_10Y - Y_2Y | Wider = more stress |
| 5 | **EMPI** | FX | z(Δe) - z(ΔRES) | Higher = more stress |

**Aggregation**: Standardize (z-score) each component, then simple average or PCA.

### The Gap: Levels vs Trajectories

**Current FSI** answers: *"How stressed is the financial system right now?"*

**Missing capability**: *"How fast is stress building? Are we heading toward crisis?"*

| Dimension | Park-Mercado FSI | Proposed Enhancement |
|-----------|------------------|---------------------|
| Signal timing | Coincident/lagging | Leading |
| Measurement | Stress **level** | Stress **trajectory** |
| Early warning | Detects crisis when happening | Predicts crisis before happening |
| Policy use | Monitor current conditions | Anticipate future conditions |

---

## Part 2: The Velocity Enhancement

### Core Innovation

For each Park-Mercado component, we calculate its **velocity** (rate of change):

| Original Component | Velocity Enhancement | What It Captures |
|-------------------|---------------------|------------------|
| Banking Beta | Δβ/Δt | Is bank systemic risk *increasing*? |
| Equity Returns | Δr/Δt (acceleration) | Is market decline *accelerating*? |
| Equity Volatility | Δσ²/Δt | Is uncertainty *growing*? |
| Debt Spread | ΔSpread/Δt | Is risk premium *widening*? |
| EMPI | ΔEMPI/Δt | Is FX pressure *intensifying*? |

### Additional Velocity Component

We add **Reserve Velocity** as a 6th component based on empirical findings:

| New Component | Formula | Rationale |
|---------------|---------|-----------|
| **Reserve Velocity** | (RES_t - RES_{t-3}) / RES_{t-3} | Strongest leading indicator in 2022 crisis |

### Velocity-Enhanced FSI (V-FSI) Formula

```
V-FSI_t = (1/6) × [z(Δβ/Δt) + z(Δr/Δt) + z(Δσ²/Δt) + z(ΔSpread/Δt) + z(ΔEMPI/Δt) + z(ΔRES/Δt)]
```

Or using PCA:
```
V-FSI_t = PC1 of velocity components
```

---

## Part 3: Empirical Validation

### Research Question

> Does the Velocity-Enhanced FSI (V-FSI) provide earlier warning signals than the standard Park-Mercado FSI?

### Data Requirements

**From CBSL (all available)**:
- ASPI and banking sector returns (for β, returns, volatility)
- Treasury bill/bond yields (for debt spread)
- USD/LKR exchange rate (for EMPI)
- Gross official reserves (for EMPI and reserve velocity)

**Coverage needed**: 2005-2024 monthly (actual data, not interpolated)

**Critical data issue**: Reserve data 2005-2013 is currently interpolated. Need actual CBSL monthly series.

### Stress Episodes to Validate

| Episode | Period | Type | Expected Velocity Lead |
|---------|--------|------|------------------------|
| Global Financial Crisis | 2008-2009 | External shock | 2-3 months |
| BOP Pressure | 2011-2012 | Reserve stress | 2-4 months |
| Political/Easter Bombing | 2018-2019 | Confidence crisis | 1-2 months |
| **Sovereign Default** | 2020-2022 | Full crisis | **3-6 months** |

### Key Hypothesis

For each episode, we expect:
```
Lead time (V-FSI signal) > Lead time (FSI signal)
```

### Preliminary Evidence (2022 Crisis)

From existing analysis:

| Indicator | First Breach | Days Before FX Float (Mar 7, 2022) |
|-----------|--------------|-----------------------------------|
| Reserve **Level** < $3B | October 2021 | 157 days |
| Reserve **Velocity** < -$200M/mo | July 2021 | ~250 days |
| **Velocity advantage** | — | **~90 days earlier** |

---

## Part 4: Comparison Framework

### Head-to-Head Comparison

| Metric | Park-Mercado FSI | Velocity-Enhanced FSI |
|--------|------------------|----------------------|
| Components | 5 | 6 (5 velocities + reserve velocity) |
| Data requirements | Same | Same (just derivatives) |
| Computation | Simple | Slightly more complex |
| Lead time (2022) | ~5 months | ~8 months (hypothesis) |
| False alarm rate | TBD | TBD |
| Interpretability | High | High |

### Evaluation Metrics

1. **Lead time**: Months before crisis that stress signal appears
2. **Hit rate**: % of stress episodes correctly identified
3. **False alarm rate**: % of signals that don't lead to crisis
4. **Signal-to-noise ratio**: Clarity of stress periods vs calm periods

---

## Part 5: Application - Recovery Fragility Monitor

### Forward-Looking Policy Tool

If velocity predicts crisis, it also monitors recovery:

| V-FSI Velocity | Interpretation | Policy Implication |
|----------------|----------------|-------------------|
| Strongly positive | Recovery strengthening | Maintain course |
| Weakly positive | Recovery on track | Monitor closely |
| Near zero | Fragile equilibrium | Prepare contingencies |
| Negative | Relapse risk | Preemptive action needed |

### Dashboard for Macroprudential Surveillance Department

Simple Streamlit application showing:
1. **Current V-FSI** vs historical distribution
2. **Component breakdown** (which velocities are concerning?)
3. **Trajectory chart** (3-month rolling V-FSI)
4. **Alert system** (automatic flags for concerning patterns)

### Integration with FSR

The V-FSI could be reported alongside standard FSI in future Financial Stability Reviews:

> "While the Financial Stress Index (FSI) remained at [X], the Velocity-Enhanced FSI (V-FSI) indicated [accelerating/stable/decelerating] stress dynamics, suggesting [interpretation]."

---

## Part 6: Paper Structure

### Target: CBSL Working Paper Series or Journal of Banking & Finance

**Title**: "Enhancing the Park-Mercado Financial Stress Index with Leading Indicator Properties: Evidence from Sri Lanka"

**Structure** (6,000-8,000 words):

```
1. Introduction (600 words)
   - Sri Lanka 2022 crisis and FSI failure to provide early warning
   - Gap: Park-Mercado measures levels, not trajectories
   - Contribution: Velocity enhancement with earlier signals

2. Literature Review (800 words)
   - Financial stress indices (Park-Mercado, IMF, KC Fed)
   - Early warning systems for emerging markets
   - Momentum/velocity in financial monitoring

3. CBSL's Current Framework (600 words)
   - Park-Mercado methodology as implemented
   - How FSI is reported in FSR
   - Limitations during 2022 crisis

4. Velocity Enhancement Methodology (800 words)
   - Velocity calculation for each component
   - Reserve velocity as additional component
   - Aggregation (variance-equal vs PCA)

5. Data and Context (600 words)
   - CBSL data sources
   - Coverage: 2005-2024
   - Stress episode definitions

6. Empirical Results (1,200 words)
   - Lead time comparison across 4 episodes
   - V-FSI vs FSI performance
   - Optimal velocity windows (1, 3, 6 months)

7. Application: Recovery Fragility Monitor (600 words)
   - Current V-FSI reading
   - Policy implications for 2026
   - Dashboard demonstration

8. Discussion (600 words)
   - Why velocity works (momentum, sustainability)
   - Limitations (data requirements, false alarms)
   - Generalizability to other EMs

9. Conclusion (400 words)
   - Velocity enhancement improves early warning
   - Recommendation for FSR integration
   - Future work: real-time implementation
```

### Figures and Tables

1. **Figure 1**: FSI vs V-FSI timeline (2005-2024) with crisis shading
2. **Figure 2**: Lead time comparison across 4 episodes
3. **Figure 3**: Component breakdown during 2022 crisis
4. **Figure 4**: Current V-FSI and recovery trajectory
5. **Table 1**: Park-Mercado components and velocity enhancements
6. **Table 2**: Lead time and hit rate comparison
7. **Table 3**: Current monitoring readings

---

## Part 7: Timeline (1 Month)

### Week 1: Data & Velocity Calculations
- [ ] Confirm access to actual CBSL monthly reserves (2005-2013)
- [ ] Calculate velocity for each Park-Mercado component
- [ ] Calculate reserve velocity series
- [ ] Generate V-FSI composite

### Week 2: Validation Across Episodes
- [ ] Identify crisis periods (4 episodes)
- [ ] Measure lead times for FSI vs V-FSI
- [ ] Calculate hit rates and false alarm rates
- [ ] Create comparison figures

### Week 3: Paper Draft
- [ ] Write methodology section
- [ ] Write results section
- [ ] Generate all tables and figures
- [ ] Draft introduction and conclusion

### Week 4: Dashboard & Polish
- [ ] Build Streamlit recovery monitor
- [ ] Complete paper draft
- [ ] Create 2-page policy brief for CBSL
- [ ] Internal review

---

## Part 8: Deliverables

| Deliverable | Format | Primary Audience | Length |
|-------------|--------|------------------|--------|
| Technical Paper | PDF | Academics + CBSL research | 6,000-8,000 words |
| Policy Brief | 2-page PDF | CBSL Macroprudential Dept | 800 words |
| Dashboard | Streamlit App | CBSL internal monitoring | - |
| Code Repository | GitHub | Reproducibility | - |

---

## Part 9: Alignment with CBSL Language & Framework

### Terminology Mapping

| Academic Term | CBSL Term (from FSR) | Use In Paper |
|---------------|---------------------|--------------|
| Velocity-Based FSI | Forward-Looking FSI | ✓ |
| Regime detection | Stress identification | ✓ |
| Leading indicator | Early warning signal | ✓ |
| Reserve depletion | Gross official reserves dynamics | ✓ |
| Crisis prediction | Anticipating vulnerabilities | ✓ |

### References to CBSL Publications

Paper should cite:
- CBSL Financial System Stability Review 2022
- CBSL Financial Stability Review 2025
- CBSL Annual Reports (for crisis narrative)
- CBSL Monetary Policy Reports

### Framing for CBSL Acceptance

**DO say**:
- "Enhancement to existing framework"
- "Complementary to current FSI"
- "Additional early warning capability"
- "Supports macroprudential surveillance"

**DON'T say**:
- "CBSL's FSI failed"
- "Replacement for Park-Mercado"
- "Superior methodology"

---

## Part 10: Critical Weaknesses & Mitigations

### Weakness 1: Data Quality (CRITICAL)

**Issue**: Reserve data 2005-2013 is interpolated from World Bank annual.

**Severity**: High  
**Mitigation**: Request actual monthly data from CBSL, or focus on 2014-2024  
**Residual risk**: May miss GFC episode validation

---

### Weakness 2: In-Sample Optimization

**Issue**: Finding optimal velocity windows on same data creates overfitting.

**Severity**: Medium  
**Mitigation**: 
- Test multiple windows (1, 3, 6 months) and report sensitivity
- Use rolling origin cross-validation
- Reserve most recent episode (2022) for out-of-sample test

---

### Weakness 3: Single Country

**Issue**: Results may be Sri Lanka-specific.

**Severity**: Medium  
**Mitigation**:
- Frame as "case study with generalizable methodology"
- Note that velocity logic should apply to any FSI framework
- Suggest future work on other ARIC countries

---

### Weakness 4: Velocity vs Acceleration

**Issue**: Why first derivative? Why not second derivative (acceleration)?

**Severity**: Low  
**Mitigation**:
- Test acceleration as robustness check
- Economic intuition: velocity captures "direction of travel"
- Acceleration may be too noisy for monthly data

---

### Weakness 5: False Alarm Rate Unknown

**Issue**: Velocity might signal stress that doesn't materialize.

**Severity**: Medium  
**Mitigation**:
- Explicitly calculate false alarm rate
- Compare to false alarm rate of level-based FSI
- Acknowledge trade-off: earlier signal vs more false alarms

---

### Weakness 6: CBSL May Already Do This Internally

**Issue**: CBSL might already track velocities unofficially.

**Severity**: Low  
**Mitigation**:
- Position as "formalizing and validating" rather than "inventing"
- Engage with Macroprudential Surveillance Department for feedback
- Offer to collaborate rather than publish externally first

---

## Part 11: Open Questions

### Q1: Data Access
**Can you confirm access to actual monthly CBSL reserve data for 2005-2013?**
- If yes → Full 4-episode validation
- If no → Focus on 2014-2024 (2 episodes)

### Q2: CBSL Engagement
**Would you like to share preliminary findings with CBSL before publication?**
- Option A: Publish first, share later
- Option B: Share informally, get feedback, then publish
- Option C: Formal collaboration with CBSL as co-author

### Q3: Paper Venue
**Primary target?**
- Option A: CBSL Working Paper Series (fastest, most aligned)
- Option B: ADB Economics Working Paper (regional reach)
- Option C: Journal of Banking & Finance (highest prestige, longest)

### Q4: Dashboard Scope
**How elaborate should the monitoring tool be?**
- Option A: Simple static charts (minimal effort)
- Option B: Interactive Streamlit dashboard (medium effort)
- Option C: Real-time updating system (high effort)

---

## Suggested Answers

- **Q1**: Proceed with available data; request full series if possible
- **Q2**: Option B (get CBSL feedback before formal publication)
- **Q3**: Option A first (CBSL WP), then Option C (journal revision)
- **Q4**: Option B (interactive dashboard, reasonable scope)

---

## Next Steps

1. **Confirm data availability** for actual monthly reserves 2005-2013
2. **Decide on CBSL engagement approach**
3. **Approve this plan** to begin Week 1 work
4. **Identify contact** at CBSL Macroprudential Surveillance Department

---

*Document created: 2026-01-13*  
*Last updated: 2026-01-13 (v3 - CBSL-Aligned)*  
*Status: DRAFT - AWAITING APPROVAL*
