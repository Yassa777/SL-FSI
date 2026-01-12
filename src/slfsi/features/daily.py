"""Daily feature engineering for SL-FSI."""

from __future__ import annotations

import numpy as np
import pandas as pd

from slfsi.config.schema import ColumnSchema


def compute_daily_features(
    daily: pd.DataFrame,
    schema: ColumnSchema,
    vol_window: int,
    vol_min_periods: int,
) -> pd.DataFrame:
    """Compute daily market stress features.

    Economic intent:
        Daily returns and volatility capture fast-moving market stress, which
        often precedes slower-moving macro deterioration.

    Args:
        daily: Daily panel with raw market series.
        schema: Canonical column schema.
        vol_window: Rolling window size for volatility.
        vol_min_periods: Minimum observations for rolling volatility.

    Returns:
        Daily dataframe with derived features.
    """
    daily = daily.copy()

    if schema.usd_lkr in daily.columns:
        daily[schema.r_fx] = np.log(daily[schema.usd_lkr] / daily[schema.usd_lkr].shift(1))
        daily[schema.vol_fx_20d] = (
            daily[schema.r_fx].rolling(vol_window, min_periods=vol_min_periods).std()
        )

    if schema.aspi in daily.columns:
        daily[schema.r_eq] = np.log(daily[schema.aspi] / daily[schema.aspi].shift(1))
        daily[schema.vol_eq_20d] = (
            daily[schema.r_eq].rolling(vol_window, min_periods=vol_min_periods).std()
        )

    if schema.r_eq in daily.columns and schema.r_fx in daily.columns:
        daily[schema.r_eq_real] = daily[schema.r_eq] - daily[schema.r_fx]

    if (
        schema.gold_lkr in daily.columns
        and schema.gold_usd in daily.columns
        and schema.usd_lkr in daily.columns
    ):
        daily[schema.implied_fx] = daily[schema.gold_lkr] / daily[schema.gold_usd]
        daily[schema.gold_premium_pct] = (
            daily[schema.implied_fx] / daily[schema.usd_lkr] - 1
        ) * 100

    if schema.equity_turnover in daily.columns and schema.market_cap in daily.columns:
        daily[schema.turnover_ratio] = daily[schema.equity_turnover] / daily[schema.market_cap]

    if schema.isb_yield in daily.columns and schema.us_10y_yield in daily.columns:
        daily[schema.embi_spread_approx] = (
            daily[schema.isb_yield] - daily[schema.us_10y_yield]
        ) * 100

    slope_created = False
    if schema.tbond_yield in daily.columns and schema.tbill_primary in daily.columns:
        daily[schema.yield_curve_slope] = daily[schema.tbond_yield] - daily[schema.tbill_primary]
        slope_created = True
    elif schema.isb_yield in daily.columns and schema.tbill_primary in daily.columns:
        daily[schema.yield_curve_slope] = daily[schema.isb_yield] - daily[schema.tbill_primary]
        slope_created = True
    elif schema.isb_yield in daily.columns and schema.policy_ceiling in daily.columns:
        daily[schema.yield_curve_slope] = daily[schema.isb_yield] - daily[schema.policy_ceiling]
        slope_created = True

    if not slope_created and schema.yield_curve_slope in daily.columns:
        daily = daily.drop(columns=[schema.yield_curve_slope])

    return daily


def _safe_slope(series: pd.Series) -> float:
    values = series.dropna().values
    if len(values) < 3:
        return float("nan")
    return float(np.polyfit(range(len(values)), values, 1)[0])


def compute_post_upsample_features(daily: pd.DataFrame, schema: ColumnSchema) -> pd.DataFrame:
    """Compute features that rely on upsampled macro series.

    Economic intent:
        Interbank spreads and real rates combine market and policy signals,
        which require consistent macro inputs at the daily frequency.

    Args:
        daily: Daily dataframe with upsampled macro series.
        schema: Canonical column schema.

    Returns:
        Daily dataframe with post-upsampling features.
    """
    daily = daily.copy()

    if schema.awcmr in daily.columns and schema.policy_ceiling in daily.columns:
        daily[schema.interbank_spread] = daily[schema.awcmr] - daily[schema.policy_ceiling]

    if schema.policy_ceiling in daily.columns and schema.ncpi_yoy_pct in daily.columns:
        daily[schema.real_policy_rate] = (
            daily[schema.policy_ceiling] - daily[schema.ncpi_yoy_pct]
        )

    if schema.gross_reserves_usd_m in daily.columns:
        daily[schema.reserve_slope_3m] = (
            daily[schema.gross_reserves_usd_m]
            .rolling(90, min_periods=30)
            .apply(_safe_slope, raw=False)
        )

    return daily
