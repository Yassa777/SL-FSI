"""Data quality checks for SL-FSI panels."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable, Mapping, Tuple

import pandas as pd


@dataclass(frozen=True)
class GapThresholds:
    """Thresholds for detecting critical data gaps."""

    min_coverage_pct: float
    max_consecutive_missing: int


@dataclass(frozen=True)
class QualitySummary:
    """Summary of data quality checks."""

    report: pd.DataFrame
    critical_failures: int


def _max_consecutive_missing(series: pd.Series) -> int:
    missing = series.isna().astype(int)
    if missing.empty:
        return 0
    groups = (missing != missing.shift()).cumsum()
    streaks = missing.groupby(groups).sum()
    return int(streaks.max()) if not streaks.empty else 0


def _evaluate_columns(
    df: pd.DataFrame,
    dataset_name: str,
    date_col: str,
    thresholds: GapThresholds,
    critical_columns: Iterable[str],
) -> pd.DataFrame:
    rows = []
    total = len(df)
    for col in df.columns:
        if col == date_col:
            continue
        non_null = df[col].notna().sum()
        coverage_pct = (non_null / total * 100) if total > 0 else 0
        max_gap = _max_consecutive_missing(df[col])
        is_critical = col in critical_columns

        status = "ok"
        if coverage_pct < thresholds.min_coverage_pct or max_gap > thresholds.max_consecutive_missing:
            status = "fail" if is_critical else "warn"

        rows.append(
            {
                "dataset": dataset_name,
                "column": col,
                "coverage_pct": round(coverage_pct, 2),
                "max_consecutive_missing": max_gap,
                "status": status,
                "critical": is_critical,
            }
        )
    return pd.DataFrame(rows)


def _filter_window(df: pd.DataFrame, date_col: str, start: pd.Timestamp, end: pd.Timestamp) -> pd.DataFrame:
    mask = (df[date_col] >= start) & (df[date_col] <= end)
    return df.loc[mask].copy()


def run_quality_checks(
    daily: pd.DataFrame,
    monthly: pd.DataFrame,
    config: Mapping[str, object],
    date_col: str = "date",
) -> QualitySummary:
    """Run critical data gap checks for daily and monthly panels.

    Economic intent:
        Regime detection is sensitive to missing data. These checks flag
        gaps that could distort early warning signals or regime timing.

    Args:
        daily: Daily panel dataframe.
        monthly: Monthly panel dataframe.
        config: Quality configuration dictionary.
        date_col: Date column name.

    Returns:
        QualitySummary with report dataframe and critical failure count.
    """
    daily_cfg = config.get("daily", {})
    monthly_cfg = config.get("monthly", {})

    daily_thresholds = GapThresholds(
        min_coverage_pct=float(daily_cfg.get("min_coverage_pct", 50)),
        max_consecutive_missing=int(daily_cfg.get("max_consecutive_missing", 30)),
    )
    monthly_thresholds = GapThresholds(
        min_coverage_pct=float(monthly_cfg.get("min_coverage_pct", 80)),
        max_consecutive_missing=int(monthly_cfg.get("max_consecutive_missing", 2)),
    )

    daily_critical = set(daily_cfg.get("critical_columns", []))
    monthly_critical = set(monthly_cfg.get("critical_columns", []))

    daily_report = _evaluate_columns(daily, "daily", date_col, daily_thresholds, daily_critical)
    monthly_report = _evaluate_columns(monthly, "monthly", date_col, monthly_thresholds, monthly_critical)

    crisis_cfg = config.get("crisis_window", {})
    crisis_reports = []
    if crisis_cfg:
        start = pd.Timestamp(crisis_cfg.get("start", daily[date_col].min()))
        end = pd.Timestamp(crisis_cfg.get("end", daily[date_col].max()))

        daily_window = _filter_window(daily, date_col, start, end)
        monthly_window = _filter_window(monthly, date_col, start, end)

        daily_window_thresholds = GapThresholds(
            min_coverage_pct=float(crisis_cfg.get("daily_min_coverage_pct", daily_thresholds.min_coverage_pct)),
            max_consecutive_missing=int(
                crisis_cfg.get("daily_max_consecutive_missing", daily_thresholds.max_consecutive_missing)
            ),
        )
        monthly_window_thresholds = GapThresholds(
            min_coverage_pct=float(
                crisis_cfg.get("monthly_min_coverage_pct", monthly_thresholds.min_coverage_pct)
            ),
            max_consecutive_missing=int(
                crisis_cfg.get("monthly_max_consecutive_missing", monthly_thresholds.max_consecutive_missing)
            ),
        )

        daily_window_critical = set(crisis_cfg.get("daily_critical_columns", daily_critical))
        monthly_window_critical = set(crisis_cfg.get("monthly_critical_columns", monthly_critical))

        crisis_reports.append(
            _evaluate_columns(
                daily_window,
                "daily_crisis",
                date_col,
                daily_window_thresholds,
                daily_window_critical,
            )
        )
        crisis_reports.append(
            _evaluate_columns(
                monthly_window,
                "monthly_crisis",
                date_col,
                monthly_window_thresholds,
                monthly_window_critical,
            )
        )

    report = pd.concat([daily_report, monthly_report, *crisis_reports], ignore_index=True)
    critical_failures = int(report[(report["critical"]) & (report["status"] == "fail")].shape[0])

    return QualitySummary(report=report, critical_failures=critical_failures)
