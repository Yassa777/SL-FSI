"""Compute leading indicators for early warning analysis."""

from __future__ import annotations

import logging
from pathlib import Path
from typing import Optional

import pandas as pd

from slfsi.config.loader import load_config
from slfsi.config.schema import load_schema
from slfsi.config.settings import Settings


def run(config_path: Optional[str] = None) -> int:
    """Compute leading indicators on the monthly panel.

    Economic intent:
        Leading indicators (reserve adequacy, real rates, spreads) provide
        forward-looking signals of stress accumulation before regime shifts.

    Args:
        config_path: Optional path to a YAML/JSON config file.

    Returns:
        Process exit code (0 for success).
    """
    logger = logging.getLogger(__name__)
    settings = Settings.default()

    cfg_path = Path(config_path) if config_path else settings.configs_dir / "leading_indicators.yml"
    config = load_config(cfg_path)
    schema, _ = load_schema(settings.configs_dir / "schema.yml")

    monthly_path = settings.merged_dir / "slfsi_monthly_panel.csv"
    if not monthly_path.exists():
        logger.error("Missing monthly panel: %s", monthly_path)
        return 1

    monthly = pd.read_csv(monthly_path, parse_dates=[schema.date])

    pboc = config.get("pboc_swap", {})
    pboc_amount = float(pboc.get("amount_usd_m", 1500))
    pboc_start = pd.Timestamp(pboc.get("start", "2021-03-01"))
    monthly_imports = float(config.get("monthly_imports_usd_m", 1500))
    equilibrium_rate = float(config.get("equilibrium_real_rate", 2.0))

    if schema.isb_yield in monthly.columns and schema.us_10y_yield in monthly.columns:
        monthly["isb_spread_bps"] = (monthly[schema.isb_yield] - monthly[schema.us_10y_yield]) * 100

    if schema.gross_reserves_usd_m in monthly.columns:
        monthly["net_reserves_usd_m"] = monthly[schema.gross_reserves_usd_m]
        mask = monthly[schema.date] >= pboc_start
        monthly.loc[mask, "net_reserves_usd_m"] = (
            monthly.loc[mask, schema.gross_reserves_usd_m] - pboc_amount
        )
        monthly["net_import_cover"] = monthly["net_reserves_usd_m"] / monthly_imports

    if schema.real_policy_rate in monthly.columns:
        monthly["real_rate_gap"] = monthly[schema.real_policy_rate] - equilibrium_rate

    components = []
    if "net_import_cover" in monthly.columns:
        series = monthly["net_import_cover"]
        monthly["z_reserve_stress"] = -(series - series.mean()) / series.std()
        components.append("z_reserve_stress")

    if schema.real_policy_rate in monthly.columns:
        series = monthly[schema.real_policy_rate]
        monthly["z_real_rate_stress"] = -(series - series.mean()) / series.std()
        components.append("z_real_rate_stress")

    if "isb_spread_bps" in monthly.columns:
        series = monthly["isb_spread_bps"]
        monthly["z_isb_stress"] = (series - series.mean()) / series.std()
        components.append("z_isb_stress")

    if len(components) >= 2:
        monthly["early_warning_score"] = monthly[components].mean(axis=1)

    output_path = settings.merged_dir / "monthly_with_indicators.csv"
    monthly.to_csv(output_path, index=False)
    logger.info("Saved leading indicators: %s", output_path)

    return 0
