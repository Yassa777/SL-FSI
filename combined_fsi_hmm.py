#!/usr/bin/env python3
"""
Combined FSI-HMM Early Warning Framework
=========================================
Combines Mercado FSI (continuous) with HMM regimes (probabilistic)
for a complementary early warning system.

Key Features:
1. Weighted average combination: α * FSI + (1-α) * HMM_stress_prob
2. Disagreement detection: When FSI and HMM signals diverge
3. Early warning evaluation using combined score

Run: python combined_fsi_hmm.py
"""

import pandas as pd
import numpy as np
from datetime import timedelta
import warnings
warnings.filterwarnings('ignore')

# ============================================================
# CONFIGURATION
# ============================================================

ALPHA = 0.5  # Weight for FSI (0.5 = equal weighting)

# Thresholds for combined score
STRESS_THRESHOLD = 0.5
CRISIS_THRESHOLD = 0.7

# ============================================================
# CORE FUNCTIONS
# ============================================================

def load_and_align_data():
    """Load FSI and HMM probability data and align on date."""
    print("Loading data...")

    # Load FSI
    try:
        fsi_df = pd.read_csv('data/merged/mercado_fsi_monthly.csv', parse_dates=['date'])
        print(f"  FSI: {len(fsi_df)} months ({fsi_df['date'].min().strftime('%Y-%m')} to {fsi_df['date'].max().strftime('%Y-%m')})")
    except Exception as e:
        print(f"  ERROR loading FSI: {e}")
        return None

    # Load HMM probabilities
    try:
        hmm_df = pd.read_csv('data/merged/hmm_probs_monthly.csv', parse_dates=['date'])
        print(f"  HMM: {len(hmm_df)} months ({hmm_df['date'].min().strftime('%Y-%m')} to {hmm_df['date'].max().strftime('%Y-%m')})")
    except Exception as e:
        print(f"  ERROR loading HMM: {e}")
        return None

    # Merge on date
    merged = pd.merge(
        fsi_df[['date', 'fsi_variance_equal', 'banking_beta', 'equity_volatility', 'empi']],
        hmm_df[['date', 'p_calm', 'p_stress', 'p_crisis', 'regime_realtime', 'confidence']],
        on='date',
        how='inner'
    )

    print(f"  Merged: {len(merged)} months")

    return merged


def compute_combined_score(merged_df, alpha=ALPHA):
    """
    Compute combined FSI-HMM stress score.

    combined_stress = α * FSI_standardized + (1-α) * HMM_stress_prob

    Where:
    - FSI_standardized: (fsi - mean) / std
    - HMM_stress_prob: p_stress + p_crisis (probability of non-CALM)
    """
    df = merged_df.copy()

    # Standardize FSI
    fsi_mean = df['fsi_variance_equal'].mean()
    fsi_std = df['fsi_variance_equal'].std()
    df['fsi_std'] = (df['fsi_variance_equal'] - fsi_mean) / fsi_std

    # HMM stress probability (non-CALM)
    df['hmm_stress_prob'] = df['p_stress'] + df['p_crisis']

    # Combined score
    df['combined_stress'] = alpha * df['fsi_std'] + (1 - alpha) * df['hmm_stress_prob']

    # Normalize combined score to 0-1 range for easier interpretation
    comb_min = df['combined_stress'].min()
    comb_max = df['combined_stress'].max()
    df['combined_stress_norm'] = (df['combined_stress'] - comb_min) / (comb_max - comb_min)

    return df


def detect_disagreements(df, fsi_threshold=1.0, hmm_threshold=0.5):
    """
    Detect when FSI and HMM disagree.

    Early Warning: FSI high but HMM still CALM
    Possible False Alarm: HMM CRISIS but FSI normal
    """
    # Early warning: FSI elevated but HMM calm
    df['early_warning'] = (df['fsi_std'] > fsi_threshold) & (df['p_calm'] > hmm_threshold)

    # Possible false alarm: HMM crisis but FSI normal
    df['possible_false_alarm'] = (df['p_crisis'] > hmm_threshold) & (df['fsi_std'] < 0.5)

    # Agreement: Both elevated or both calm
    df['agreement'] = ~(df['early_warning'] | df['possible_false_alarm'])

    return df


