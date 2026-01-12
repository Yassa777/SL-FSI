"""Enhanced validation using sustained crossing logic."""

from __future__ import annotations

from typing import Iterable, Mapping

import pandas as pd

from slfsi.validation.event_alignment import EventSpec, evaluate_sustained_events


def run_enhanced_validation(
    probs_monthly: pd.DataFrame,
    events: Iterable[EventSpec],
    tau: float,
    k: int,
    tactical_months: int,
    strategic_months: int,
) -> Mapping[str, pd.DataFrame]:
    """Run sustained crossing validation.

    Economic intent:
        Sustained crossing requires persistent regime confidence, reducing
        false signals from noisy month-to-month fluctuations.

    Args:
        probs_monthly: Monthly probability dataframe.
        events: Iterable of EventSpec entries.
        tau: Probability threshold.
        k: Consecutive months required.
        tactical_months: Tactical window size.
        strategic_months: Strategic window size.

    Returns:
        Dict of tactical and strategic result dataframes.
    """
    tactical = evaluate_sustained_events(
        probs_monthly,
        events,
        tau=tau,
        k=k,
        window_months=tactical_months,
    )
    strategic = evaluate_sustained_events(
        probs_monthly,
        events,
        tau=tau,
        k=k,
        window_months=strategic_months,
    )
    return {"tactical": tactical, "strategic": strategic}
