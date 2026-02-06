"""I/O helpers for forecasting preparation artifacts."""

from __future__ import annotations

import json
from typing import Any

import pandas as pd

from .config import OUTPUT_DIR


def save_dataframe(df: pd.DataFrame, filename: str) -> str:
    path = OUTPUT_DIR / filename
    df.to_csv(path, index=False)
    return str(path)


def save_metadata(metadata: dict[str, Any], filename: str = "forecast_prep_metadata.json") -> str:
    path = OUTPUT_DIR / filename
    with open(path, "w") as f:
        json.dump(metadata, f, indent=2)
    return str(path)
