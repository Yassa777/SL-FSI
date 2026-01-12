"""Build combined FSI-HMM score."""

from __future__ import annotations

import logging
from pathlib import Path
from typing import Optional

import pandas as pd

from slfsi.config.loader import load_config
from slfsi.config.schema import load_schema
from slfsi.config.settings import Settings
from slfsi.io.writers import write_csv
from slfsi.models.combine import CombineConfig, combine_fsi_hmm


def run(config_path: Optional[str] = None) -> int:
    """Run the combined FSI-HMM pipeline."""
    logger = logging.getLogger(__name__)
    settings = Settings.default()
    schema, _ = load_schema(settings.configs_dir / "schema.yml")

    cfg_path = Path(config_path) if config_path else settings.configs_dir / "combine.yml"
    config = load_config(cfg_path)

    fsi_path = settings.merged_dir / "mercado_fsi_monthly.csv"
    hmm_path = settings.merged_dir / "hmm_probs_monthly.csv"
    if not fsi_path.exists() or not hmm_path.exists():
        logger.error("Missing inputs for combine pipeline")
        return 1

    fsi_df = pd.read_csv(fsi_path, parse_dates=[schema.date])
    hmm_df = pd.read_csv(hmm_path, parse_dates=[schema.date])

    combine_cfg = CombineConfig(
        alpha=float(config.get("alpha", 0.5)),
        stress_threshold=float(config.get("stress_threshold", 0.5)),
        crisis_threshold=float(config.get("crisis_threshold", 0.7)),
        fsi_threshold=float(config.get("fsi_threshold", 1.0)),
        hmm_threshold=float(config.get("hmm_threshold", 0.5)),
    )

    combined = combine_fsi_hmm(fsi_df, hmm_df, schema, combine_cfg)
    output_path = settings.repo_root / config.get("outputs", {}).get(
        "combined", "data/merged/combined_fsi_hmm.csv"
    )
    write_csv(combined, output_path)
    logger.info("Saved combined FSI-HMM: %s", output_path)
    return 0
