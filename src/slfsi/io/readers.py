"""Input helpers for SL-FSI pipelines."""

from __future__ import annotations

from pathlib import Path
from typing import Any, Mapping

import pandas as pd


def read_csv(
    path: Path,
    *,
    date_col: str | None = None,
    dtype: Mapping[str, Any] | None = None,
) -> pd.DataFrame:
    """Read a CSV file with optional date parsing.

    Economic intent:
        Standardized parsing keeps external data aligned in time, preventing
        silent shifts in stress indicators caused by inconsistent date formats.

    Args:
        path: Path to the CSV file.
        date_col: Optional date column to parse.
        dtype: Optional dtype overrides for columns.

    Returns:
        Parsed dataframe.
    """
    if date_col:
        df = pd.read_csv(path, parse_dates=[date_col], dtype=dtype)
    else:
        df = pd.read_csv(path, dtype=dtype)
    return df
