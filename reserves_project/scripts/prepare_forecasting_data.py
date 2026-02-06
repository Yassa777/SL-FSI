#!/usr/bin/env python3
"""Prepare model-ready datasets for ARIMA, VECM, MS-VAR, and MS-VECM forecasting."""

from __future__ import annotations

from datetime import datetime
import pandas as pd

from diagnostics_phases.io_utils import load_panel
from forecasting_prep import (
    build_arima_dataset,
    build_model_readiness,
    build_ms_var_dataset,
    build_vecm_datasets,
    save_dataframe,
    save_metadata,
)
from forecasting_prep.config import OUTPUT_DIR, TRAIN_END, VALID_END


def run_forecasting_prep(verbose: bool = True):
    if verbose:
        print("=" * 70)
        print("FORECASTING DATA PREPARATION")
        print("=" * 70)
        print(f"Started: {datetime.now()}")

    panel = load_panel()
    if verbose:
        print(f"Loaded panel: {panel.shape[0]} rows x {panel.shape[1]} columns")
        print(f"Date range: {panel.index.min().date()} to {panel.index.max().date()}")
        print(f"Splits: train <= {TRAIN_END.date()}, validation <= {VALID_END.date()}, test > {VALID_END.date()}")

    arima_df, arima_meta = build_arima_dataset(panel)
    vecm_levels_df, vecm_state_df, vecm_meta = build_vecm_datasets(panel)
    ms_var_raw_df, ms_var_scaled_df, ms_var_meta = build_ms_var_dataset(panel)

    metadata = {
        "timestamp": str(datetime.now()),
        "source": "data/merged/reserves_forecasting_panel.csv",
        "splits": {
            "train_end": str(TRAIN_END.date()),
            "validation_end": str(VALID_END.date()),
            "test_start": str((VALID_END + pd.offsets.MonthBegin(1)).date()),
        },
        "arima": arima_meta,
        "vecm": vecm_meta,
        "ms_var": ms_var_meta,
    }

    readiness_df = build_model_readiness(metadata)

    outputs = {
        "arima": save_dataframe(arima_df, "arima_prep_dataset.csv"),
        "vecm_levels": save_dataframe(vecm_levels_df, "vecm_levels_dataset.csv"),
        "vecm_state": save_dataframe(vecm_state_df, "ms_vecm_state_dataset.csv"),
        "ms_var_raw": save_dataframe(ms_var_raw_df, "ms_var_raw_dataset.csv"),
        "ms_var_scaled": save_dataframe(ms_var_scaled_df, "ms_var_scaled_dataset.csv"),
        "readiness": save_dataframe(readiness_df, "model_readiness_summary.csv"),
        "metadata": save_metadata(metadata),
    }

    if verbose:
        print("\nSaved artifacts:")
        for key, path in outputs.items():
            print(f"  - {key}: {path}")
        print(f"\nOutput directory: {OUTPUT_DIR}")
        print("=" * 70)
        print(f"Completed: {datetime.now()}")

    return outputs, metadata, readiness_df


if __name__ == "__main__":
    run_forecasting_prep(verbose=True)
