"""Validation pipelines for SL-FSI."""

from __future__ import annotations

import logging
from pathlib import Path
from typing import Optional

import pandas as pd

from slfsi.config.loader import load_config
from slfsi.config.schema import ColumnSchema, load_schema
from slfsi.config.settings import Settings
from slfsi.validation.enhanced import run_enhanced_validation
from slfsi.validation.event_alignment import evaluate_event_alignment, parse_events
from slfsi.validation.framework import (
    HMMConfig,
    analyze_false_alarms,
    analyze_transitions,
    build_monthly_from_daily,
    calculate_metrics,
    fit_hmm,
    fit_zscore_baseline,
)
from slfsi.validation.reporting import (
    build_base_report,
    build_enhanced_report,
    build_framework_report,
    write_report,
)


def _load_daily(settings: Settings, schema: ColumnSchema) -> pd.DataFrame:
    daily_path = settings.merged_dir / "slfsi_daily_panel.csv"
    if not daily_path.exists():
        raise FileNotFoundError(f"Missing daily panel: {daily_path}")
    return pd.read_csv(daily_path, parse_dates=[schema.date])


def _load_probs(settings: Settings, schema: ColumnSchema) -> pd.DataFrame:
    probs_path = settings.merged_dir / "hmm_probs_monthly.csv"
    if not probs_path.exists():
        raise FileNotFoundError(f"Missing probabilities: {probs_path}")
    return pd.read_csv(probs_path, parse_dates=[schema.date])


def run(config_path: Optional[str] = None) -> int:
    """Run validation workflows.

    Economic intent:
        Compares HMM regimes against pre-specified crisis events and
        validates regime stability with sustained probability crossings.

    Args:
        config_path: Optional path to a YAML/JSON config file.

    Returns:
        Process exit code (0 for success).
    """
    logger = logging.getLogger(__name__)
    settings = Settings.default()
    schema, _ = load_schema(settings.configs_dir / "schema.yml")

    cfg_path = Path(config_path) if config_path else settings.configs_dir / "validation.yml"
    config = load_config(cfg_path)

    report = build_base_report()

    if config.get("run_framework", True):
        hmm_cfg = config.get("hmm", {})
        features = tuple(hmm_cfg.get("features", []))
        hmm_config = HMMConfig(
            features=features,
            n_states=int(hmm_cfg.get("n_states", 3)),
            covariance_type=str(hmm_cfg.get("covariance_type", "diag")),
            n_iter=int(hmm_cfg.get("n_iter", 300)),
            random_state=int(hmm_cfg.get("random_state", 42)),
        )

        daily = _load_daily(settings, schema)
        monthly = build_monthly_from_daily(daily, hmm_config.features)

        monthly_hmm, _ = fit_hmm(monthly, hmm_config)
        monthly_baseline = fit_zscore_baseline(
            monthly_hmm.copy(), hmm_config.features, float(config.get("zscore_threshold", 2.0))
        )
        monthly_hmm["zscore_regime"] = monthly_baseline["zscore_regime"]

        event_specs = parse_events(config.get("events", {}).get("framework", []))
        windows = config.get("windows", {})
        tactical = int(windows.get("tactical_months", 1))
        strategic = int(windows.get("strategic_months", 2))

        hmm_tactical = evaluate_event_alignment(monthly_hmm, event_specs, "regime_label", tactical)
        baseline_tactical = evaluate_event_alignment(monthly_hmm, event_specs, "zscore_regime", tactical)
        hmm_strategic = evaluate_event_alignment(monthly_hmm, event_specs, "regime_label", strategic)
        baseline_strategic = evaluate_event_alignment(monthly_hmm, event_specs, "zscore_regime", strategic)

        costs = config.get("costs", {})
        tactical_metrics = calculate_metrics(
            hmm_tactical,
            baseline_tactical,
            lambda_missed=float(costs.get("lambda_missed", 2.0)),
            lambda_false=float(costs.get("lambda_false", 1.0)),
        )
        strategic_metrics = calculate_metrics(
            hmm_strategic,
            baseline_strategic,
            lambda_missed=float(costs.get("lambda_missed", 2.0)),
            lambda_false=float(costs.get("lambda_false", 1.0)),
        )

        transitions = analyze_transitions(monthly_hmm, model_col="regime_label")
        false_alarm = analyze_false_alarms(
            monthly_hmm,
            event_specs,
            window_days=int(windows.get("false_alarm_days", 60)),
            model_col="regime_label",
        )

        results_df = pd.DataFrame(hmm_strategic["details"])
        results_df.to_csv(settings.merged_dir / "validation_results.csv", index=False)
        monthly_hmm.to_csv(settings.merged_dir / "monthly_regimes_validated.csv", index=False)

        logger.info("Validation saved to data/merged/validation_results.csv")
        logger.info("Validated regimes saved to data/merged/monthly_regimes_validated.csv")
        logger.info("Tactical metrics: %s", tactical_metrics["HMM"]["hit_rate"])
        logger.info("Strategic metrics: %s", strategic_metrics["HMM"]["hit_rate"])
        logger.info("False alarm rate: %s", false_alarm["false_alarm_rate"])

        report["framework"] = build_framework_report(
            hmm_config=hmm_cfg,
            windows=windows,
            costs=costs,
            tactical_metrics=tactical_metrics,
            strategic_metrics=strategic_metrics,
            false_alarm=false_alarm,
            transitions=transitions,
            hmm_tactical=hmm_tactical,
            hmm_strategic=hmm_strategic,
            baseline_tactical=baseline_tactical,
            baseline_strategic=baseline_strategic,
        )

    if config.get("run_enhanced", True):
        enhanced_cfg = config.get("enhanced", {})
        tau = float(enhanced_cfg.get("tau", 0.7))
        k = int(enhanced_cfg.get("k", 3))
        tactical = int(enhanced_cfg.get("tactical_months", 1))
        strategic = int(enhanced_cfg.get("strategic_months", 2))

        probs_monthly = _load_probs(settings, schema)
        events = parse_events(config.get("events", {}).get("enhanced", []))
        results = run_enhanced_validation(
            probs_monthly,
            events,
            tau=tau,
            k=k,
            tactical_months=tactical,
            strategic_months=strategic,
        )

        results["strategic"].to_csv(
            settings.merged_dir / "enhanced_validation_results.csv", index=False
        )
        logger.info("Enhanced validation saved to data/merged/enhanced_validation_results.csv")
        report["enhanced"] = build_enhanced_report(
            tau=tau,
            k=k,
            tactical_months=tactical,
            strategic_months=strategic,
            tactical_df=results["tactical"],
            strategic_df=results["strategic"],
        )

    report_path = settings.merged_dir / "validation_report.json"
    md_path = settings.repo_root / "DOCS/data/merged/validation_report.md"
    write_report(report, report_path, md_path)
    logger.info("Validation report saved to %s", report_path)

    return 0
