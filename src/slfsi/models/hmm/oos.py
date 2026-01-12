"""Out-of-sample HMM validation."""

from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import Any, Mapping

import numpy as np
import pandas as pd
from hmmlearn import hmm

from slfsi.config.schema import ColumnSchema
from slfsi.models.hmm.fit import HMMModelConfig


@dataclass(frozen=True)
class OOSResults:
    """Outputs for out-of-sample validation."""

    predictions: pd.DataFrame
    model_info: Mapping[str, Any]
    metrics: Mapping[str, Any]


def _truth_for_date(date: pd.Timestamp, windows: list[Mapping[str, str]]) -> str | None:
    for window in windows:
        start = pd.Timestamp(window["start"])
        end = pd.Timestamp(window["end"])
        if start <= date <= end:
            return str(window["regime"])
    return None


def run_oos(
    monthly: pd.DataFrame,
    model_config: HMMModelConfig,
    schema: ColumnSchema,
    config: Mapping[str, Any],
) -> OOSResults:
    """Run out-of-sample validation on a train/test split.

    Economic intent:
        Out-of-sample validation quantifies early warning performance
        without using future information in the training window.

    Args:
        monthly: Monthly panel dataframe.
        model_config: HMM model configuration.
        schema: Column schema.
        config: Out-of-sample configuration mapping.

    Returns:
        OOSResults containing predictions, model metadata, and metrics.
    """
    logger = logging.getLogger(__name__)
    try:
        from sklearn.preprocessing import StandardScaler
    except ImportError as exc:
        raise RuntimeError("scikit-learn is required for OOS validation") from exc

    train_start = pd.Timestamp(config.get("train_start"))
    train_end = pd.Timestamp(config.get("train_end"))
    test_start = pd.Timestamp(config.get("test_start"))
    test_end = pd.Timestamp(config.get("test_end"))

    if any(value is pd.NaT for value in [train_start, train_end, test_start, test_end]):
        raise ValueError("Train/test date range missing in OOS config")

    train_mask = (monthly[schema.date] >= train_start) & (monthly[schema.date] <= train_end)
    test_mask = (monthly[schema.date] >= test_start) & (monthly[schema.date] <= test_end)

    train = monthly[train_mask].dropna(subset=list(model_config.features)).copy()
    test = monthly[test_mask].dropna(subset=list(model_config.features)).copy()

    if train.empty or test.empty:
        raise ValueError("Insufficient data for OOS train/test split")

    X_train = train[list(model_config.features)].values
    scaler = StandardScaler()
    X_train_scaled = scaler.fit_transform(X_train)

    model = hmm.GaussianHMM(
        n_components=model_config.n_states,
        covariance_type=model_config.covariance_type,
        n_iter=model_config.n_iter,
        random_state=model_config.random_state,
    )
    model.fit(X_train_scaled)

    train_states = model.predict(X_train_scaled)
    train = train.copy()
    train[schema.regime] = train_states

    label_feature = model_config.label_feature
    if label_feature not in train.columns:
        label_feature = schema.ncpi_yoy_pct

    state_means = {
        s: train[train[schema.regime] == s][label_feature].mean()
        for s in range(model_config.n_states)
    }
    sorted_states = sorted(state_means.keys(), key=lambda x: state_means[x])
    state_labels = {
        sorted_states[0]: "CALM",
        sorted_states[1]: "STRESS",
        sorted_states[2]: "CRISIS",
    }

    X_test = test[list(model_config.features)].values
    X_test_scaled = scaler.transform(X_test)
    probs = model.predict_proba(X_test_scaled)
    states = probs.argmax(axis=1)

    results = test.copy()
    results["state"] = states
    results[schema.regime_label] = results["state"].map(state_labels)
    results[schema.confidence] = probs.max(axis=1)

    for state_idx in sorted_states:
        label = state_labels[state_idx].lower()
        results[f"p_{label}"] = probs[:, state_idx]

    results["year_month_str"] = results[schema.date].dt.strftime("%Y-%m")

    expected_events = config.get("expected_events", [])
    hits = 0
    total = 0
    event_rows = []
    for event in expected_events:
        date = pd.Timestamp(event["date"])
        expected = str(event["expected"])
        row = results[results[schema.date].dt.to_period("M") == date.to_period("M")]
        if row.empty:
            continue
        predicted = row.iloc[0][schema.regime_label]
        prob = row.iloc[0].get(f"p_{expected.lower()}", float("nan"))
        match = predicted == expected
        hits += 1 if match else 0
        total += 1
        event_rows.append(
            {
                "date": date,
                "event": event.get("label", ""),
                "expected": expected,
                "predicted": predicted,
                "p_expected": prob,
                "match": match,
            }
        )

    event_df = pd.DataFrame(event_rows)

    default_date = pd.Timestamp(config.get("default_date", "2022-04-12"))
    stress_mask = results[schema.regime_label].isin(["STRESS", "CRISIS"])
    first_stress_date = results.loc[stress_mask, schema.date].min()

    lead_months = None
    if pd.notna(first_stress_date):
        lead_months = int((default_date - first_stress_date).days / 30)

    calibration_cfg = config.get("calibration", {})
    thresholds = calibration_cfg.get("thresholds", [])
    truth_windows = calibration_cfg.get("truth_windows", [])
    calibration_rows = []
    for threshold in thresholds:
        high_conf = results[results[schema.confidence] >= float(threshold)]
        if high_conf.empty:
            continue
        correct = 0.0
        for _, row in high_conf.iterrows():
            truth = _truth_for_date(row[schema.date], truth_windows)
            if truth and row[schema.regime_label] == truth:
                correct += 1.0
            elif truth is None:
                correct += 0.5
        accuracy = correct / len(high_conf)
        calibration_rows.append(
            {"threshold": float(threshold), "n_predictions": len(high_conf), "accuracy": accuracy}
        )

    metrics = {
        "event_hits": hits,
        "event_total": total,
        "event_hit_rate": hits / total if total else 0.0,
        "lead_months": lead_months,
        "calibration": calibration_rows,
    }

    model_info = {
        "train_start": train_start.strftime("%Y-%m-%d"),
        "train_end": train_end.strftime("%Y-%m-%d"),
        "test_start": test_start.strftime("%Y-%m-%d"),
        "test_end": test_end.strftime("%Y-%m-%d"),
        "features": list(model_config.features),
        "n_states": model_config.n_states,
        "state_labels": state_labels,
        "scaler_mean": scaler.mean_.tolist(),
        "scaler_std": scaler.scale_.tolist(),
    }

    logger.info("OOS event hit rate: %.2f", metrics["event_hit_rate"])
    return OOSResults(predictions=results, model_info=model_info, metrics=metrics | {"events": event_df})
