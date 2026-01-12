"""Run analysis/validation utilities for SL-FSI."""

from __future__ import annotations

import logging
from pathlib import Path
from typing import Optional

import pandas as pd

from slfsi.config.loader import load_config
from slfsi.config.schema import load_schema
from slfsi.config.settings import Settings
from slfsi.validation.compare import run_compare
from slfsi.validation.feature_overlap import run_feature_overlap
from slfsi.validation.transitions import run_transitions
from slfsi.plots.three_panel import run_three_panel


def run(config_path: Optional[str] = None) -> int:
    """Run analysis utilities (FSI vs HMM, overlap, transitions).

    Args:
        config_path: Optional path to a YAML/JSON config file.

    Returns:
        Process exit code (0 for success).
    """
    logger = logging.getLogger(__name__)
    settings = Settings.default()
    schema, _ = load_schema(settings.configs_dir / "schema.yml")

    cfg_path = Path(config_path) if config_path else settings.configs_dir / "analysis.yml"
    config = load_config(cfg_path)

    compare_cfg = config.get("compare_fsi_hmm")
    if compare_cfg:
        run_compare(compare_cfg, schema, settings)
        logger.info("Completed FSI vs HMM comparison")

    overlap_cfg = config.get("feature_overlap")
    if overlap_cfg:
        daily_path = settings.merged_dir / "slfsi_daily_panel.csv"
        if not daily_path.exists():
            logger.error("Missing daily panel: %s", daily_path)
        else:
            daily = pd.read_csv(daily_path, parse_dates=[schema.date])
            overlap = run_feature_overlap(daily, overlap_cfg, schema)
            output_path = overlap_cfg.get("outputs", {}).get(
                "regimes", "data/merged/hmm_regimes_working.csv"
            )
            recommendation = overlap.get("recommendation")
            if recommendation and output_path:
                df = pd.DataFrame(
                    {"date": recommendation["dates"], "regime": recommendation["states"]}
                )
                out_path = settings.repo_root / output_path
                out_path.parent.mkdir(parents=True, exist_ok=True)
                df.to_csv(out_path, index=False)
                logger.info("Saved recommended HMM regimes: %s", out_path)

    transitions_cfg = config.get("transitions")
    if transitions_cfg:
        run_transitions(transitions_cfg, schema, settings)
        logger.info("Completed transition dynamics analysis")

    plot_cfg = config.get("three_panel")
    if plot_cfg:
        run_three_panel(plot_cfg, schema, settings)
        logger.info("Completed three-panel comparison plot")

    return 0
