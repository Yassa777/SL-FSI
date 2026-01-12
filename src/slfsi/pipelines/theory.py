"""Run theory-based regime classification."""

from __future__ import annotations

import logging
from pathlib import Path
from typing import Optional

import pandas as pd

from slfsi.config.loader import load_config
from slfsi.config.schema import load_schema
from slfsi.config.settings import Settings
from slfsi.io.writers import write_csv
from slfsi.models.theory import classify_theory_regimes, compare_with_hmm


def run(config_path: Optional[str] = None) -> int:
    """Run theory-based classification pipeline."""
    logger = logging.getLogger(__name__)
    settings = Settings.default()
    schema, _ = load_schema(settings.configs_dir / "schema.yml")

    cfg_path = Path(config_path) if config_path else settings.configs_dir / "theory.yml"
    config = load_config(cfg_path)

    inputs = config.get("inputs", {})
    monthly_path = settings.repo_root / inputs.get(
        "monthly_with_indicators", "data/merged/monthly_with_indicators.csv"
    )
    if not monthly_path.exists():
        monthly_path = settings.repo_root / inputs.get(
            "monthly_panel", "data/merged/slfsi_monthly_panel.csv"
        )
    if not monthly_path.exists():
        logger.error("Missing monthly input: %s", monthly_path)
        return 1

    monthly = pd.read_csv(monthly_path, parse_dates=[schema.date])
    monthly_with_theory, _ = classify_theory_regimes(monthly, schema, config)

    outputs = config.get("outputs", {})
    theory_path = settings.repo_root / outputs.get(
        "monthly_with_theory", "data/merged/monthly_with_theory_regimes.csv"
    )
    write_csv(monthly_with_theory, theory_path)
    logger.info("Saved theory regimes: %s", theory_path)

    hmm_path = settings.repo_root / inputs.get("hmm_probs", "data/merged/hmm_probs_monthly.csv")
    if hmm_path.exists():
        hmm = pd.read_csv(hmm_path, parse_dates=[schema.date])
        comparison = compare_with_hmm(monthly_with_theory, hmm, schema)
        comparison_path = settings.repo_root / outputs.get(
            "theory_vs_hmm", "data/merged/theory_vs_hmm_comparison.csv"
        )
        write_csv(comparison, comparison_path)
        logger.info("Saved theory vs HMM comparison: %s", comparison_path)

    return 0
