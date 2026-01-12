"""Cleaning utilities for SL-FSI datasets."""

from __future__ import annotations

from typing import Iterable

import pandas as pd


def coerce_numeric(df: pd.DataFrame, columns: Iterable[str]) -> pd.DataFrame:
    """Convert selected columns to numeric values.

    Economic intent:
        Many SL-FSI series are sourced from spreadsheets with mixed types.
        Coercing to numeric ensures macro and market indicators can be
        compared consistently without silent string contamination.

    Args:
        df: Input dataframe.
        columns: Columns to convert to numeric.

    Returns:
        DataFrame with converted columns.
    """
    df = df.copy()
    for col in columns:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors="coerce")
    return df


def ensure_datetime(df: pd.DataFrame, date_col: str) -> pd.DataFrame:
    """Ensure the date column is timezone-naive datetime.

    Economic intent:
        Aligning time indices is critical for regime timing and event alignment
        in stress analysis. This standardizes the temporal axis for merges.

    Args:
        df: Input dataframe.
        date_col: Name of the date column.

    Returns:
        DataFrame with normalized datetime column.
    """
    df = df.copy()
    if date_col in df.columns:
        df[date_col] = pd.to_datetime(df[date_col])
    return df
