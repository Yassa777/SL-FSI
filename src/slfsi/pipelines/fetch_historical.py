"""Fetch historical macro data for the SL-FSI extension."""

from __future__ import annotations

import logging
from datetime import datetime
from pathlib import Path
from typing import Any, Mapping, Optional

import pandas as pd

from slfsi.config.loader import load_config
from slfsi.config.settings import Settings
from slfsi.io.readers import read_csv
from slfsi.io.writers import write_csv


def _resolve_path(settings: Settings, raw_path: str) -> Path:
    path = Path(raw_path)
    if path.is_absolute():
        return path
    return settings.repo_root / path


def _fetch_fred_series(series_id: str, start: str, end: str) -> pd.DataFrame:
    try:
        from pandas_datareader import data as web
    except ImportError as exc:
        raise RuntimeError("pandas-datareader is required to fetch FRED data") from exc

    return web.DataReader(series_id, "fred", start, end).reset_index()


def _fetch_fred_fx(
    cfg: Mapping[str, Any],
    date_range: Mapping[str, pd.Timestamp],
) -> pd.DataFrame:
    series_id = str(cfg.get("series_id", "EXSLUS"))
    fetch_start = str(cfg.get("fetch_start", date_range["start"].date()))
    date_col = str(cfg.get("date_col", "date"))
    value_col = str(cfg.get("value_col", "usd_lkr"))

    raw = _fetch_fred_series(series_id, fetch_start, date_range["end"].date().isoformat())
    raw = raw.rename(columns={raw.columns[0]: date_col, series_id: value_col})
    raw[date_col] = pd.to_datetime(raw[date_col])

    mask = (raw[date_col] >= date_range["start"]) & (raw[date_col] <= date_range["end"])
    return raw.loc[mask, [date_col, value_col]].dropna()


def _build_inflation(
    cfg: Mapping[str, Any],
    date_range: Mapping[str, pd.Timestamp],
    settings: Settings,
) -> pd.DataFrame:
    annual_path = _resolve_path(settings, cfg["annual_path"])
    annual_date_col = str(cfg.get("annual_date_col", "date"))
    annual_value_col = str(cfg.get("annual_value_col", "inflation_yoy_pct"))
    monthly_reference_path = _resolve_path(settings, cfg["monthly_reference_path"])
    monthly_date_col = str(cfg.get("monthly_date_col", "date"))
    monthly_value_col = str(cfg.get("monthly_value_col", "ncpi_yoy_pct"))
    date_col = str(cfg.get("date_col", "date"))
    value_col = str(cfg.get("value_col", "ncpi_yoy_pct"))
    source_col = str(cfg.get("source_col", "source"))
    source_note = str(cfg.get("source_note", "Interpolated from annual data"))

    annual = read_csv(annual_path, date_col=annual_date_col)
    annual = annual.dropna(subset=[annual_value_col])
    annual["year"] = annual[annual_date_col].dt.year
    annual = annual[(annual[annual_date_col] >= date_range["start"]) &
                    (annual[annual_date_col] <= date_range["end"])]
    annual_by_year = dict(zip(annual["year"], annual[annual_value_col]))

    seasonal_pattern = {month: 1.0 for month in range(1, 13)}
    if monthly_reference_path.exists():
        monthly = read_csv(monthly_reference_path, date_col=monthly_date_col)
        monthly = monthly.dropna(subset=[monthly_value_col])
        if not monthly.empty:
            monthly["month"] = monthly[monthly_date_col].dt.month
            seasonal = monthly.groupby("month")[monthly_value_col].mean()
            overall = monthly[monthly_value_col].mean()
            if overall:
                seasonal_pattern = (seasonal / overall).to_dict()

    rows = []
    for date in pd.date_range(date_range["start"], date_range["end"], freq="MS"):
        annual_value = annual_by_year.get(date.year)
        if annual_value is None:
            continue
        factor = seasonal_pattern.get(date.month, 1.0)
        rows.append(
            {
                date_col: date,
                value_col: round(float(annual_value) * float(factor), 2),
                source_col: source_note,
            }
        )

    return pd.DataFrame(rows)


def _fetch_world_bank(cfg: Mapping[str, Any]) -> pd.DataFrame:
    try:
        import requests
    except ImportError as exc:
        raise RuntimeError("requests is required to fetch World Bank data") from exc

    country = cfg["country"]
    indicator = cfg["indicator"]
    start_year = int(cfg.get("start_year", 2000))
    end_year = int(cfg.get("end_year", datetime.now().year))
    url = f"http://api.worldbank.org/v2/country/{country}/indicator/{indicator}"
    params = {"format": "json", "date": f"{start_year}:{end_year}", "per_page": 500}

    response = requests.get(url, params=params, timeout=30)
    response.raise_for_status()
    payload = response.json()
    if len(payload) < 2 or not payload[1]:
        raise ValueError("World Bank API returned no data")

    records = []
    for item in payload[1]:
        value = item.get("value")
        year = item.get("date")
        if value is None or year is None:
            continue
        records.append({"year": int(year), "value": float(value)})

    return pd.DataFrame(records).sort_values("year")


