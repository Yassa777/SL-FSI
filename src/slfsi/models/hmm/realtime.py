"""Real-time recursive HMM estimation."""

from __future__ import annotations

import logging
from typing import Any, Mapping, Optional

import pandas as pd

from slfsi.config.schema import ColumnSchema
from slfsi.models.hmm.fit import HMMModelConfig, fit_hmm_with_probs


def _event_lookup(events: list[Mapping[str, str]]) -> dict[str, str]:
    lookup: dict[str, str] = {}
    for event in events:
        month = event.get("month")
        label = event.get("label")
        if month and label:
            lookup[str(month)] = str(label)
    return lookup


def run_realtime(
    monthly: pd.DataFrame,
    model_config: HMMModelConfig,
    schema: ColumnSchema,
    config: Mapping[str, Any],
    *,
    full_sample: Optional[pd.DataFrame] = None,
) -> tuple[pd.DataFrame, Optional[pd.DataFrame]]:
    """Run recursive real-time HMM estimation.

    Economic intent:
        Recursively re-fitting the HMM simulates a policymaker's view using
        only information available at each point in time.

    Args:
        monthly: Monthly panel dataframe.
        model_config: HMM model configuration.
        schema: Column schema.
        config: Real-time configuration mapping.
        full_sample: Optional full-sample regimes for comparison.

    Returns:
        Tuple of (realtime results dataframe, comparison dataframe or None).
    """
    logger = logging.getLogger(__name__)
    start = pd.Timestamp(config.get("start", monthly[schema.date].min()))
    eval_start = pd.Timestamp(config.get("eval_start", start))
    min_training = int(config.get("min_training_months", 12))
    stable_window = int(config.get("stable_window_months", 3))
    stable_key = f"stable_{stable_window}m"

    filtered = monthly[monthly[schema.date] >= start].copy()
    filtered["year_month_str"] = filtered[schema.date].dt.strftime("%Y-%m")
    filtered["period"] = filtered[schema.date].dt.to_period("M")

    if filtered.empty:
        raise ValueError("No monthly data available for realtime HMM range")

    eval_idx = filtered[filtered[schema.date] >= eval_start].index
    if eval_idx.empty:
        raise ValueError("Evaluation start date is outside available data range")
    eval_start_idx = eval_idx[0]

    events = _event_lookup(config.get("key_events", []))
    results = []

    for idx in range(eval_start_idx, len(filtered)):
        window = filtered.iloc[: idx + 1].copy()
        if len(window) < min_training:
            continue

        try:
            fitted, _, _ = fit_hmm_with_probs(window, model_config, schema)
        except Exception as exc:
            logger.warning("Realtime HMM failed at %s: %s", window.iloc[-1][schema.date], exc)
            continue

        current = fitted.iloc[-1]
        recent = fitted.tail(stable_window)[schema.regime_label].tolist()
        stable = len(set(recent)) == 1 if len(recent) == stable_window else False
        month_str = current["year_month_str"]

        results.append(
            {
                "month": month_str,
                schema.date: current[schema.date],
                schema.period: current["period"],
                "n_training": len(window),
                schema.regime_realtime: current[schema.regime_label],
                schema.p_calm: current.get(schema.p_calm, current.get("p_calm", float("nan"))),
                schema.p_stress: current.get(schema.p_stress, current.get("p_stress", float("nan"))),
                schema.p_crisis: current.get(schema.p_crisis, current.get("p_crisis", float("nan"))),
                schema.confidence: current[schema.confidence],
                stable_key: stable,
                "key_event": events.get(month_str, ""),
            }
        )

    results_df = pd.DataFrame(results)

    comparison_df = None
    if full_sample is not None and not full_sample.empty and not results_df.empty:
        full_sample = full_sample.copy()
        full_sample["year_month_str"] = full_sample[schema.date].dt.strftime("%Y-%m")
        comparison_df = results_df.merge(
            full_sample[[schema.date, "year_month_str", schema.regime_label]],
            left_on="month",
            right_on="year_month_str",
            how="left",
            suffixes=("", "_full"),
        ).rename(columns={schema.regime_label: "regime_fullsample"})

    return results_df, comparison_df
