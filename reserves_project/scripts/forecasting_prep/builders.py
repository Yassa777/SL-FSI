"""Builders for model-specific forecasting datasets."""

from __future__ import annotations

import warnings
from typing import Any

import numpy as np
import pandas as pd
from statsmodels.tsa.vector_ar.vecm import coint_johansen

from .config import (
    ARIMA_EXOG_VARS,
    DIAG_DIR,
    MIN_OBS_MS,
    MIN_OBS_VECM,
    MS_VAR_SYSTEM_VARS,
    TARGET_VAR,
    TRAIN_END,
    VALID_END,
    VECM_SYSTEM_VARS,
)


def add_split_labels(df: pd.DataFrame) -> pd.DataFrame:
    out = df.copy()
    idx = pd.to_datetime(out.index)
    split = np.where(idx <= TRAIN_END, "train", np.where(idx <= VALID_END, "validation", "test"))
    out["split"] = split
    return out


def load_integration_summary() -> pd.DataFrame | None:
    path = DIAG_DIR / "integration_summary.csv"
    if not path.exists():
        return None
    return pd.read_csv(path)


def load_johansen_summary() -> pd.DataFrame | None:
    path = DIAG_DIR / "johansen_summary.csv"
    if not path.exists():
        return None
    return pd.read_csv(path)


def build_arima_dataset(panel: pd.DataFrame) -> tuple[pd.DataFrame, dict[str, Any]]:
    cols = [TARGET_VAR] + [c for c in ARIMA_EXOG_VARS if c in panel.columns]
    ds = panel[cols].dropna(subset=[TARGET_VAR]).copy()

    safe_target = ds[TARGET_VAR].where(ds[TARGET_VAR] > 0)
    ds["target_diff1"] = ds[TARGET_VAR].diff()
    ds["target_log"] = np.log(safe_target)
    ds["target_log_diff1"] = ds["target_log"].diff()
    ds["target_pct_change"] = ds[TARGET_VAR].pct_change() * 100.0
    ds = add_split_labels(ds)

    stats = {
        "rows": int(len(ds)),
        "train_rows": int((ds["split"] == "train").sum()),
        "validation_rows": int((ds["split"] == "validation").sum()),
        "test_rows": int((ds["split"] == "test").sum()),
        "d_recommendation": 1,
        "arima_exog_vars": [c for c in cols if c != TARGET_VAR],
    }
    return ds.reset_index().rename(columns={"index": "date"}), stats


def _parse_johansen_k_diff(summary: pd.DataFrame | None) -> int:
    if summary is None or summary.empty:
        return 2
    if "k_ar_diff" not in summary.columns:
        return 2
    try:
        return max(1, int(summary["k_ar_diff"].iloc[0]))
    except Exception:
        return 2


def _compute_ect(levels: pd.DataFrame, k_ar_diff: int) -> tuple[pd.Series | None, dict[str, Any]]:
    if len(levels) < MIN_OBS_VECM:
        return None, {"error": "Insufficient observations for Johansen vector"}

    try:
        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            joh = coint_johansen(levels, det_order=0, k_ar_diff=k_ar_diff)

        beta = np.asarray(joh.evec[:, 0], dtype=float)
        target_coeff = beta[0] if not np.isclose(beta[0], 0.0) else 1.0
        beta_norm = beta / target_coeff
        ect = pd.Series(levels.values @ beta_norm, index=levels.index, name="ect")

        meta = {
            "cointegration_vector": beta_norm.tolist(),
            "k_ar_diff": int(k_ar_diff),
            "trace_stats": [float(v) for v in joh.lr1],
            "trace_cv_95": [float(v) for v in joh.cvt[:, 1]],
        }
        return ect, meta
    except Exception as exc:
        return None, {"error": str(exc), "k_ar_diff": int(k_ar_diff)}


def build_vecm_datasets(panel: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame, dict[str, Any]]:
    vars_vecm = [c for c in VECM_SYSTEM_VARS if c in panel.columns]
    levels = panel[vars_vecm].dropna().copy()
    levels = add_split_labels(levels)

    joh_summary = load_johansen_summary()
    k_ar_diff = _parse_johansen_k_diff(joh_summary)
    ect, ect_meta = _compute_ect(levels[vars_vecm], k_ar_diff=k_ar_diff)

    diffs = levels[vars_vecm].diff()
    vecm_state = diffs.add_prefix("d_")
    if ect is not None:
        vecm_state["ect_lag1"] = ect.shift(1)
    vecm_state["split"] = levels["split"]
    vecm_state = vecm_state.dropna()

    meta = {
        "variables": vars_vecm,
        "rows_levels": int(len(levels)),
        "rows_state": int(len(vecm_state)),
        "suitable_for_vecm": bool(len(levels) >= MIN_OBS_VECM),
        "ect_metadata": ect_meta,
    }

    levels_out = levels.reset_index().rename(columns={"index": "date"})
    state_out = vecm_state.reset_index().rename(columns={"index": "date"})
    return levels_out, state_out, meta


def build_ms_var_dataset(panel: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame, dict[str, Any]]:
    vars_ms = [c for c in MS_VAR_SYSTEM_VARS if c in panel.columns]
    raw = panel[vars_ms].dropna().diff().dropna().copy()
    raw = add_split_labels(raw)

    train_mask = raw["split"] == "train"
    train_stats = raw.loc[train_mask, vars_ms].agg(["mean", "std"])

    scaled = raw.copy()
    for col in vars_ms:
        mean = train_stats.loc["mean", col]
        std = train_stats.loc["std", col]
        safe_std = std if (std is not None and std > 1e-12) else 1.0
        scaled[col] = (raw[col] - mean) / safe_std

    # Regime helper features (not required by model but useful for initialization/checks)
    if f"{TARGET_VAR}" in vars_ms:
        vol = raw[TARGET_VAR].rolling(6).std()
        thr = float(vol[train_mask].quantile(0.75)) if train_mask.any() else float(vol.quantile(0.75))
        scaled["regime_init_high_vol"] = (vol > thr).astype(int)
    else:
        scaled["regime_init_high_vol"] = 0

    raw_out = raw.reset_index().rename(columns={"index": "date"})
    scaled_out = scaled.reset_index().rename(columns={"index": "date"})

    meta = {
        "variables": vars_ms,
        "rows": int(len(raw)),
        "suitable_for_ms_var": bool(len(raw) >= MIN_OBS_MS),
        "standardized_on": "train_split",
    }
    return raw_out, scaled_out, meta


def build_model_readiness(metadata: dict[str, Any]) -> pd.DataFrame:
    rows = [
        {
            "model": "ARIMA",
            "ready": True,
            "rows": metadata["arima"]["rows"],
            "note": "Univariate stationary transforms prepared",
        },
        {
            "model": "VECM",
            "ready": metadata["vecm"].get("suitable_for_vecm", False),
            "rows": metadata["vecm"].get("rows_levels", 0),
            "note": "Level system + ECT state prepared",
        },
        {
            "model": "MS-VAR",
            "ready": metadata["ms_var"].get("suitable_for_ms_var", False),
            "rows": metadata["ms_var"].get("rows", 0),
            "note": "Differenced standardized system prepared",
        },
        {
            "model": "MS-VECM",
            "ready": metadata["vecm"].get("suitable_for_vecm", False)
            and metadata["ms_var"].get("suitable_for_ms_var", False),
            "rows": metadata["vecm"].get("rows_state", 0),
            "note": "ECT-augmented state prepared for regime switching",
        },
    ]
    return pd.DataFrame(rows)
