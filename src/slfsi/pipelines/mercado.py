"""Run Mercado-Park FSI pipeline."""

from __future__ import annotations

import logging
from pathlib import Path
from typing import Optional

import pandas as pd

from slfsi.config.loader import load_config
from slfsi.config.schema import load_schema
from slfsi.config.settings import Settings
from slfsi.io.writers import write_csv
from slfsi.models.mercado import MercadoConfig, compute_mercado_fsi


def run(config_path: Optional[str] = None) -> int:
    """Compute Mercado-Park FSI from the monthly panel."""
    logger = logging.getLogger(__name__)
    settings = Settings.default()
    schema, _ = load_schema(settings.configs_dir / "schema.yml")

    cfg_path = Path(config_path) if config_path else settings.configs_dir / "mercado.yml"
    config = load_config(cfg_path)

    monthly_path = settings.merged_dir / "slfsi_monthly_panel.csv"
    if not monthly_path.exists():
        logger.error("Missing monthly panel: %s", monthly_path)
        return 1

    monthly = pd.read_csv(monthly_path, parse_dates=[schema.date])

    mercado_cfg = MercadoConfig(
        rolling_window=int(config.get("rolling_window", 36)),
        empi_lookback=int(config.get("empi_lookback", 60)),
        min_periods=int(config.get("min_periods", 12)),
        debt_spread_min_obs=int(config.get("debt_spread_min_obs", 36)),
    )

    fsi_df = compute_mercado_fsi(monthly, schema, mercado_cfg, data_is_monthly=True)
    output_path = settings.repo_root / config.get("outputs", {}).get(
        "monthly", "data/merged/mercado_fsi_monthly.csv"
    )
    write_csv(fsi_df, output_path)
    logger.info("Saved Mercado FSI: %s", output_path)
    return 0
