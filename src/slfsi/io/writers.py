"""Output helpers for SL-FSI pipelines."""

from __future__ import annotations

from pathlib import Path

import pandas as pd


def write_csv(df: pd.DataFrame, path: Path, *, index: bool = False) -> None:
    """Write a dataframe to CSV, creating parent directories.

    Economic intent:
        Ensures data artifacts land in consistent locations for reproducible
        stress analysis and downstream model validation.

    Args:
        df: Dataframe to write.
        path: Output CSV path.
        index: Whether to include the index column.
    """
    path.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(path, index=index)
