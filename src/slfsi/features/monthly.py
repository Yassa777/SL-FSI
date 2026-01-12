"""Monthly feature engineering for SL-FSI."""

from __future__ import annotations

import pandas as pd

from slfsi.config.schema import ColumnSchema


def compute_monthly_features(
    monthly: pd.DataFrame,
    schema: ColumnSchema,
    monthly_imports_usd_m: float,
    pboc_swap_usd_m: float,
    pboc_swap_start: pd.Timestamp,
) -> pd.DataFrame:
    """Compute monthly macro stress features.

    Economic intent:
        Monthly reserve cover and real rates reflect structural stress that
        accumulates more slowly than daily market volatility.

    Args:
        monthly: Monthly panel with macro series.
        schema: Canonical column schema.
        monthly_imports_usd_m: Assumed monthly import bill for cover ratios.
        pboc_swap_usd_m: Swap amount to exclude from usable reserves.
        pboc_swap_start: Start date for swap adjustment.

    Returns:
        Monthly dataframe with derived features.
    """
    monthly = monthly.copy()

    if schema.gross_reserves_usd_m in monthly.columns:
        monthly[schema.import_cover_months] = (
            monthly[schema.gross_reserves_usd_m] / monthly_imports_usd_m
        )
        monthly[schema.net_usable_reserves_usd_m] = monthly[schema.gross_reserves_usd_m]
        mask = monthly[schema.date] >= pboc_swap_start
        monthly.loc[mask, schema.net_usable_reserves_usd_m] = (
            monthly.loc[mask, schema.gross_reserves_usd_m] - pboc_swap_usd_m
        )
        monthly[schema.net_import_cover_months] = (
            monthly[schema.net_usable_reserves_usd_m] / monthly_imports_usd_m
        )

    if schema.policy_ceiling in monthly.columns and schema.ncpi_yoy_pct in monthly.columns:
        monthly[schema.real_policy_rate] = (
            monthly[schema.policy_ceiling] - monthly[schema.ncpi_yoy_pct]
        )

    return monthly
