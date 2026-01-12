"""Canonical column names for SL-FSI datasets."""

from __future__ import annotations

from dataclasses import dataclass, fields
from pathlib import Path
from typing import Any, Iterable, Mapping, Tuple

from slfsi.config.loader import load_config


@dataclass(frozen=True)
class ColumnSchema:
    """Canonical column names used across SL-FSI pipelines."""

    date: str = "date"
    year_month: str = "year_month"
    period: str = "period"

    # Core market series
    usd_lkr: str = "usd_lkr"
    awcmr: str = "awcmr"
    aspi: str = "aspi"
    equity_turnover: str = "equity_turnover"
    market_cap: str = "market_cap"
    sl20_index: str = "sl20_index"
    gold_lkr: str = "gold_lkr"
    gold_usd: str = "gold_usd"
    tbill_primary: str = "tbill_primary"
    tbill_secondary: str = "tbill_secondary"
    tbond_yield: str = "tbond_yield"
    isb_yield: str = "isb_yield"
    us_10y_yield: str = "us_10y_yield"

    # Policy and macro series
    sdfr: str = "sdfr"
    slfr: str = "slfr"
    opr: str = "opr"
    policy_ceiling: str = "policy_ceiling"
    gross_reserves_usd_m: str = "gross_reserves_usd_m"
    net_usable_reserves_usd_m: str = "net_usable_reserves_usd_m"
    ncpi_yoy_pct: str = "ncpi_yoy_pct"
    reer_index: str = "reer_index"
    tourism_earnings_usd_m: str = "tourism_earnings_usd_m"
    remittances_usd_m: str = "remittances_usd_m"

    # Derived daily features
    r_fx: str = "r_fx"
    vol_fx_20d: str = "vol_fx_20d"
    r_eq: str = "r_eq"
    vol_eq_20d: str = "vol_eq_20d"
    r_eq_real: str = "r_eq_real"
    implied_fx: str = "implied_fx"
    gold_premium_pct: str = "gold_premium_pct"
    reserve_slope_3m: str = "reserve_slope_3m"
    import_cover_months: str = "import_cover_months"
    net_import_cover_months: str = "net_import_cover_months"
    interbank_spread: str = "interbank_spread"
    real_policy_rate: str = "real_policy_rate"
    yield_curve_slope: str = "yield_curve_slope"
    turnover_ratio: str = "turnover_ratio"
    embi_spread_approx: str = "embi_spread_approx"

    # HMM / regime outputs
    regime: str = "regime"
    regime_label: str = "regime_label"
    regime_realtime: str = "regime_realtime"
    p_calm: str = "p_calm"
    p_stress: str = "p_stress"
    p_crisis: str = "p_crisis"
    confidence: str = "confidence"

    # Cross-country schema
    country: str = "country"
    inflation_yoy: str = "inflation_yoy"
    reserves_usd_m: str = "reserves_usd_m"
    policy_rate: str = "policy_rate"
    kibor: str = "kibor"
    interbank_rate: str = "interbank_rate"

    @classmethod
    def from_config(cls, config: Mapping[str, Any]) -> "ColumnSchema":
        """Build a schema from a config mapping.

        Economic intent:
            Centralizing canonical names in config prevents silent drift in
            series definitions across ETL, feature, and validation stages.

        Args:
            config: Mapping of schema field names to column names.

        Returns:
            ColumnSchema populated with config overrides.
        """
        defaults = cls()
        values: dict[str, Any] = {}
        for field in fields(cls):
            name = field.name
            override = config.get(name) if config else None
            values[name] = override if override is not None else getattr(defaults, name)
        return cls(**values)


@dataclass(frozen=True)
class ColumnGroups:
    """Column groupings to keep schema usage consistent."""

    market_daily: Tuple[str, ...] = (
        "usd_lkr",
        "awcmr",
        "aspi",
        "equity_turnover",
        "market_cap",
        "sl20_index",
        "gold_lkr",
        "gold_usd",
        "tbill_primary",
        "tbill_secondary",
        "tbond_yield",
        "isb_yield",
        "us_10y_yield",
    )
    macro_monthly: Tuple[str, ...] = (
        "gross_reserves_usd_m",
        "ncpi_yoy_pct",
        "reer_index",
        "tourism_earnings_usd_m",
        "remittances_usd_m",
        "policy_ceiling",
        "sdfr",
        "slfr",
        "opr",
    )
    derived_daily: Tuple[str, ...] = (
        "r_fx",
        "vol_fx_20d",
        "r_eq",
        "vol_eq_20d",
        "r_eq_real",
        "implied_fx",
        "gold_premium_pct",
        "reserve_slope_3m",
        "import_cover_months",
        "net_usable_reserves_usd_m",
        "net_import_cover_months",
        "interbank_spread",
        "real_policy_rate",
        "yield_curve_slope",
        "turnover_ratio",
        "embi_spread_approx",
    )
    hmm_outputs: Tuple[str, ...] = (
        "regime",
        "regime_label",
        "regime_realtime",
        "p_calm",
        "p_stress",
        "p_crisis",
        "confidence",
    )
    cross_country: Tuple[str, ...] = (
        "country",
        "inflation_yoy",
        "reserves_usd_m",
        "policy_rate",
        "real_policy_rate",
        "kibor",
        "interbank_rate",
    )

    @classmethod
    def from_config(cls, config: Mapping[str, Iterable[str]]) -> "ColumnGroups":
        """Build column groups from config mappings.

        Economic intent:
            Consistent groupings ensure downstream models draw from the
            same economic categories when computing stress metrics.

        Args:
            config: Mapping of group names to column lists.

        Returns:
            ColumnGroups populated with config overrides.
        """
        defaults = cls()
        values: dict[str, Tuple[str, ...]] = {}
        for field in fields(cls):
            name = field.name
            override = config.get(name) if config else None
            if override is None:
                values[name] = getattr(defaults, name)
            else:
                values[name] = tuple(override)
        return cls(**values)


def load_schema(path: Path) -> tuple[ColumnSchema, ColumnGroups]:
    """Load column schema and groups from a YAML/JSON config.

    Economic intent:
        Loading schema definitions from config avoids hardcoded column names
        and keeps series definitions auditable for economic analysis.

    Args:
        path: Path to the schema config file.

    Returns:
        Tuple of (ColumnSchema, ColumnGroups).
    """
    if not path.exists():
        return ColumnSchema(), ColumnGroups()

    config = load_config(path)
    columns_cfg = config.get("columns", {})
    groups_cfg = config.get("groups", {})
    return ColumnSchema.from_config(columns_cfg), ColumnGroups.from_config(groups_cfg)
