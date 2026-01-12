"""Three-panel comparison plot for FSI and HMM outputs."""

from __future__ import annotations

import logging
from typing import Any, Mapping

import pandas as pd

from slfsi.config.schema import ColumnSchema
from slfsi.config.settings import Settings


def run_three_panel(
    config: Mapping[str, Any],
    schema: ColumnSchema,
    settings: Settings,
) -> None:
    """Generate the three-panel comparison plot.

    Economic intent:
        Visual comparison highlights how market-based stress and macro
        regimes align or diverge across crisis phases.
    """
    logger = logging.getLogger(__name__)
    try:
        import matplotlib.pyplot as plt
        import matplotlib.gridspec as gridspec
    except ImportError as exc:
        raise RuntimeError("matplotlib is required for three-panel plotting") from exc

    fsi_path = settings.repo_root / config.get("fsi_path", "data/merged/mercado_fsi_monthly.csv")
    hmm_path = settings.repo_root / config.get("hmm_probs_path", "data/merged/hmm_probs_monthly.csv")
    combined_path = settings.repo_root / config.get("combined_path", "data/merged/combined_fsi_hmm.csv")

    if not fsi_path.exists() or not hmm_path.exists() or not combined_path.exists():
        raise FileNotFoundError("Missing inputs for three-panel plot")

    fsi_df = pd.read_csv(fsi_path, parse_dates=[schema.date])
    hmm_df = pd.read_csv(hmm_path, parse_dates=[schema.date])
    combined_df = pd.read_csv(combined_path, parse_dates=[schema.date])

    events = {event["date"]: event["label"] for event in config.get("events", [])}

    def create_panel1(ax_main, ax_components, ax_formula) -> None:
        ax_main.plot(fsi_df[schema.date], fsi_df["fsi_variance_equal"], color="#1f77b4", linewidth=2)
        ax_main.axhline(0, color="gray", linestyle="--", alpha=0.5)
        ax_main.axhline(1, color="red", linestyle=":", alpha=0.7)
        ax_main.axhline(-1, color="green", linestyle=":", alpha=0.7)

        for date_str in events:
            date = pd.Timestamp(date_str)
            ax_main.axvline(date, color="red", alpha=0.3, linestyle="-")

        ax_main.set_ylabel("FSI (Standardized)", fontsize=10)
        ax_main.set_title("Panel 1: CBSL/Mercado-Park Financial Stress Index", fontsize=12)
        ax_main.grid(True, alpha=0.3)

        component_cols = ["banking_beta", "equity_volatility", "empi"]
        colors = ["#ff7f0e", "#2ca02c", "#9467bd"]
        for i, col in enumerate(component_cols):
            if col not in fsi_df.columns:
                continue
            series = fsi_df[col].dropna()
            if series.empty:
                continue
            std_series = (series - series.mean()) / series.std()
            ax_components.plot(
                fsi_df.loc[series.index, schema.date],
                std_series,
                alpha=0.7,
                linewidth=1,
                color=colors[i],
                label=col.replace("_", " ").title(),
            )

        ax_components.set_ylabel("Standardized", fontsize=9)
        ax_components.set_xlabel("Date", fontsize=9)
        ax_components.legend(loc="upper left", fontsize=7)
        ax_components.grid(True, alpha=0.3)
        ax_components.set_title("FSI Components", fontsize=10)

        ax_formula.axis("off")
        ax_formula.text(
            0.02,
            0.98,
            "MERCADO-PARK FSI\n(see methodology docs)",
            transform=ax_formula.transAxes,
            fontsize=8,
            verticalalignment="top",
            bbox=dict(boxstyle="round", facecolor="lightblue", alpha=0.3),
        )

    def create_panel2(ax_main, ax_probs, ax_formula) -> None:
        ax_main.stackplot(
            hmm_df[schema.date],
            hmm_df["p_calm"],
            hmm_df["p_stress"],
            hmm_df["p_crisis"],
            labels=["P(CALM)", "P(STRESS)", "P(CRISIS)"],
            colors=["#90EE90", "#FFD700", "#FF6B6B"],
            alpha=0.8,
        )
        for date_str in events:
            date = pd.Timestamp(date_str)
            ax_main.axvline(date, color="black", alpha=0.5, linestyle="--")
        ax_main.set_ylabel("Regime Probability", fontsize=10)
        ax_main.set_title("Panel 2: Recursive 3-State HMM", fontsize=12)
        ax_main.legend(loc="upper left", fontsize=8)
        ax_main.set_ylim(0, 1)

        ax_probs.plot(hmm_df[schema.date], hmm_df["confidence"], color="purple", linewidth=1.5)
        ax_probs.set_ylabel("Confidence", fontsize=9)
        ax_probs.set_xlabel("Date", fontsize=9)
        ax_probs.set_ylim(0, 1.1)
        ax_probs.grid(True, alpha=0.3)
        ax_probs.set_title("Regime Confidence", fontsize=10)

        ax_formula.axis("off")
        ax_formula.text(
            0.02,
            0.98,
            "RECURSIVE HMM\n(see methodology docs)",
            transform=ax_formula.transAxes,
            fontsize=8,
            verticalalignment="top",
            bbox=dict(boxstyle="round", facecolor="lightyellow", alpha=0.3),
        )

    def create_panel3(ax_main, ax_disagreement, ax_stats) -> None:
        ax_main.plot(
            combined_df[schema.date],
            combined_df["fsi_std"],
            color="#1f77b4",
            linewidth=1.5,
            label="FSI (standardized)",
        )
        ax_main.plot(
            combined_df[schema.date],
            combined_df["hmm_stress_prob"],
            color="#d62728",
            linewidth=1.5,
            label="HMM Stress Prob",
        )
        ax_main.plot(
            combined_df[schema.date],
            combined_df["combined_stress_norm"],
            color="purple",
            linewidth=2,
            linestyle="--",
            label="Combined Score",
        )
        ax_main.axhline(0.5, color="orange", linestyle=":", alpha=0.5)
        ax_main.axhline(0.7, color="red", linestyle=":", alpha=0.5)
        for date_str in events:
            date = pd.Timestamp(date_str)
            ax_main.axvline(date, color="red", alpha=0.3, linestyle="-")
        ax_main.set_ylabel("Score", fontsize=10)
        ax_main.set_title("Panel 3: FSI vs HMM Combination", fontsize=12)
        ax_main.legend(loc="upper left", fontsize=8)
        ax_main.grid(True, alpha=0.3)

        fsi_high = combined_df["fsi_std"] > 1
        hmm_calm = combined_df["p_calm"] > 0.5
        early_warning = fsi_high & hmm_calm

        hmm_crisis = combined_df["p_crisis"] > 0.5
        fsi_normal = combined_df["fsi_std"] < 0.5
        false_alarm = hmm_crisis & fsi_normal

        ax_disagreement.fill_between(
            combined_df[schema.date],
            0,
            1,
            where=early_warning,
            color="orange",
            alpha=0.5,
            label="Early Warning",
        )
        ax_disagreement.fill_between(
            combined_df[schema.date],
            0,
            -1,
            where=false_alarm,
            color="purple",
            alpha=0.5,
            label="False Alarm",
        )
        ax_disagreement.axhline(0, color="gray", linestyle="-", alpha=0.5)
        ax_disagreement.set_ylabel("Signal", fontsize=9)
        ax_disagreement.set_xlabel("Date", fontsize=9)
        ax_disagreement.set_ylim(-1.5, 1.5)
        ax_disagreement.legend(loc="upper left", fontsize=7)
        ax_disagreement.grid(True, alpha=0.3)
        ax_disagreement.set_title("Disagreement Signals", fontsize=10)

        corr = combined_df["fsi_std"].corr(combined_df["hmm_stress_prob"])
        agreement_rate = combined_df["agreement"].mean() * 100
        ax_stats.axis("off")
        ax_stats.text(
            0.02,
            0.98,
            f"Correlation: r = {corr:.2f}\nAgreement: {agreement_rate:.1f}%",
            transform=ax_stats.transAxes,
            fontsize=8,
            verticalalignment="top",
            bbox=dict(boxstyle="round", facecolor="lightgreen", alpha=0.3),
        )

    fig = plt.figure(figsize=(20, 16))
    grid = gridspec.GridSpec(3, 3, figure=fig, height_ratios=[1, 1, 1], width_ratios=[2, 1, 1])

    create_panel1(fig.add_subplot(grid[0, 0]), fig.add_subplot(grid[0, 1]), fig.add_subplot(grid[0, 2]))
    create_panel2(fig.add_subplot(grid[1, 0]), fig.add_subplot(grid[1, 1]), fig.add_subplot(grid[1, 2]))
    create_panel3(fig.add_subplot(grid[2, 0]), fig.add_subplot(grid[2, 1]), fig.add_subplot(grid[2, 2]))

    fig.suptitle(
        "Sri Lanka Financial Stress Index: CBSL FSI vs Recursive HMM Comparison",
        fontsize=14,
        fontweight="bold",
        y=0.995,
    )

    outputs = config.get("outputs", {})
    plot_path = settings.repo_root / outputs.get("plot", "figures/three_panel_comparison.png")
    plot_path.parent.mkdir(parents=True, exist_ok=True)
    plt.savefig(plot_path, dpi=150, bbox_inches="tight", facecolor="white", edgecolor="none")
    logger.info("Saved three-panel plot: %s", plot_path)

    plot_hires = outputs.get("plot_hires")
    if plot_hires:
        hires_path = settings.repo_root / plot_hires
        plt.savefig(hires_path, dpi=300, bbox_inches="tight", facecolor="white", edgecolor="none")
        logger.info("Saved high-res plot: %s", hires_path)

    plt.close()
