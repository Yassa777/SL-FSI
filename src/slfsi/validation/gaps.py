"""Gap checks for validation workflows."""

from __future__ import annotations

from typing import Mapping

import pandas as pd

from slfsi.config.schema import ColumnSchema
from slfsi.etl.quality import run_quality_checks, QualitySummary


def run_gap_report(
    daily: pd.DataFrame,
    monthly: pd.DataFrame,
    config: Mapping[str, object],
    schema: ColumnSchema,
) -> QualitySummary:
    """Run quality checks for validation reporting.

    Economic intent:
        Validation metrics should be conditioned on data availability to
        avoid overconfidence in regimes inferred from sparse inputs.

    Args:
        daily: Daily panel dataframe.
        monthly: Monthly panel dataframe.
        config: Quality configuration mapping.
        schema: Column schema.

    Returns:
        QualitySummary with coverage and gap statistics.
    """
    return run_quality_checks(daily, monthly, config, date_col=schema.date)
