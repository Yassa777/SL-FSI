"""Validation framework for HMM regimes and baselines."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable, Mapping, Tuple

import numpy as np
import pandas as pd
from hmmlearn import hmm

from slfsi.validation.event_alignment import EventSpec, evaluate_event_alignment


@dataclass(frozen=True)
class HMMConfig:
    """HMM configuration parameters."""

    features: Tuple[str, ...]
    n_states: int
    covariance_type: str
    n_iter: int
    random_state: int


def build_monthly_from_daily(daily: pd.DataFrame, features: Iterable[str]) -> pd.DataFrame:
    """Aggregate daily panel to monthly frequency using first observations.

    Economic intent:
        Aligns macro series to monthly resolution while retaining the
        first observation in each month as a consistent anchor.

    Args:
        daily: Daily panel dataframe.
        features: Feature column names.

    Returns:
        Monthly dataframe with required features and date column.
    """
    daily = daily.copy()
    daily["year_month"] = daily["date"].dt.to_period("M")
    monthly = daily.groupby("year_month")[list(features) + ["date"]].first().reset_index(drop=True)
    return monthly.dropna()


def fit_hmm(monthly: pd.DataFrame, config: HMMConfig) -> Tuple[pd.DataFrame, hmm.GaussianHMM]:
    """Fit a Gaussian HMM and label regimes by inflation level.

    Economic intent:
        Regime labels reflect macro severity, with higher inflation
        corresponding to higher stress.

    Args:
        monthly: Monthly dataframe.
        config: HMM configuration.

    Returns:
        Tuple of (monthly dataframe with regimes, fitted model).
    """
    X = monthly[list(config.features)].values
    X_scaled = (X - X.mean(axis=0)) / X.std(axis=0)

    model = hmm.GaussianHMM(
        n_components=config.n_states,
        covariance_type=config.covariance_type,
        n_iter=config.n_iter,
        random_state=config.random_state,
    )
    model.fit(X_scaled)
    states = model.predict(X_scaled)

    result = monthly.copy()
    result["regime"] = states

    state_inflation = {
        s: result[result["regime"] == s]["ncpi_yoy_pct"].mean() for s in range(config.n_states)
    }
    sorted_states = sorted(state_inflation.keys(), key=lambda x: state_inflation[x])
    state_labels = {
        sorted_states[0]: "CALM",
        sorted_states[1]: "STRESS",
        sorted_states[2]: "CRISIS",
    }
    result["regime_label"] = result["regime"].map(state_labels)

    return result, model


def fit_zscore_baseline(monthly: pd.DataFrame, features: Iterable[str], threshold: float) -> pd.DataFrame:
    """Fit a z-score threshold baseline model.

    Economic intent:
        A transparent baseline ensures regime claims exceed simple
        threshold-based stress signals.

    Args:
        monthly: Monthly dataframe.
        features: Feature column names.
        threshold: Z-score threshold for STRESS.

    Returns:
        Monthly dataframe with z-score regime labels.
    """
    result = monthly.copy()
    for feat in features:
        result[f"{feat}_zscore"] = (result[feat] - result[feat].mean()) / result[feat].std()

    z_cols = [f"{feat}_zscore" for feat in features]
    max_abs = result[z_cols].abs().max(axis=1)

    result["zscore_regime"] = "CALM"
    result.loc[max_abs > threshold, "zscore_regime"] = "STRESS"
    result.loc[max_abs > threshold * 1.5, "zscore_regime"] = "CRISIS"

    return result


def calculate_metrics(
    hmm_results: Mapping[str, object],
    baseline_results: Mapping[str, object],
    lambda_missed: float,
    lambda_false: float,
) -> Mapping[str, Mapping[str, float]]:
    """Calculate hit/miss metrics for model and baseline."""
    metrics = {}

    for name, results in [("HMM", hmm_results), ("Z-Score", baseline_results)]:
        hits = int(results["hits"])
        misses = int(results["misses"])
        total = hits + misses
        hit_rate = hits / total if total else 0
        miss_rate = misses / total if total else 0
        cost = lambda_missed * misses + lambda_false * 0
        metrics[name] = {
            "hits": hits,
            "misses": misses,
            "total": total,
            "hit_rate": hit_rate,
            "miss_rate": miss_rate,
            "cost_weighted_score": cost,
        }

    return metrics


def analyze_transitions(monthly: pd.DataFrame, model_col: str = "regime_label") -> pd.DataFrame:
    """Extract transition points from regime labels."""
    transitions = []
    prev_regime = None

    for _, row in monthly.iterrows():
        current_regime = row[model_col]
        if prev_regime is not None and current_regime != prev_regime:
            transitions.append({"date": row["date"], "from": prev_regime, "to": current_regime})
        prev_regime = current_regime

    return pd.DataFrame(transitions)


def analyze_false_alarms(
    monthly: pd.DataFrame,
    events: Iterable[EventSpec],
    window_days: int,
    model_col: str = "regime_label",
) -> Mapping[str, float]:
    """Detect regime transitions not near known events."""
    transitions = analyze_transitions(monthly, model_col)
    if transitions.empty:
        return {"total_transitions": 0, "justified": 0, "false_alarms": 0, "false_alarm_rate": 0.0}

    event_dates = [event.date for event in events]
    false_alarms = 0
    justified = 0

    for _, row in transitions.iterrows():
        trans_date = row["date"]
        near_event = any(abs((trans_date - event_date).days) <= window_days for event_date in event_dates)
        if near_event:
            justified += 1
        else:
            false_alarms += 1

    total = len(transitions)
    return {
        "total_transitions": float(total),
        "justified": float(justified),
        "false_alarms": float(false_alarms),
        "false_alarm_rate": float(false_alarms / total if total else 0.0),
    }
