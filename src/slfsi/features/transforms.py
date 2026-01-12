"""Shared feature transforms for SL-FSI."""

from __future__ import annotations

import numpy as np
import pandas as pd


def zscore(series: pd.Series) -> pd.Series:
    """Compute z-scores for a series.

    Economic intent:
        Standardizing indicators allows stress metrics to be compared across
        heterogeneous scales.
    """
    mean = series.mean()
    std = series.std()
    if std == 0 or pd.isna(std):
        return series * 0.0
    return (series - mean) / std


def winsorize(series: pd.Series, lower: float = 0.01, upper: float = 0.99) -> pd.Series:
    """Winsorize a series to limit outlier influence.

    Economic intent:
        Winsorization reduces the influence of extreme shocks that can
        dominate composite stress scores.
    """
    if series.empty:
        return series
    lower_q = series.quantile(lower)
    upper_q = series.quantile(upper)
    return series.clip(lower=lower_q, upper=upper_q)
