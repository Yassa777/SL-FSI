"""Train HMM models for SL-FSI."""

from __future__ import annotations

import logging
import json
from pathlib import Path
from typing import Optional

import pandas as pd

from slfsi.config.loader import load_config
from slfsi.config.schema import load_schema
from slfsi.config.settings import Settings
from slfsi.io.writers import write_csv
from slfsi.models.hmm import HMMModelConfig, fit_hmm_with_probs, prepare_monthly_features
from slfsi.models.hmm import run_oos, run_realtime


def run(config_path: Optional[str] = None) -> int:
    """Run the HMM training pipeline.

    Args:
        config_path: Optional path to a YAML/JSON config file.

    Returns:
        Process exit code (0 for success).
    """
    logger = logging.getLogger(__name__)
    settings = Settings.default()

    cfg_path = Path(config_path) if config_path else settings.configs_dir / "hmm.yml"
    config = load_config(cfg_path)
    schema, _ = load_schema(settings.configs_dir / "schema.yml")

    daily_path = settings.merged_dir / "slfsi_daily_panel.csv"
    if not daily_path.exists():
        logger.error("Missing daily panel: %s", daily_path)
        return 1

    daily = pd.read_csv(daily_path, parse_dates=[schema.date])

    features = tuple(config.get("features", []))
    if not features:
        logger.error("No features configured for HMM training")
        return 1

    model_cfg = config.get("model", {})
    hmm_config = HMMModelConfig(
        features=features,
        n_states=int(model_cfg.get("n_states", 3)),
        covariance_type=str(model_cfg.get("covariance_type", "diag")),
        n_iter=int(model_cfg.get("n_iter", 300)),
        random_state=int(model_cfg.get("random_state", 42)),
    )

    agg_cfg = config.get("monthly_aggregation", {})
    monthly = prepare_monthly_features(
        daily,
        features,
        schema.date,
        method=str(agg_cfg.get("method", "first")),
        interpolate=agg_cfg.get("interpolate", "linear"),
        fill_edges=bool(agg_cfg.get("fill_edges", True)),
    )

    outputs_cfg = config.get("outputs", {})
    full_sample_path = outputs_cfg.get("full_sample", "data/merged/hmm_regimes_3state_monthly.csv")
    full_sample = fit_hmm_with_probs(monthly, hmm_config, schema)[0]
    full_sample_out = settings.repo_root / full_sample_path
    write_csv(full_sample, full_sample_out)
    logger.info("Saved full-sample regimes: %s", full_sample_out)

    realtime_cfg = config.get("realtime", {})
    if realtime_cfg.get("enabled", True):
        realtime_df, comparison_df = run_realtime(
            monthly,
            hmm_config,
            schema,
            realtime_cfg,
            full_sample=full_sample,
        )
        if not realtime_df.empty:
            outputs = realtime_cfg.get("outputs", {})
            probs_path = settings.repo_root / outputs.get(
                "probs", "data/merged/hmm_probs_monthly.csv"
            )
            recursive_path = settings.repo_root / outputs.get(
                "recursive", "data/merged/recursive_realtime_results.csv"
            )
            write_csv(realtime_df, probs_path)
            write_csv(realtime_df, recursive_path)
            logger.info("Saved realtime probabilities: %s", probs_path)
            logger.info("Saved realtime results: %s", recursive_path)
        if comparison_df is not None and not comparison_df.empty:
            comparison_path = settings.repo_root / realtime_cfg.get("outputs", {}).get(
                "comparison", "data/merged/realtime_vs_fullsample_comparison.csv"
            )
            write_csv(comparison_df, comparison_path)
            logger.info("Saved realtime comparison: %s", comparison_path)

    oos_cfg = config.get("oos", {})
    if oos_cfg.get("enabled", True):
        oos_results = run_oos(monthly, hmm_config, schema, oos_cfg)
        oos_outputs = oos_cfg.get("outputs", {})
        predictions_path = settings.repo_root / oos_outputs.get(
            "predictions", "data/merged/oos_predictions.csv"
        )
        params_path = settings.repo_root / oos_outputs.get(
            "params", "data/merged/oos_model_params.json"
        )
        write_csv(oos_results.predictions, predictions_path)
        params_path.parent.mkdir(parents=True, exist_ok=True)
        params_path.write_text(json.dumps(oos_results.model_info, indent=2), encoding="utf-8")
        logger.info("Saved OOS predictions: %s", predictions_path)
        logger.info("Saved OOS model params: %s", params_path)

    return 0
