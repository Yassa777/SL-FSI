"""Combine FSI and HMM regime probabilities."""

from __future__ import annotations

from dataclasses import dataclass

import pandas as pd

from slfsi.config.schema import ColumnSchema


@dataclass(frozen=True)
class CombineConfig:
    """Configuration for combined FSI-HMM score."""

    alpha: float = 0.5
    stress_threshold: float = 0.5
    crisis_threshold: float = 0.7
    fsi_threshold: float = 1.0
    hmm_threshold: float = 0.5


def combine_fsi_hmm(
    fsi_df: pd.DataFrame,
    hmm_df: pd.DataFrame,
    schema: ColumnSchema,
    config: CombineConfig,
    *,
    fsi_col: str = "fsi_variance_equal",
) -> pd.DataFrame:
    """Combine FSI and HMM signals into a composite score."""
    merged = pd.merge(
        fsi_df[[schema.date, fsi_col]],
        hmm_df[[schema.date, "p_calm", "p_stress", "p_crisis"]],
        on=schema.date,
        how="inner",
    )

    fsi_mean = merged[fsi_col].mean()
    fsi_std = merged[fsi_col].std()
    merged["fsi_std"] = (merged[fsi_col] - fsi_mean) / fsi_std

    merged["hmm_stress_prob"] = merged["p_stress"] + merged["p_crisis"]
    merged["combined_stress"] = config.alpha * merged["fsi_std"] + (
        1 - config.alpha
    ) * merged["hmm_stress_prob"]

    comb_min = merged["combined_stress"].min()
    comb_max = merged["combined_stress"].max()
    denom = comb_max - comb_min
    if denom == 0:
        merged["combined_stress_norm"] = 0.0
    else:
        merged["combined_stress_norm"] = (merged["combined_stress"] - comb_min) / denom

    merged["early_warning"] = (merged["fsi_std"] > config.fsi_threshold) & (
        merged["p_calm"] > config.hmm_threshold
    )
    merged["possible_false_alarm"] = (merged["p_crisis"] > config.hmm_threshold) & (
        merged["fsi_std"] < 0.5
    )
    merged["agreement"] = ~(merged["early_warning"] | merged["possible_false_alarm"])

    return merged
