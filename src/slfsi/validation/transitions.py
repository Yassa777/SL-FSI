"""Stress-to-crisis transition analysis."""

from __future__ import annotations

import logging
from typing import Any, Mapping

import pandas as pd

from slfsi.config.schema import ColumnSchema
from slfsi.config.settings import Settings


def _first_breach(df: pd.DataFrame, column: str, threshold: float, direction: str) -> pd.Timestamp | None:
    if direction == "above":
        breached = df[df[column] > threshold]
    else:
        breached = df[df[column] < threshold]
    if breached.empty:
        return None
    return breached.iloc[0]["date"]


def run_transitions(
    config: Mapping[str, Any],
    schema: ColumnSchema,
    settings: Settings,
) -> Mapping[str, Any]:
    """Analyze indicator thresholds during stress-to-crisis transitions.

    Economic intent:
        Identifies which macro indicators breach critical thresholds leading
        to regime escalation from stress to crisis.

    Args:
        config: Transition analysis configuration mapping.
        schema: Column schema.
        settings: Repository settings for path resolution.

    Returns:
        Dictionary with breach timeline and summary tables.
    """
    logger = logging.getLogger(__name__)
    regimes_path = settings.repo_root / config.get(
        "regimes_path", "data/merged/hmm_regimes_3state_monthly.csv"
    )
    if not regimes_path.exists():
        raise FileNotFoundError(f"Missing regimes data: {regimes_path}")

    regimes = pd.read_csv(regimes_path, parse_dates=[schema.date])
    if regimes.empty:
        raise ValueError("Regimes data is empty")

    thresholds = config.get("thresholds", {})
    key_dates = config.get("key_dates", {})
    default_date = pd.Timestamp(key_dates.get("default_date", "2022-04-12"))

    breach_rows = []
    for _, row in regimes.iterrows():
        breaches = []
        for feature, limits in thresholds.items():
            if feature not in regimes.columns:
                continue
            direction = limits.get("direction", "below")
            critical = float(limits.get("critical"))
            value = row[feature]
            if pd.isna(value):
                continue
            if (direction == "above" and value > critical) or (
                direction == "below" and value < critical
            ):
                breaches.append(feature)
        breach_rows.append(
            {
                "month": row[schema.date].strftime("%Y-%m"),
                schema.date: row[schema.date],
                "breaches": len(breaches),
                "indicators": ", ".join(breaches) if breaches else "-",
                "regime": row[schema.regime_label],
            }
        )

    breach_df = pd.DataFrame(breach_rows)

    summary_rows = []
    for feature, limits in thresholds.items():
        if feature not in regimes.columns:
            continue
        direction = limits.get("direction", "below")
        warning = float(limits.get("warning"))
        critical = float(limits.get("critical"))

        warning_date = _first_breach(regimes, feature, warning, direction)
        critical_date = _first_breach(regimes, feature, critical, direction)

        months_before_default = None
        if critical_date is not None:
            months_before_default = int((default_date - critical_date).days / 30)

        summary_rows.append(
            {
                "indicator": feature,
                "warning_threshold": warning,
                "critical_threshold": critical,
                "direction": direction,
                "first_warning": warning_date.strftime("%Y-%m") if warning_date else None,
                "first_critical": critical_date.strftime("%Y-%m") if critical_date else None,
                "months_before_default": months_before_default,
            }
        )

    summary_df = pd.DataFrame(summary_rows)

    outputs = config.get("outputs", {})
    breach_out = outputs.get("breach_timeline")
    summary_out = outputs.get("summary")
    if breach_out:
        path = settings.repo_root / breach_out
        path.parent.mkdir(parents=True, exist_ok=True)
        breach_df.to_csv(path, index=False)
        logger.info("Saved breach timeline: %s", path)
    if summary_out:
        path = settings.repo_root / summary_out
        path.parent.mkdir(parents=True, exist_ok=True)
        summary_df.to_csv(path, index=False)
        logger.info("Saved threshold summary: %s", path)

    return {"breach_timeline": breach_df, "summary": summary_df}