def _build_reserves(
    cfg: Mapping[str, Any],
    date_range: Mapping[str, pd.Timestamp],
    settings: Settings,
) -> pd.DataFrame:
    wb_cfg = cfg.get("world_bank", {})
    annual = _fetch_world_bank(wb_cfg)

    scale = float(cfg.get("scale", 1))
    annual["value_scaled"] = annual["value"] / scale
    annual_by_year = dict(zip(annual["year"], annual["value_scaled"]))

    date_col = str(cfg.get("date_col", "date"))
    value_col = str(cfg.get("value_col", "gross_reserves_usd_m"))
    source_col = str(cfg.get("source_col", "source"))
    source_note = str(cfg.get("source_note", "Interpolated from World Bank annual"))

    rows = []
    for date in pd.date_range(date_range["start"], date_range["end"], freq="MS"):
        prev_val = annual_by_year.get(date.year - 1)
        curr_val = annual_by_year.get(date.year)
        if prev_val is not None and curr_val is not None:
            t = date.month / 12
            value = prev_val + t * (curr_val - prev_val)
        elif curr_val is not None:
            value = curr_val
        else:
            continue
        rows.append(
            {
                date_col: date,
                value_col: round(float(value), 0),
                source_col: source_note,
            }
        )

    return pd.DataFrame(rows)


def _write_documentation(cfg: Mapping[str, Any], settings: Settings) -> None:
    template_path = _resolve_path(settings, cfg["template"])
    output_path = _resolve_path(settings, cfg["output"])

    template = template_path.read_text(encoding="utf-8")
    rendered = template.format(
        date=datetime.now().strftime("%Y-%m-%d"),
        pipeline="slfsi fetch-historical",
    )
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(rendered, encoding="utf-8")


def run(config_path: Optional[str] = None) -> int:
    """Run the historical data fetch pipeline.

    Economic intent:
        Extends macro context back to 2005 using documented sources and
        interpolation, enabling regime analysis across longer cycles.

    Args:
        config_path: Optional path to a YAML/JSON config file.

    Returns:
        Process exit code (0 for success).
    """
    logger = logging.getLogger(__name__)
    settings = Settings.default()

    cfg_path = Path(config_path) if config_path else settings.configs_dir / "historical_data.yml"
    config = load_config(cfg_path)

    date_cfg = config.get("date_range", {})
    date_range = {
        "start": pd.Timestamp(date_cfg.get("start", "2005-01-01")),
        "end": pd.Timestamp(date_cfg.get("end", datetime.now().strftime("%Y-%m-%d"))),
    }

    failures = 0

    fx_cfg = config.get("fred_fx", {})
    if fx_cfg:
        try:
            fx_df = _fetch_fred_fx(fx_cfg, date_range)
            output_path = _resolve_path(settings, fx_cfg["output"])
            write_csv(fx_df, output_path)
            logger.info("Saved historical FX: %s", output_path)
        except Exception as exc:
            logger.error("Failed to fetch FRED FX: %s", exc)
            if fx_cfg.get("required", False):
                failures += 1

    inflation_cfg = config.get("inflation", {})
    if inflation_cfg:
        try:
            inflation_df = _build_inflation(inflation_cfg, date_range, settings)
            output_path = _resolve_path(settings, inflation_cfg["output"])
            write_csv(inflation_df, output_path)
            logger.info("Saved historical inflation: %s", output_path)
        except Exception as exc:
            logger.error("Failed to build historical inflation: %s", exc)
            failures += 1

    reserves_cfg = config.get("reserves", {})
    if reserves_cfg:
        try:
            reserves_df = _build_reserves(reserves_cfg, date_range, settings)
            output_path = _resolve_path(settings, reserves_cfg["output"])
            write_csv(reserves_df, output_path)
            logger.info("Saved historical reserves: %s", output_path)
        except Exception as exc:
            logger.error("Failed to build historical reserves: %s", exc)
            failures += 1

    awcmr_cfg = config.get("awcmr", {})
    if awcmr_cfg:
        path = _resolve_path(settings, awcmr_cfg["path"])
        if path.exists():
            logger.info("AWCMR source present: %s", path)
        else:
            logger.warning("AWCMR source missing: %s", path)

    doc_cfg = config.get("documentation", {})
    if doc_cfg:
        try:
            _write_documentation(doc_cfg, settings)
            logger.info("Saved historical documentation: %s", doc_cfg.get("output"))
        except Exception as exc:
            logger.error("Failed to write documentation: %s", exc)
            failures += 1

    return 1 if failures else 0
