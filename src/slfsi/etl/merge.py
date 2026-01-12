"""Merge and feature logic for SL-FSI panels."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, Iterable, Mapping, Optional, Tuple

import pandas as pd

from slfsi.config.schema import ColumnSchema
from slfsi.features.daily import compute_daily_features, compute_post_upsample_features
from slfsi.features.monthly import compute_monthly_features


@dataclass(frozen=True)
class DateRange:
    """Inclusive date range for panel construction."""

    start: pd.Timestamp
    end: pd.Timestamp


def build_spine(date_range: DateRange, freq: str, date_col: str) -> pd.DataFrame:
    """Create a continuous date spine for merges.

    Economic intent:
        A continuous calendar spine ensures that stress indicators align
        across markets and macro series without hidden gaps.

    Args:
        date_range: Date range for the spine.
        freq: Pandas frequency string.
        date_col: Name of the date column.

    Returns:
        DataFrame with a single date column.
    """
    dates = pd.date_range(start=date_range.start, end=date_range.end, freq=freq)
    return pd.DataFrame({date_col: dates})


def merge_sources(
    spine: pd.DataFrame,
    sources: Iterable[pd.DataFrame],
    date_col: str,
) -> pd.DataFrame:
    """Merge multiple sources onto a shared date spine.

    Economic intent:
        Aligning sources on a shared calendar enables apples-to-apples
        comparisons of market stress and macro conditions.

    Args:
        spine: Base date spine.
        sources: Dataframes to merge.
        date_col: Name of the date column.

    Returns:
        Merged dataframe.
    """
    merged = spine.copy()
    for df in sources:
        if df is None or date_col not in df.columns:
            continue
        overlap = [c for c in df.columns if c != date_col and c in merged.columns]
        if overlap:
            df = df.rename(columns={c: f"{c}__new" for c in overlap})
        merged = merged.merge(df, on=date_col, how="left")
        for col in overlap:
            new_col = f"{col}__new"
            if new_col in merged.columns:
                merged[col] = merged[col].combine_first(merged[new_col])
                merged = merged.drop(columns=[new_col])
    return merged


def apply_overlay(
    base: pd.DataFrame,
    overlay: pd.DataFrame,
    date_col: str,
    value_col: str,
    upsample: bool = False,
) -> pd.DataFrame:
    """Overlay historical data to extend series coverage.

    Economic intent:
        Historical overlays preserve long-run macro context while keeping
        higher-frequency observations intact for recent stress episodes.

    Args:
        base: Base dataframe containing the target column.
        overlay: Historical overlay dataframe.
        date_col: Name of the date column.
        value_col: Column to overlay.
        upsample: Whether to forward-fill overlay values to daily frequency.

    Returns:
        DataFrame with overlay applied.
    """
    if overlay is None or value_col not in overlay.columns:
        return base

    base = base.copy()
    overlay = _restrict_overlay_to_history(base, overlay, date_col, value_col)
    base_series = base.set_index(date_col)[value_col] if value_col in base.columns else None
    overlay_series = overlay.set_index(date_col)[value_col]

    if upsample:
        overlay_series = overlay_series.resample("D").ffill()

    if base_series is None:
        base[value_col] = base.set_index(date_col).index.map(overlay_series)
        return base

    combined = base_series.combine_first(overlay_series)
    base[value_col] = combined.values
    return base


def _restrict_overlay_to_history(
    base: pd.DataFrame,
    overlay: pd.DataFrame,
    date_col: str,
    value_col: str,
) -> pd.DataFrame:
    """Limit overlays to dates before the first observed base value.

    Economic intent:
        Historical overlays should only extend coverage backward, not replace
        newer compiled data in the core sample.

    Args:
        base: Base dataframe with the target column (if present).
        overlay: Overlay dataframe to restrict.
        date_col: Name of the date column.
        value_col: Target column name.

    Returns:
        Overlay dataframe filtered to pre-sample dates when applicable.
    """
    if value_col not in base.columns or date_col not in overlay.columns:
        return overlay

    base_non_null = base[[date_col, value_col]].dropna()
    if base_non_null.empty:
        return overlay

    cutoff = base_non_null[date_col].min()
    return overlay[overlay[date_col] < cutoff]




def upsample_monthly_to_daily(
    monthly: pd.DataFrame,
    daily_spine: pd.DataFrame,
    date_col: str,
) -> pd.DataFrame:
    """Forward-fill monthly data onto a daily spine.

    Economic intent:
        Upsampling allows slow-moving macro series to be viewed alongside
        daily market stress metrics without implying higher-frequency noise.

    Args:
        monthly: Monthly dataframe.
        daily_spine: Daily date spine.
        date_col: Date column name.

    Returns:
        Daily dataframe containing monthly columns forward-filled.
    """
    monthly = monthly.copy()
    monthly = monthly.set_index(date_col).sort_index()
    daily = daily_spine.copy().set_index(date_col)
    upsampled = daily.join(monthly, how="left")
    upsampled = upsampled.ffill().reset_index()
    return upsampled




def aggregate_daily_to_monthly(
    daily: pd.DataFrame,
    date_col: str,
    agg_rules: Mapping[str, Iterable[str]],
) -> pd.DataFrame:
    """Aggregate daily data to monthly frequency.

    Economic intent:
        Aggregation provides consistent monthly measures for macro-regime
        modeling without losing daily volatility structure.

    Args:
        daily: Daily dataframe.
        date_col: Date column name.
        agg_rules: Mapping of aggregation method to column lists.

    Returns:
        Monthly dataframe.
    """
    daily_indexed = daily.set_index(date_col)
    rules: Dict[str, str] = {}
    for method, cols in agg_rules.items():
        for col in cols:
            if col in daily_indexed.columns:
                rules[col] = method

    monthly = daily_indexed.resample("M").agg(rules).reset_index()
    return monthly


def build_panels(
    daily_sources: Iterable[pd.DataFrame],
    monthly_sources: Iterable[pd.DataFrame],
    overlays: Iterable[Mapping[str, Any]],
    date_range: DateRange,
    schema: ColumnSchema,
    config: Mapping[str, Any],
) -> Tuple[pd.DataFrame, pd.DataFrame]:
    """Construct daily and monthly panels from source data.

    Economic intent:
        Produces harmonized daily and monthly panels for regime detection,
        respecting the distinction between market volatility and macro trend.

    Args:
        daily_sources: Iterable of daily dataframes.
        monthly_sources: Iterable of monthly dataframes.
        overlays: Historical overlay specifications.
        date_range: Date range for the panels.
        schema: Canonical column schema.
        config: ETL configuration dictionary.

    Returns:
        Tuple of (daily_panel, monthly_panel).
    """
    date_col = schema.date
    vol_config = config.get("volatility", {})
    vol_window = int(vol_config.get("window", 20))
    vol_min_periods = int(vol_config.get("min_periods", 10))

    monthly_imports = float(config.get("monthly_imports_usd_m", 1500))
    pboc = config.get("pboc_swap", {})
    pboc_amount = float(pboc.get("amount_usd_m", 1500))
    pboc_start = pd.Timestamp(pboc.get("start", "2021-03-01"))

    daily_spine = build_spine(date_range, "D", date_col)
    daily = merge_sources(daily_spine, daily_sources, date_col)

    for overlay in overlays:
        target = overlay.get("target")
        if not target or overlay.get("data") is None:
            continue
        if overlay.get("frequency", "monthly") == "daily":
            daily = apply_overlay(
                daily,
                overlay.get("data"),
                date_col,
                target,
                upsample=bool(overlay.get("upsample", False)),
            )

    daily = compute_daily_features(daily, schema, vol_window, vol_min_periods)

    monthly_spine = build_spine(date_range, "MS", date_col)
    monthly = merge_sources(monthly_spine, monthly_sources, date_col)

    for overlay in overlays:
        target = overlay.get("target")
        if not target or overlay.get("data") is None:
            continue
        if overlay.get("frequency", "monthly") != "daily":
            monthly = apply_overlay(
                monthly,
                overlay.get("data"),
                date_col,
                target,
                upsample=bool(overlay.get("upsample", False)),
            )

    monthly = compute_monthly_features(monthly, schema, monthly_imports, pboc_amount, pboc_start)
    monthly_for_upsample = monthly.copy()
    monthly_for_output = monthly.copy()
    monthly_for_output[date_col] = (
        monthly_for_output[date_col].dt.to_period("M").dt.to_timestamp("M")
    )

    monthly_up = upsample_monthly_to_daily(monthly_for_upsample, daily_spine, date_col)
    daily = daily.merge(monthly_up, on=date_col, how="left", suffixes=("", "__monthly"))
    for col in monthly_up.columns:
        if col == date_col:
            continue
        monthly_col = f"{col}__monthly"
        if monthly_col in daily.columns and col in daily.columns:
            daily[col] = daily[col].combine_first(daily[monthly_col])
            daily = daily.drop(columns=[monthly_col])

    daily = compute_post_upsample_features(daily, schema)

    agg_rules = config.get("aggregation", {})
    daily_monthly = aggregate_daily_to_monthly(daily, date_col, agg_rules)
    monthly = monthly_for_output.merge(daily_monthly, on=date_col, how="left", suffixes=("", "__daily"))
    for col in daily_monthly.columns:
        if col == date_col:
            continue
        daily_col = f"{col}__daily"
        if daily_col in monthly.columns and col in monthly.columns:
            monthly[col] = monthly[col].combine_first(monthly[daily_col])
            monthly = monthly.drop(columns=[daily_col])

    return daily, monthly
