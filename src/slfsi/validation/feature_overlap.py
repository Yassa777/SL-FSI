"""Feature overlap analysis for HMM inputs."""

from __future__ import annotations

import logging
from itertools import combinations
from typing import Any, Mapping

import numpy as np
import pandas as pd
from hmmlearn import hmm

from slfsi.config.schema import ColumnSchema


def _coverage_stats(df: pd.DataFrame, date_col: str) -> pd.DataFrame:
    total = len(df)
    rows = []
    for col in df.columns:
        if col == date_col:
            continue
        if not pd.api.types.is_numeric_dtype(df[col]):
            continue
        valid = int(df[col].notna().sum())
        pct = (valid / total * 100) if total else 0
        rows.append({"feature": col, "valid_days": valid, "coverage_pct": pct})
    coverage = pd.DataFrame(rows)
    return coverage.sort_values("coverage_pct", ascending=False)


def _combo_overlap(df: pd.DataFrame, features: tuple[str, ...]) -> tuple[int, float]:
    subset = df[list(features)].dropna()
    days = len(subset)
    pct = days / len(df) * 100 if len(df) else 0
    return days, pct


def _test_hmm(
    df: pd.DataFrame, features: tuple[str, ...], n_states: int, n_iter: int, covariance_type: str
) -> Mapping[str, Any]:
    data = df[[*features, "date"]].dropna()
    X = data[list(features)].values
    X_mean = X.mean(axis=0)
    X_std = X.std(axis=0)
    X_scaled = (X - X_mean) / (X_std + 1e-8)

    model = hmm.GaussianHMM(
        n_components=n_states,
        covariance_type=covariance_type,
        n_iter=n_iter,
        random_state=42,
    )
    model.fit(X_scaled)
    states = model.predict(X_scaled)
    log_likelihood = model.score(X_scaled)

    state_counts = np.bincount(states, minlength=n_states)
    state_pcts = state_counts / len(states) * 100
    degenerate = int(np.sum(state_pcts < 5))

    k_params = n_states * len(features) + n_states * n_states
    aic = -2 * log_likelihood + 2 * k_params

    return {
        "n_observations": len(data),
        "log_likelihood": float(log_likelihood),
        "aic": float(aic),
        "state_distribution": state_pcts,
        "degenerate_states": degenerate,
        "converged": bool(model.monitor_.converged),
        "dates": data["date"].values,
        "states": states,
    }


def run_feature_overlap(
    daily: pd.DataFrame,
    config: Mapping[str, Any],
    schema: ColumnSchema,
) -> Mapping[str, Any]:
    """Analyze feature overlap and viable HMM combinations.

    Economic intent:
        Ensures HMM feature sets have sufficient overlapping coverage in
        the crisis window, avoiding spurious regime inference.

    Args:
        daily: Daily panel dataframe.
        config: Feature overlap configuration mapping.
        schema: Column schema.

    Returns:
        Dictionary of coverage, combinations, and HMM test results.
    """
    logger = logging.getLogger(__name__)
    start = pd.Timestamp(config.get("start", daily[schema.date].min()))
    end = pd.Timestamp(config.get("end", daily[schema.date].max()))
    analysis = daily[(daily[schema.date] >= start) & (daily[schema.date] <= end)].copy()

    coverage = _coverage_stats(analysis, schema.date)
    min_feature_pct = float(config.get("min_feature_coverage_pct", 30))
    usable = coverage[coverage["coverage_pct"] > min_feature_pct]["feature"].tolist()

    overlap_matrix = pd.DataFrame(index=usable, columns=usable, dtype=float)
    for feat1 in usable:
        for feat2 in usable:
            days, pct = _combo_overlap(analysis, (feat1, feat2))
            overlap_matrix.loc[feat1, feat2] = pct

    min_overlap_pct = float(config.get("min_overlap_pct", 50))
    min_overlap_days = int(config.get("min_overlap_days", 500))
    min_features = int(config.get("min_features", 3))
    max_features = int(config.get("max_features", min_features + 2))
    high_coverage_pct = float(config.get("high_coverage_pct", 50))
    high_coverage = coverage[coverage["coverage_pct"] >= high_coverage_pct]["feature"].tolist()

    viable = []
    for size in range(min_features, max_features + 1):
        for combo in combinations(high_coverage, size):
            days, pct = _combo_overlap(analysis, combo)
            if pct >= min_overlap_pct and days >= min_overlap_days:
                viable.append(
                    {
                        "features": combo,
                        "n_features": size,
                        "overlap_days": days,
                        "overlap_pct": pct,
                    }
                )

    viable = sorted(viable, key=lambda x: (-x["overlap_pct"], -x["n_features"]))

    test_cfg = config.get("hmm_test", {})
    hmm_results = []
    if test_cfg.get("enabled", True):
        n_states_list = test_cfg.get("n_states", [2, 3])
        n_iter = int(test_cfg.get("n_iter", 100))
        cov_type = str(test_cfg.get("covariance_type", "full"))
        for combo in viable[:5]:
            for n_states in n_states_list:
                try:
                    result = _test_hmm(analysis, combo["features"], n_states, n_iter, cov_type)
                except Exception as exc:
                    logger.warning("HMM test failed for %s: %s", combo["features"], exc)
                    continue
                result["features"] = combo["features"]
                result["n_states"] = n_states
                result["overlap_pct"] = combo["overlap_pct"]
                hmm_results.append(result)

    good_results = [
        res for res in hmm_results if res["converged"] and res["degenerate_states"] == 0
    ]
    good_results = sorted(good_results, key=lambda x: x["aic"])

    recommendation = good_results[0] if good_results else None
    if recommendation:
        logger.info(
            "Recommended features: %s (states=%s, overlap=%.1f%%)",
            recommendation["features"],
            recommendation["n_states"],
            recommendation["overlap_pct"],
        )

    category_summary = {}
    for category, feats in config.get("categories", {}).items():
        available = [feat for feat in feats if feat in coverage["feature"].values]
        if not available:
            continue
        avg = float(coverage[coverage["feature"].isin(available)]["coverage_pct"].mean())
        usable_feats = [
            feat
            for feat in available
            if coverage.loc[coverage["feature"] == feat, "coverage_pct"].iloc[0] > 50
        ]
        category_summary[category] = {"avg_coverage_pct": avg, "usable_features": usable_feats}

    return {
        "coverage": coverage,
        "overlap_pct": overlap_matrix,
        "viable_combos": viable,
        "hmm_results": hmm_results,
        "recommendation": recommendation,
        "category_summary": category_summary,
    }
