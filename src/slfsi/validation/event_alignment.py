"""Event alignment utilities for regime validation."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable, List, Mapping

import pandas as pd


@dataclass(frozen=True)
class EventSpec:
    """Specification for a validation event."""

    date: pd.Timestamp
    name: str
    expected: str
    event_type: str


def parse_events(raw_events: Iterable[Mapping[str, str]]) -> List[EventSpec]:
    """Parse event specs from config.

    Economic intent:
        Pre-specified events anchor regime validation to known crisis
        milestones, avoiding ex-post tuning.

    Args:
        raw_events: Iterable of event dictionaries.

    Returns:
        List of EventSpec objects.
    """
    events: List[EventSpec] = []
    for raw in raw_events:
        events.append(
            EventSpec(
                date=pd.Timestamp(raw["date"]),
                name=str(raw["name"]),
                expected=str(raw["expected"]),
                event_type=str(raw.get("type", "anchor")),
            )
        )
    return events


def evaluate_event_alignment(
    monthly: pd.DataFrame,
    events: Iterable[EventSpec],
    model_col: str,
    window_months: int,
    date_col: str = "date",
) -> Mapping[str, object]:
    """Evaluate whether regimes align with known events.

    Economic intent:
        Tests whether model regimes line up with documented crisis milestones
        within a policy-relevant window.

    Args:
        monthly: Monthly dataframe with regime labels.
        events: Iterable of EventSpec entries.
        model_col: Column containing detected regimes.
        window_months: Evaluation window size in months.
        date_col: Date column name.

    Returns:
        Dict with hits, misses, and detailed per-event results.
    """
    results = {"hits": 0, "misses": 0, "details": []}

    monthly = monthly.copy()
    monthly["period"] = monthly[date_col].dt.to_period("M")

    for event in events:
        event_month = event.date.to_period("M")
        window_start = event_month - window_months
        window_end = event_month + window_months

        window_data = monthly[
            (monthly["period"] >= window_start) & (monthly["period"] <= window_end)
        ]

        if window_data.empty:
            results["details"].append(
                {
                    "date": event.date.strftime("%Y-%m-%d"),
                    "name": event.name,
                    "type": event.event_type,
                    "expected": event.expected,
                    "detected": "NO DATA",
                    "hit": False,
                    "in_window": False,
                }
            )
            results["misses"] += 1
            continue

        detected_regimes = window_data[model_col].unique().tolist()
        exact_month = window_data[window_data["period"] == event_month]
        if not exact_month.empty:
            detected_at_event = exact_month[model_col].values[0]
        else:
            detected_at_event = window_data[model_col].values[0]

        hit = event.expected in detected_regimes or detected_at_event == event.expected
        if hit:
            results["hits"] += 1
        else:
            results["misses"] += 1

        results["details"].append(
            {
                "date": event.date.strftime("%Y-%m-%d"),
                "name": event.name,
                "type": event.event_type,
                "expected": event.expected,
                "detected": detected_at_event,
                "all_in_window": detected_regimes,
                "hit": hit,
            }
        )

    return results


def evaluate_sustained_crossing(
    probs_monthly: pd.DataFrame,
    event: EventSpec,
    tau: float,
    k: int,
    window_months: int,
    date_col: str = "date",
) -> Mapping[str, object]:
    """Evaluate a sustained crossing event hit.

    Economic intent:
        Requires persistent regime confidence to avoid reacting to
        transient noise in stress probabilities.

    Args:
        probs_monthly: Monthly probabilities dataframe.
        event: Event specification.
        tau: Probability threshold.
        k: Consecutive months required.
        window_months: Evaluation window size.
        date_col: Date column name.

    Returns:
        Dict with hit status and diagnostics.
    """
    event_period = event.date.to_period("M")
    window_start = event_period - window_months
    window_end = event_period + window_months

    probs_monthly = probs_monthly.copy()
    probs_monthly["period"] = probs_monthly[date_col].dt.to_period("M")
    in_window = (probs_monthly["period"] >= window_start) & (probs_monthly["period"] <= window_end)
    window_probs = probs_monthly[in_window].copy()

    if window_probs.empty:
        return {
            "is_hit": False,
            "max_prob": 0.0,
            "sustained_count": 0,
            "window_probs": [],
            "reason": "No data in window",
        }

    prob_col = f"p_{event.expected.lower()}"
    if prob_col not in window_probs.columns:
        return {
            "is_hit": False,
            "max_prob": 0.0,
            "sustained_count": 0,
            "window_probs": [],
            "reason": f"Column {prob_col} not found",
        }

    probs = window_probs[prob_col].values
    max_prob = float(probs.max()) if len(probs) > 0 else 0.0
    above = (probs > tau).astype(int)

    sustained_count = 0
    for i in range(len(above) - k + 1):
        if above[i : i + k].sum() == k:
            sustained_count += 1

    is_hit = sustained_count > 0

    return {
        "is_hit": is_hit,
        "max_prob": max_prob,
        "sustained_count": sustained_count,
        "window_probs": probs.tolist(),
        "reason": "Hit" if is_hit else f"Max prob {max_prob:.1%} < {tau:.0%} or not sustained",
    }


def evaluate_sustained_events(
    probs_monthly: pd.DataFrame,
    events: Iterable[EventSpec],
    tau: float,
    k: int,
    window_months: int,
    date_col: str = "date",
) -> pd.DataFrame:
    """Evaluate sustained crossing for all events.

    Args:
        probs_monthly: Monthly probabilities dataframe.
        events: Iterable of EventSpec entries.
        tau: Probability threshold.
        k: Consecutive months required.
        window_months: Evaluation window size.
        date_col: Date column name.

    Returns:
        DataFrame of per-event results.
    """
    rows = []
    for event in events:
        result = evaluate_sustained_crossing(
            probs_monthly,
            event,
            tau=tau,
            k=k,
            window_months=window_months,
            date_col=date_col,
        )
        rows.append(
            {
                "date": event.date.strftime("%Y-%m-%d"),
                "event": event.name,
                "type": event.event_type,
                "expected_regime": event.expected,
                "is_hit": result["is_hit"],
                "max_prob": result["max_prob"],
                "sustained_count": result["sustained_count"],
                "reason": result["reason"],
            }
        )
    return pd.DataFrame(rows)
