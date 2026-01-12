"""Shared HMM fitting utilities."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable, Mapping, Tuple

import numpy as np
import pandas as pd
from hmmlearn import hmm

from slfsi.config.schema import ColumnSchema


@dataclass(frozen=True)
class HMMModelConfig:
    """Configuration for HMM fitting."""

    features: Tuple[str, ...]
    n_states: int
    covariance_type: str
    n_iter: int
    random_state: int
    label_feature: str = "ncpi_yoy_pct"


def prepare_monthly_features(
    daily: pd.DataFrame,
    features: Iterable[str],
    date_col: str,
    *,
    method: str = "first",
    interpolate: str | None = "linear",
    fill_edges: bool = True,
) -> pd.DataFrame:
    """Aggregate daily panel to monthly and optionally interpolate gaps.

    Economic intent:
        Monthly aggregation preserves macro structure while allowing
        consistent HMM input series across regimes.

    Args:
        daily: Daily panel dataframe.
        features: Feature columns to retain.
        date_col: Date column name.
        method: Aggregation method ("first", "last", "mean").
        interpolate: Pandas interpolation method or None.
        fill_edges: Whether to fill leading/trailing NaNs after interpolation.

    Returns:
        Monthly dataframe containing date and feature columns.
    """
    daily = daily.copy()
    daily["year_month"] = daily[date_col].dt.to_period("M")
    cols = list(features) + [date_col]

    if method == "last":
        monthly = daily.groupby("year_month")[cols].last().reset_index(drop=True)
    elif method == "mean":
        monthly = daily.groupby("year_month")[cols].mean(numeric_only=True).reset_index(drop=True)
    else:
        monthly = daily.groupby("year_month")[cols].first().reset_index(drop=True)

    if interpolate:
        for feat in features:
            if feat in monthly.columns:
                monthly[feat] = monthly[feat].interpolate(method=interpolate)
                if fill_edges:
                    monthly[feat] = monthly[feat].bfill().ffill()

    return monthly


def _standardize_matrix(matrix: np.ndarray) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    mean = np.nanmean(matrix, axis=0)
    std = np.nanstd(matrix, axis=0)
    std_safe = np.where(std == 0, 1.0, std)
    scaled = (matrix - mean) / std_safe
    return scaled, mean, std_safe


def fit_hmm_with_probs(
    monthly: pd.DataFrame,
    config: HMMModelConfig,
    schema: ColumnSchema,
) -> tuple[pd.DataFrame, hmm.GaussianHMM, Mapping[int, str]]:
    """Fit a Gaussian HMM and return regime probabilities.

    Economic intent:
        Probabilistic regimes expose stress intensity rather than relying
        solely on discrete regime labels.

    Args:
        monthly: Monthly panel with required features.
        config: HMM model configuration.
        schema: Column schema for output naming.

    Returns:
        Tuple of (results dataframe, fitted model, state label mapping).
    """
    data = monthly.dropna(subset=list(config.features)).copy()
    X = data[list(config.features)].values
    X_scaled, _, _ = _standardize_matrix(X)

    model = hmm.GaussianHMM(
        n_components=config.n_states,
        covariance_type=config.covariance_type,
        n_iter=config.n_iter,
        random_state=config.random_state,
    )
    model.fit(X_scaled)

    probs = model.predict_proba(X_scaled)
    states = probs.argmax(axis=1)
    data[schema.regime] = states

    label_feature = config.label_feature
    if label_feature not in data.columns:
        label_feature = schema.ncpi_yoy_pct

    state_means = {
        s: data[data[schema.regime] == s][label_feature].mean() for s in range(config.n_states)
    }
    sorted_states = sorted(state_means.keys(), key=lambda x: state_means[x])
    if config.n_states == 3:
        state_labels = {
            sorted_states[0]: "CALM",
            sorted_states[1]: "STRESS",
            sorted_states[2]: "CRISIS",
        }
    else:
        state_labels = {sorted_states[0]: "CALM", sorted_states[-1]: "CRISIS"}
        for idx in sorted_states[1:-1]:
            state_labels[idx] = "STRESS"

    data[schema.regime_label] = data[schema.regime].map(state_labels)
    data[schema.confidence] = probs.max(axis=1)

    for state_idx in sorted_states:
        label = state_labels[state_idx].lower()
        col = f"p_{label}"
        data[col] = probs[:, state_idx]

    return data, model, state_labels
