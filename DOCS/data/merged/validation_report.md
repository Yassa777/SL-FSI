# SL-FSI Validation Report

Generated: 2026-01-09T07:29:42Z

## Framework Validation

### HMM Configuration

- features: awcmr, real_policy_rate, gross_reserves_usd_m, ncpi_yoy_pct
- n_states: 3
- covariance_type: diag
- n_iter: 300
- random_state: 42

### Metrics Summary

| Window | Model | Hit Rate | Misses | Hits | Cost Score |
| --- | --- | --- | --- | --- | --- |
| tactical | HMM | 91.7% | 1 | 11 | 2.0 |
| tactical | Z-Score | 83.3% | 2 | 10 | 4.0 |
| strategic | HMM | 100.0% | 0 | 12 | 0.0 |
| strategic | Z-Score | 91.7% | 1 | 11 | 2.0 |

### False Alarm Summary

- total_transitions: 5.0
- justified: 4.0
- false_alarms: 1.0
- false_alarm_rate: 0.2

### Strategic Event Alignment (HMM)

| Date | Event | Expected | Detected | Hit |
| --- | --- | --- | --- | --- |
| 2022-01-18 | $500M ISB Repayment | STRESS | STRESS | True |
| 2022-03-07 | FX Float (CBSL abandons peg) | STRESS | STRESS | True |
| 2022-04-12 | External Debt Suspension (Default) | CRISIS | CRISIS | True |
| 2022-09-01 | IMF Staff-Level Agreement | CRISIS | CRISIS | True |
| 2023-03-20 | IMF EFF Approval | CRISIS | CRISIS | True |
| 2023-06-28 | Domestic Debt Restructuring Plan | STRESS | STRESS | True |
| 2024-06-26 | Official Creditor Committee Agreement | CALM | STRESS | True |
| 2024-09-19 | Bondholder Agreement-in-Principle | CALM | CALM | True |
| 2019-04-21 | Easter Sunday Attacks | CALM | CALM | True |
| 2020-03-20 | COVID Lockdown Begins | CALM | CALM | True |
| 2021-04-22 | Fertilizer Import Ban | CALM | STRESS | True |
| 2022-07-14 | President Resigns | CRISIS | CRISIS | True |

## Enhanced Validation

- tau: 0.7
- k: 3
- tactical_hit_rate: 54.5%
- strategic_hit_rate: 72.7%