def analyze_early_warning(df):
    """Analyze early warning signals from combined framework."""
    print("\n" + "=" * 80)
    print("EARLY WARNING ANALYSIS")
    print("=" * 80)

    # Key events
    default_date = pd.Timestamp('2022-04-12')

    # When did combined score first exceed thresholds?
    stress_signals = df[df['combined_stress_norm'] > STRESS_THRESHOLD]
    crisis_signals = df[df['combined_stress_norm'] > CRISIS_THRESHOLD]

    print(f"\nDefault Date: {default_date.strftime('%Y-%m-%d')}")

    if len(stress_signals) > 0:
        first_stress = stress_signals.iloc[0]
        lead_days = (default_date - first_stress['date']).days
        print(f"\nFirst STRESS signal (combined > {STRESS_THRESHOLD}):")
        print(f"  Date: {first_stress['date'].strftime('%Y-%m')}")
        print(f"  Combined score: {first_stress['combined_stress_norm']:.2f}")
        print(f"  FSI: {first_stress['fsi_std']:.2f}, HMM stress prob: {first_stress['hmm_stress_prob']:.2f}")
        print(f"  Lead time: {lead_days} days ({lead_days // 30} months)")

    if len(crisis_signals) > 0:
        first_crisis = crisis_signals.iloc[0]
        lead_days = (default_date - first_crisis['date']).days
        print(f"\nFirst CRISIS signal (combined > {CRISIS_THRESHOLD}):")
        print(f"  Date: {first_crisis['date'].strftime('%Y-%m')}")
        print(f"  Combined score: {first_crisis['combined_stress_norm']:.2f}")
        print(f"  FSI: {first_crisis['fsi_std']:.2f}, HMM stress prob: {first_crisis['hmm_stress_prob']:.2f}")
        if lead_days > 0:
            print(f"  Lead time: {lead_days} days ({lead_days // 30} months) before default")
        else:
            print(f"  Lead time: {abs(lead_days)} days after default")


def analyze_disagreements(df):
    """Analyze disagreement signals."""
    print("\n" + "=" * 80)
    print("DISAGREEMENT ANALYSIS")
    print("=" * 80)

    # Early warnings (FSI up, HMM calm)
    early_warnings = df[df['early_warning']]
    print(f"\nEarly Warning Signals (FSI > 1σ but HMM CALM > 50%):")
    print(f"  Total: {len(early_warnings)} months")

    if len(early_warnings) > 0:
        for _, row in early_warnings.head(5).iterrows():
            print(f"    {row['date'].strftime('%Y-%m')}: FSI={row['fsi_std']:.2f}, P(CALM)={row['p_calm']:.1%}")

    # Possible false alarms (HMM crisis, FSI normal)
    false_alarms = df[df['possible_false_alarm']]
    print(f"\nPossible False Alarms (HMM CRISIS > 50% but FSI < 0.5σ):")
    print(f"  Total: {len(false_alarms)} months")

    if len(false_alarms) > 0:
        for _, row in false_alarms.head(5).iterrows():
            print(f"    {row['date'].strftime('%Y-%m')}: FSI={row['fsi_std']:.2f}, P(CRISIS)={row['p_crisis']:.1%}")

    # Agreement rate
    agreement_rate = df['agreement'].mean()
    print(f"\nAgreement Rate: {agreement_rate:.1%}")


