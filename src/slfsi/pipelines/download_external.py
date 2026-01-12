"""Download external data sources and build manual templates."""

from __future__ import annotations

import logging
from pathlib import Path
from typing import Any, Mapping, Optional

import pandas as pd

from slfsi.config.loader import load_config
from slfsi.config.settings import Settings
from slfsi.io.writers import write_csv


def _resolve_path(settings: Settings, raw_path: str) -> Path:
    path = Path(raw_path)
    if path.is_absolute():
        return path
    return settings.repo_root / path


def _download_yfinance_series(symbol: str, start: str, end: str, interval: str) -> pd.DataFrame:
    try:
        import yfinance as yf
    except ImportError as exc:
        raise RuntimeError("yfinance is required to download market data") from exc

    data = yf.download(symbol, start=start, end=end, interval=interval, progress=False)
    if data.empty:
        raise ValueError(f"yfinance returned no data for {symbol}")
    return data.reset_index()


def _build_policy_rates(policy_cfg: Mapping[str, Any]) -> tuple[pd.DataFrame, pd.DataFrame]:
    date_col = str(policy_cfg.get("date_col", "date"))
    changes = pd.DataFrame(policy_cfg.get("changes", []))
    if changes.empty:
        raise ValueError("No policy rate changes provided")

    changes[date_col] = pd.to_datetime(changes[date_col])
    changes = changes.sort_values(date_col)

    columns_cfg = policy_cfg.get("columns", {})
    rename_map = {
        key: columns_cfg.get(key, key)
        for key in changes.columns
        if key in columns_cfg
    }
    if rename_map:
        changes = changes.rename(columns=rename_map)

    start = policy_cfg.get("start")
    end = policy_cfg.get("end")
    if not start or not end:
        raise ValueError("Policy rate start/end date missing in config")

    date_range = pd.date_range(start=start, end=end, freq="D")
    daily = pd.DataFrame({date_col: date_range})

    sdfr_col = columns_cfg.get("sdfr", "sdfr")
    slfr_col = columns_cfg.get("slfr", "slfr")
    opr_col = columns_cfg.get("opr", "opr")
    policy_ceiling_col = columns_cfg.get("policy_ceiling", "policy_ceiling")

    for _, row in changes.iterrows():
        mask = daily[date_col] >= row[date_col]
        for col in (sdfr_col, slfr_col, opr_col):
            if col in changes.columns:
                value = row.get(col)
                if pd.notna(value):
                    daily.loc[mask, col] = value

    if slfr_col in daily.columns and opr_col in daily.columns:
        daily[policy_ceiling_col] = daily[slfr_col].fillna(daily[opr_col])
    elif slfr_col in daily.columns:
        daily[policy_ceiling_col] = daily[slfr_col]
    elif opr_col in daily.columns:
        daily[policy_ceiling_col] = daily[opr_col]

    daily[date_col] = pd.to_datetime(daily[date_col]).dt.normalize()
    return changes, daily


def _build_template(template_cfg: Mapping[str, Any]) -> pd.DataFrame:
    date_col = str(template_cfg.get("date_col", "date"))
    start = template_cfg.get("start")
    periods = int(template_cfg.get("periods", 0))
    freq = str(template_cfg.get("freq", "MS"))
    date_format = template_cfg.get("date_format")

    if not start or periods <= 0:
        raise ValueError("Template start or periods missing")

    dates = pd.date_range(start=start, periods=periods, freq=freq)
    if date_format:
        date_values = dates.strftime(date_format)
    else:
        date_values = dates

    data: dict[str, Any] = {date_col: date_values}
    for col, default in (template_cfg.get("columns") or {}).items():
        data[col] = [default] * len(dates)

    return pd.DataFrame(data)


def run(config_path: Optional[str] = None) -> int:
    """Run the external data download pipeline.

    Economic intent:
        External series (gold, US yields, policy rates) add global and
        policy context to domestic stress measures while keeping sources
        auditable and configurable.

    Args:
        config_path: Optional path to a YAML/JSON config file.

    Returns:
        Process exit code (0 for success).
    """
    logger = logging.getLogger(__name__)
    settings = Settings.default()

    cfg_path = Path(config_path) if config_path else settings.configs_dir / "external_data.yml"
    config = load_config(cfg_path)
    failures = 0

    yfinance_cfg = config.get("yfinance", {})
    yf_start = str(yfinance_cfg.get("start", "2010-01-01"))
    yf_end = str(yfinance_cfg.get("end", "2025-12-31"))
    yf_interval = str(yfinance_cfg.get("interval", "1d"))

    for name, series_cfg in config.get("series", {}).items():
        symbol = series_cfg.get("symbol")
        output = series_cfg.get("output")
        date_col = series_cfg.get("date_col", "date")
        value_col = series_cfg.get("value_col", "value")
        required = bool(series_cfg.get("required", False))

        if not symbol or not output:
            logger.error("Series %s missing symbol/output in config", name)
            failures += 1
            continue

        try:
            data = _download_yfinance_series(symbol, yf_start, yf_end, yf_interval)
            date_field = data.columns[0]
            if "Close" not in data.columns:
                raise ValueError(f"Close column missing for {symbol}")
            df = data[[date_field, "Close"]].rename(
                columns={date_field: date_col, "Close": value_col}
            )
            df[date_col] = pd.to_datetime(df[date_col]).dt.normalize()
            output_path = _resolve_path(settings, output)
            write_csv(df, output_path)
            logger.info("Saved %s (%s rows): %s", name, len(df), output_path)
        except Exception as exc:
            if required:
                logger.error("Failed to download %s: %s", name, exc)
                failures += 1
            else:
                logger.warning("Skipped %s: %s", name, exc)

    policy_cfg = config.get("policy_rates")
    if policy_cfg:
        try:
            changes_df, daily_df = _build_policy_rates(policy_cfg)
            changes_path = _resolve_path(settings, policy_cfg["output_changes"])
            daily_path = _resolve_path(settings, policy_cfg["output_daily"])
            write_csv(changes_df, changes_path)
            write_csv(daily_df, daily_path)
            logger.info("Saved policy rate changes: %s", changes_path)
            logger.info("Saved policy rates daily: %s", daily_path)
        except Exception as exc:
            logger.error("Failed to build policy rates: %s", exc)
            failures += 1

    for template_cfg in config.get("templates", []):
        name = template_cfg.get("name", "template")
        output = template_cfg.get("output")
        if not output:
            logger.warning("Template %s missing output path", name)
            continue
        try:
            df = _build_template(template_cfg)
            output_path = _resolve_path(settings, output)
            write_csv(df, output_path)
            logger.info("Saved template %s: %s", name, output_path)
        except Exception as exc:
            logger.error("Failed to build template %s: %s", name, exc)
            failures += 1

    for instruction in config.get("manual_instructions", []):
        logger.info("Manual step: %s", instruction)

    return 1 if failures else 0
