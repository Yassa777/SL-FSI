"""Build the SL-FSI daily and monthly panels."""

from __future__ import annotations

import logging
from pathlib import Path
from typing import Optional

import pandas as pd

from slfsi.config.loader import load_config
from slfsi.config.schema import load_schema
from slfsi.config.settings import Settings
from slfsi.etl.ingest import load_sources
from slfsi.etl.merge import DateRange, build_panels
from slfsi.etl.quality import run_quality_checks


def _load_overlay(overlay: dict, settings: Settings) -> dict:
    """Load a historical overlay dataset.

    Economic intent:
        Historical overlays extend the macro context so regime models can
        distinguish structural stress from short-lived episodes.

    Args:
        overlay: Overlay configuration dictionary.
        settings: Repository settings for path resolution.

    Returns:
        Overlay dictionary with loaded dataframe, or empty dict if missing.
    """
    path = (settings.repo_root / overlay["path"]).resolve()
    if not path.exists():
        return {}

    df = pd.read_csv(path)
    date_col = overlay.get("date_col", "date")
    df[date_col] = pd.to_datetime(df[date_col])
    value_col = overlay.get("value_col")
    if value_col and value_col in df.columns:
        df = df[[date_col, value_col]].dropna()
    return {**overlay, "data": df}


def run(config_path: Optional[str] = None) -> int:
    """Run the panel build pipeline.

    Economic intent:
        Produces harmonized daily and monthly panels for stress analysis,
        ensuring that high-frequency volatility is computed before any
        macro series are upsampled.

    Args:
        config_path: Optional path to a YAML/JSON config file.

    Returns:
        Process exit code (0 for success).
    """
    logger = logging.getLogger(__name__)
    settings = Settings.default()

    etl_config_path = Path(config_path) if config_path else settings.configs_dir / "etl.yml"
    etl_config = load_config(etl_config_path)

    sources_config_path = settings.configs_dir / "data_sources.yml"
    sources_config = load_config(sources_config_path)

    sources = load_sources(sources_config, settings)
    source_specs = sources_config.get("sources", {})

    daily_names = [name for name, cfg in source_specs.items() if cfg.get("frequency") == "daily"]
    monthly_names = [name for name, cfg in source_specs.items() if cfg.get("frequency") == "monthly"]

    if "awcmr_monthly" in sources and "awcmr_daily_fallback" in sources:
        daily_names = [name for name in daily_names if name != "awcmr_daily_fallback"]
        logger.info("Using awcmr_monthly; ignoring awcmr_daily_fallback")

    daily_sources = [sources[name] for name in daily_names if name in sources]
    monthly_sources = [sources[name] for name in monthly_names if name in sources]

    overlays = []
    for overlay in etl_config.get("historical_overlays", []):
        loaded = _load_overlay(overlay, settings)
        if loaded:
            overlays.append(loaded)
        else:
            logger.warning("Historical overlay missing: %s", overlay.get("path"))

    date_range = DateRange(
        start=pd.Timestamp(etl_config["date_range"]["start"]),
        end=pd.Timestamp(etl_config["date_range"]["end"]),
    )

    schema, _ = load_schema(settings.configs_dir / "schema.yml")
    daily, monthly = build_panels(
        daily_sources=daily_sources,
        monthly_sources=monthly_sources,
        overlays=overlays,
        date_range=date_range,
        schema=schema,
        config=etl_config,
    )

    settings.merged_dir.mkdir(parents=True, exist_ok=True)
    daily_path = settings.merged_dir / "slfsi_daily_panel.csv"
    monthly_path = settings.merged_dir / "slfsi_monthly_panel.csv"

    daily.to_csv(daily_path, index=False)
    monthly.to_csv(monthly_path, index=False)

    logger.info("Saved daily panel: %s", daily_path)
    logger.info("Saved monthly panel: %s", monthly_path)

    quality_config_path = settings.configs_dir / "quality.yml"
    if quality_config_path.exists():
        quality_config = load_config(quality_config_path)
        summary = run_quality_checks(daily, monthly, quality_config, date_col=schema.date)
        quality_dir = settings.data_dir / "quality"
        quality_dir.mkdir(parents=True, exist_ok=True)
        report_path = quality_dir / "quality_report.csv"
        summary.report.to_csv(report_path, index=False)
        logger.info("Saved quality report: %s", report_path)
        if quality_config.get("fail_on_critical") and summary.critical_failures > 0:
            logger.error("Critical data gaps detected: %s", summary.critical_failures)
            return 1

    return 0
