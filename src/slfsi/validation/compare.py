"""Compare Mercado FSI to HMM regimes."""

from __future__ import annotations

import logging
from typing import Any, Mapping

import pandas as pd
from scipy import stats

from slfsi.config.schema import ColumnSchema
from slfsi.config.settings import Settings


def run_compare(
    config: Mapping[str, Any],
    schema: ColumnSchema,
    settings: Settings,
) -> Mapping[str, Any]:
    """Compare Mercado FSI levels across HMM regimes.

    Economic intent:
        Validates that continuous stress indices align with discrete
        regime classification.

    Args:
        config: Comparison configuration mapping.
        schema: Column schema.
        settings: Repository settings for path resolution.

    Returns:
        Dictionary of computed statistics and optional artifacts.
    """
    logger = logging.getLogger(__name__)

    fsi_path = settings.repo_root / config.get(
        "fsi_path", "data/merged/mercado_fsi_monthly.csv"
    )
    hmm_path = settings.repo_root / config.get(
        "hmm_path", "data/merged/hmm_regimes_3state_monthly.csv"
    )
    fsi_col = config.get("fsi_column", "fsi_variance_equal")

    if not fsi_path.exists() or not hmm_path.exists():
        raise FileNotFoundError("FSI or HMM regimes file missing")

    fsi = pd.read_csv(fsi_path, parse_dates=[schema.date])
    hmm = pd.read_csv(hmm_path, parse_dates=[schema.date])

    merged = pd.merge(
        fsi, hmm[[schema.date, schema.regime, schema.regime_label]], on=schema.date, how="inner"
    )
    if merged.empty:
        raise ValueError("No overlapping observations between FSI and HMM data")

    stats_df = (
        merged.groupby(schema.regime_label)[fsi_col]
        .agg(["count", "mean", "std", "min", "max"])
        .round(3)
    )

    groups = [
        merged[merged[schema.regime_label] == label][fsi_col].dropna()
        for label in ["CALM", "STRESS", "CRISIS"]
    ]
    groups = [g for g in groups if len(g) > 1]
    anova = None
    if len(groups) >= 2:
        f_stat, p_value = stats.f_oneway(*groups)
        anova = {"f_stat": float(f_stat), "p_value": float(p_value)}
        logger.info("ANOVA p-value: %.4f", p_value)

    component_means: dict[str, dict[str, float]] = {}
    for col in config.get("component_columns", []):
        if col in merged.columns:
            component_means[col] = (
                merged.groupby(schema.regime_label)[col].mean().round(3).to_dict()
            )

    threshold_summary = []
    for threshold in config.get("thresholds", []):
        above = merged[merged[fsi_col] > threshold][schema.regime_label].value_counts()
        below = merged[merged[fsi_col] <= threshold][schema.regime_label].value_counts()
        threshold_summary.append(
            {
                "threshold": float(threshold),
                "above": above.to_dict(),
                "below": below.to_dict(),
            }
        )

    stress_threshold = float(config.get("stress_threshold", 0.3))
    crisis_threshold = float(config.get("crisis_threshold", 1.0))

    hmm_stress_start = merged[merged[schema.regime_label] == "STRESS"][schema.date].min()
    hmm_crisis_start = merged[merged[schema.regime_label] == "CRISIS"][schema.date].min()

    early_warning = {}
    if pd.notna(hmm_stress_start):
        pre_stress = merged[merged[schema.date] < hmm_stress_start]
        fsi_warn = pre_stress[pre_stress[fsi_col] > stress_threshold]
        if not fsi_warn.empty:
            first_warning = fsi_warn.iloc[0]
            lead_months = int((hmm_stress_start - first_warning[schema.date]).days / 30)
            early_warning["stress_lead_months"] = lead_months

    if pd.notna(hmm_crisis_start):
        pre_crisis = merged[merged[schema.date] < hmm_crisis_start]
        fsi_warn = pre_crisis[pre_crisis[fsi_col] > crisis_threshold]
        if not fsi_warn.empty:
            first_warning = fsi_warn.iloc[0]
            lead_months = int((hmm_crisis_start - first_warning[schema.date]).days / 30)
            early_warning["crisis_lead_months"] = lead_months

    plot_path = config.get("outputs", {}).get("plot")
    if plot_path:
        try:
            import matplotlib.pyplot as plt

            fig, axes = plt.subplots(2, 1, figsize=(14, 8), sharex=True)
            regime_colors = {"CALM": "lightgreen", "STRESS": "khaki", "CRISIS": "lightcoral"}

            ax1 = axes[0]
            for regime, color in regime_colors.items():
                regime_dates = merged[merged[schema.regime_label] == regime][schema.date]
                if regime_dates.empty:
                    continue
                for idx, date in enumerate(regime_dates):
                    ax1.axvspan(
                        date - pd.Timedelta(days=15),
                        date + pd.Timedelta(days=15),
                        alpha=0.3,
                        color=color,
                        label=regime if idx == 0 else "",
                    )
            ax1.plot(merged[schema.date], merged[fsi_col], color="navy", linewidth=2, label="FSI")
            ax1.axhline(0, color="gray", linestyle="--", alpha=0.5)
            ax1.set_ylabel("FSI (Standardized)")
            ax1.set_title("Mercado FSI with HMM Regime Shading")
            ax1.legend(loc="upper left")
            ax1.grid(True, alpha=0.3)

            ax2 = axes[1]
            regime_numeric = {"CALM": 0, "STRESS": 1, "CRISIS": 2}
            merged["_regime_num"] = merged[schema.regime_label].map(regime_numeric)
            ax2.fill_between(
                merged[schema.date],
                0,
                merged["_regime_num"],
                step="mid",
                alpha=0.4,
                color="coral",
                label="HMM Regime",
            )
            fsi_norm = (merged[fsi_col] - merged[fsi_col].min()) / (
                merged[fsi_col].max() - merged[fsi_col].min()
            ) * 2
            ax2.plot(merged[schema.date], fsi_norm, color="navy", linewidth=1.5, label="FSI")
            ax2.set_ylabel("Regime / FSI")
            ax2.set_xlabel("Date")
            ax2.set_yticks([0, 1, 2])
            ax2.set_yticklabels(["CALM", "STRESS", "CRISIS"])
            ax2.set_title("HMM Regime Classification vs Mercado FSI")
            ax2.legend(loc="upper left")
            ax2.grid(True, alpha=0.3)

            plt.tight_layout()
            out_path = settings.repo_root / plot_path
            out_path.parent.mkdir(parents=True, exist_ok=True)
            plt.savefig(out_path, dpi=150, bbox_inches="tight")
            plt.close()
            logger.info("Saved comparison plot: %s", out_path)
        except Exception as exc:
            logger.warning("Plot generation skipped: %s", exc)

    return {
        "regime_stats": stats_df,
        "anova": anova,
        "component_means": component_means,
        "thresholds": threshold_summary,
        "early_warning": early_warning,
    }