def generate_combined_report():
    """Generate full combined FSI-HMM analysis report."""

    print("=" * 80)
    print("COMBINED FSI-HMM EARLY WARNING FRAMEWORK")
    print(f"Weight α = {ALPHA} (FSI:{ALPHA:.0%}, HMM:{1-ALPHA:.0%})")
    print("=" * 80)

    # Load and align data
    merged = load_and_align_data()
    if merged is None:
        return None

    # Compute combined score
    print("\nComputing combined stress score...")
    df = compute_combined_score(merged, alpha=ALPHA)

    # Detect disagreements
    df = detect_disagreements(df)

    # ============================================================
    # Timeline Analysis
    # ============================================================

    print("\n" + "=" * 80)
    print("TIMELINE: FSI vs HMM vs COMBINED")
    print("=" * 80)

    # Key dates
    key_dates = [
        ('2020-01', 'Pre-Crisis Baseline'),
        ('2021-07', 'STRESS Begins (HMM)'),
        ('2022-01', '$500M ISB Repayment'),
        ('2022-04', 'Sovereign Default'),
        ('2022-09', 'Peak Inflation'),
        ('2023-03', 'IMF EFF Approval'),
        ('2023-07', 'Recovery Begins'),
        ('2024-01', 'CALM Returns'),
    ]

    print(f"\n{'Date':<10} {'Event':<22} {'FSI':<8} {'HMM Prob':<10} {'Combined':<10} {'HMM Regime':<10}")
    print("-" * 75)

    for date_str, event in key_dates:
        date = pd.Timestamp(date_str + '-01')
        row = df[df['date'].dt.to_period('M') == date.to_period('M')]

        if len(row) > 0:
            r = row.iloc[0]
            print(f"{date_str:<10} {event[:20]:<22} {r['fsi_std']:<8.2f} {r['hmm_stress_prob']:<10.2f} {r['combined_stress_norm']:<10.2f} {r['regime_realtime']:<10}")

    # Early warning analysis
    analyze_early_warning(df)

    # Disagreement analysis
    analyze_disagreements(df)

    # ============================================================
    # Correlation Analysis
    # ============================================================

    print("\n" + "=" * 80)
    print("CORRELATION ANALYSIS")
    print("=" * 80)

    corr_fsi_hmm = df['fsi_std'].corr(df['hmm_stress_prob'])
    print(f"\nFSI vs HMM stress prob: r = {corr_fsi_hmm:.3f}")

    # Component correlations
    print("\nFSI Components vs HMM stress prob:")
    for comp in ['banking_beta', 'equity_volatility', 'empi']:
        if comp in df.columns:
            valid = df[[comp, 'hmm_stress_prob']].dropna()
            if len(valid) > 10:
                corr = valid[comp].corr(valid['hmm_stress_prob'])
                print(f"  {comp}: r = {corr:.3f}")

    # ============================================================
    # Summary
    # ============================================================

    print("\n" + "=" * 80)
    print("SUMMARY")
    print("=" * 80)

    print(f"""
METHODOLOGY:
  Combined Score = {ALPHA:.0%} × FSI + {1-ALPHA:.0%} × HMM_stress_prob

KEY FINDINGS:
  - FSI-HMM Correlation: {corr_fsi_hmm:.2f}
  - Agreement Rate: {df['agreement'].mean():.1%}
  - Early Warning Signals: {df['early_warning'].sum()} months
  - Possible False Alarms: {df['possible_false_alarm'].sum()} months

INTERPRETATION:
  - High combined score: Both market-based (FSI) and macro-based (HMM) indicators
    suggest elevated financial stress
  - Disagreement signals: When FSI and HMM diverge, investigate further
    • Early warning: FSI rising before HMM detects regime change
    • False alarm: HMM detects regime but market stress is low
""")

    # Save results
    output_cols = ['date', 'fsi_variance_equal', 'fsi_std', 'p_calm', 'p_stress', 'p_crisis',
                   'hmm_stress_prob', 'combined_stress', 'combined_stress_norm',
                   'regime_realtime', 'early_warning', 'possible_false_alarm', 'agreement']
    df[output_cols].to_csv('data/merged/combined_fsi_hmm.csv', index=False)
    print("\nSaved: data/merged/combined_fsi_hmm.csv")

    # ============================================================
    # Visualization
    # ============================================================

    try:
        import matplotlib.pyplot as plt

        fig, axes = plt.subplots(3, 1, figsize=(14, 10), sharex=True)

        # Plot 1: Combined score with components
        ax1 = axes[0]
        ax1.plot(df['date'], df['fsi_std'], label='FSI (standardized)', alpha=0.7, linewidth=1)
        ax1.plot(df['date'], df['hmm_stress_prob'], label='HMM Stress Prob', alpha=0.7, linewidth=1)
        ax1.plot(df['date'], df['combined_stress_norm'], label='Combined Score', color='navy', linewidth=2)
        ax1.axhline(STRESS_THRESHOLD, color='orange', linestyle='--', alpha=0.5, label=f'Stress threshold ({STRESS_THRESHOLD})')
        ax1.axhline(CRISIS_THRESHOLD, color='red', linestyle='--', alpha=0.5, label=f'Crisis threshold ({CRISIS_THRESHOLD})')
        ax1.set_ylabel('Score')
        ax1.set_title('Combined FSI-HMM Early Warning Score')
        ax1.legend(loc='upper left', fontsize=8)
        ax1.grid(True, alpha=0.3)

        # Add default annotation
        ax1.axvline(pd.Timestamp('2022-04-12'), color='red', linestyle=':', alpha=0.7)
        ax1.text(pd.Timestamp('2022-04-12'), ax1.get_ylim()[1], 'Default', rotation=90, va='top', fontsize=8)

        # Plot 2: Regime probabilities stacked
        ax2 = axes[1]
        ax2.stackplot(df['date'], df['p_calm'], df['p_stress'], df['p_crisis'],
                      labels=['P(CALM)', 'P(STRESS)', 'P(CRISIS)'],
                      colors=['lightgreen', 'khaki', 'lightcoral'], alpha=0.7)
        ax2.set_ylabel('Probability')
        ax2.set_title('HMM Regime Probabilities')
        ax2.legend(loc='upper left', fontsize=8)
        ax2.set_ylim(0, 1)

        # Plot 3: Disagreement indicators
        ax3 = axes[2]
        ax3.fill_between(df['date'], 0, df['early_warning'].astype(int),
                        where=df['early_warning'], color='orange', alpha=0.5, label='Early Warning')
        ax3.fill_between(df['date'], 0, -df['possible_false_alarm'].astype(int),
                        where=df['possible_false_alarm'], color='purple', alpha=0.5, label='Possible False Alarm')
        ax3.set_ylabel('Signal')
        ax3.set_xlabel('Date')
        ax3.set_title('FSI-HMM Disagreement Signals')
        ax3.legend(loc='upper left', fontsize=8)
        ax3.set_ylim(-1.5, 1.5)
        ax3.axhline(0, color='gray', linestyle='-', alpha=0.3)

        plt.tight_layout()
        plt.savefig('figures/combined_fsi_hmm.png', dpi=150, bbox_inches='tight')
        print("Saved: figures/combined_fsi_hmm.png")
        plt.close()

    except Exception as e:
        print(f"\nCould not create plot: {e}")

    return df


# ============================================================
# MAIN
# ============================================================

if __name__ == '__main__':
    df = generate_combined_report()
