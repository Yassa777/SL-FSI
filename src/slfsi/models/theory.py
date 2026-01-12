"""Theory-based regime classification."""

from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import Any, Mapping, Tuple

import numpy as np
import pandas as pd

from slfsi.config.schema import ColumnSchema


@dataclass(frozen=True)
class Thresholds:
    """Thresholds for theory-based regimes."""

    crisis: float
    stress: float


@dataclass(frozen=True)
class TheoryConfig:
    """Configuration for theory-based regimes."""

    krugman: Thresholds
    reinhart_rogoff: Thresholds
    calvo: Thresholds
    use_net_import_cover: bool = True

    net_import_cover_col: str = "net_import_cover"
    import_cover_col: str = "import_cover_months"
    real_policy_rate_col: str = "real_policy_rate"
    isb_spread_col: str = "isb_spread_bps"
    isb_yield_col: str = "isb_yield"
    us_10y_yield_col: str = "us_10y_yield"


def _build_config(raw: Mapping[str, Any]) -> TheoryConfig:
    krugman_cfg = raw.get("krugman", {})
    reinhart_cfg = raw.get("reinhart_rogoff", {})
    calvo_cfg = raw.get("calvo", {})
    columns_cfg = raw.get("columns", {})

    return TheoryConfig(
        krugman=Thresholds(
            crisis=float(krugman_cfg.get("crisis", 2)),
            stress=float(krugman_cfg.get("stress", 4)),
        ),
        reinhart_rogoff=Thresholds(
            crisis=float(reinhart_cfg.get("crisis", -20)),
            stress=float(reinhart_cfg.get("stress", 0)),
        ),
        calvo=Thresholds(
            crisis=float(calvo_cfg.get("crisis", 2000)),
            stress=float(calvo_cfg.get("stress", 500)),
        ),
        use_net_import_cover=bool(krugman_cfg.get("use_net_import_cover", True)),
        net_import_cover_col=str(columns_cfg.get("net_import_cover", "net_import_cover")),
        import_cover_col=str(columns_cfg.get("import_cover_months", "import_cover_months")),
        real_policy_rate_col=str(columns_cfg.get("real_policy_rate", "real_policy_rate")),
        isb_spread_col=str(columns_cfg.get("isb_spread_bps", "isb_spread_bps")),
        isb_yield_col=str(columns_cfg.get("isb_yield", "isb_yield")),
        us_10y_yield_col=str(columns_cfg.get("us_10y_yield", "us_10y_yield")),
    )


def _classify_threshold(value: float, thresholds: Thresholds, *, higher_is_worse: bool) -> str:
    if np.isnan(value):
        return np.nan
    if higher_is_worse:
        if value > thresholds.crisis:
            return "CRISIS"
        if value > thresholds.stress:
            return "STRESS"
        return "CALM"
    if value < thresholds.crisis:
        return "CRISIS"
    if value < thresholds.stress:
        return "STRESS"
    return "CALM"


def _ensure_isb_spread(monthly: pd.DataFrame, config: TheoryConfig) -> pd.DataFrame:
    if config.isb_spread_col in monthly.columns:
        return monthly
    if config.isb_yield_col in monthly.columns and config.us_10y_yield_col in monthly.columns:
        monthly = monthly.copy()
        monthly[config.isb_spread_col] = (
            monthly[config.isb_yield_col] - monthly[config.us_10y_yield_col]
        ) * 100
    return monthly


def classify_theory_regimes(
    monthly: pd.DataFrame,
    schema: ColumnSchema,
    config: Mapping[str, Any],
) -> Tuple[pd.DataFrame, pd.DataFrame | None]:
    """Classify regimes based on theoretical thresholds.

    Economic intent:
        Rule-based regimes provide transparent benchmarks for stress
        classification alongside probabilistic HMM outputs.

    Args:
        monthly: Monthly panel dataframe.
        schema: Column schema.
        config: Theory configuration mapping.

    Returns:
        Tuple of (monthly_with_theory, comparison_df or None).
    """
    logger = logging.getLogger(__name__)
    cfg = _build_config(config)
    monthly = _ensure_isb_spread(monthly.copy(), cfg)

    def krugman(row: pd.Series) -> str:
        if cfg.use_net_import_cover and cfg.net_import_cover_col in row:
            cover = row.get(cfg.net_import_cover_col)
        else:
            cover = row.get(cfg.import_cover_col)
        return _classify_threshold(float(cover) if pd.notna(cover) else np.nan, cfg.krugman, higher_is_worse=False)

    def reinhart(row: pd.Series) -> str:
        value = row.get(cfg.real_policy_rate_col)
        return _classify_threshold(float(value) if pd.notna(value) else np.nan, cfg.reinhart_rogoff, higher_is_worse=False)

    def calvo(row: pd.Series) -> str:
        value = row.get(cfg.isb_spread_col)
        return _classify_threshold(float(value) if pd.notna(value) else np.nan, cfg.calvo, higher_is_worse=True)

    monthly["krugman_regime"] = monthly.apply(krugman, axis=1)
    monthly["rr_regime"] = monthly.apply(reinhart, axis=1)
    monthly["calvo_regime"] = monthly.apply(calvo, axis=1)

    def combine(row: pd.Series) -> str:
        regimes = [
            row.get("krugman_regime"),
            row.get("rr_regime"),
            row.get("calvo_regime"),
        ]
        regimes = [r for r in regimes if isinstance(r, str)]
        if not regimes:
            return np.nan
        if "CRISIS" in regimes:
            return "CRISIS"
        if "STRESS" in regimes:
            return "STRESS"
        return "CALM"

    monthly["theory_regime"] = monthly.apply(combine, axis=1)
    logger.info("Theory regimes computed (%s rows)", len(monthly))

    return monthly, None


def compare_with_hmm(
    theory_df: pd.DataFrame,
    hmm_df: pd.DataFrame,
    schema: ColumnSchema,
) -> pd.DataFrame:
    comparison = theory_df.merge(
        hmm_df[[schema.date, schema.regime_realtime, schema.p_calm, schema.p_stress, schema.p_crisis]],
        on=schema.date,
        how="inner",
    )
    comparison["agreement"] = comparison["theory_regime"] == comparison[schema.regime_realtime]
    return comparison
