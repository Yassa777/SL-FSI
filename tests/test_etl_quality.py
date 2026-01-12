from __future__ import annotations

import pandas as pd

from slfsi.etl.quality import run_quality_checks


def test_quality_checks_include_crisis_window() -> None:
    dates = pd.date_range("2020-01-01", periods=10, freq="D")
    daily = pd.DataFrame(
        {
            "date": dates,
            "usd_lkr": [1.0, 1.1] + [None] * 8,
        }
    )

    monthly = pd.DataFrame(
        {
            "date": pd.to_datetime(["2020-01-01", "2020-02-01"]),
            "usd_lkr": [1.0, None],
        }
    )

    config = {
        "daily": {
            "min_coverage_pct": 80,
            "max_consecutive_missing": 2,
            "critical_columns": ["usd_lkr"],
        },
        "monthly": {
            "min_coverage_pct": 80,
            "max_consecutive_missing": 1,
            "critical_columns": ["usd_lkr"],
        },
        "crisis_window": {
            "start": "2020-01-05",
            "end": "2020-02-15",
            "daily_min_coverage_pct": 80,
            "monthly_min_coverage_pct": 80,
            "daily_critical_columns": ["usd_lkr"],
            "monthly_critical_columns": ["usd_lkr"],
        },
    }

    summary = run_quality_checks(daily, monthly, config, date_col="date")
    report = summary.report

    assert {"daily", "monthly", "daily_crisis", "monthly_crisis"}.issubset(
        set(report["dataset"])
    )
    assert summary.critical_failures >= 4
