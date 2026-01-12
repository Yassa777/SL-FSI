"""Source ingestion for SL-FSI pipelines."""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, Iterable, Mapping, Optional

import pandas as pd
import logging

from slfsi.config.settings import Settings
from slfsi.etl.clean import coerce_numeric, ensure_datetime


@dataclass(frozen=True)
class SourceSpec:
    """Specification for a single input source.

    Economic intent:
        Centralizing file metadata ensures that data lineage remains explicit,
        which is essential for reproducibility in financial stress analysis.

    Attributes:
        name: Unique source name.
        path: Relative path to the source file.
        date_col: Date column name in the raw file.
        rename: Mapping of raw column names to canonical names.
        rename_contains: Mapping of substring matches to canonical names.
        keep_columns: Optional list of columns to keep after renaming.
        frequency: Declared frequency (daily, weekly, monthly).
        optional: If True, missing files are skipped with a warning.
    """

    name: str
    path: Path
    date_col: str = "date"
    rename: Mapping[str, str] = field(default_factory=dict)
    rename_contains: Mapping[str, str] = field(default_factory=dict)
    keep_columns: Optional[Iterable[str]] = None
    frequency: str = "daily"
    optional: bool = True


def _apply_rename_contains(df: pd.DataFrame, rename_contains: Mapping[str, str]) -> pd.DataFrame:
    """Rename columns using substring matches.

    Economic intent:
        Some data providers rename columns across releases. Substring-based
        mapping preserves continuity of economic series without manual edits.

    Args:
        df: Input dataframe.
        rename_contains: Mapping of substring to target column name.

    Returns:
        Dataframe with columns renamed where matches occur.
    """
    df = df.copy()
    if not rename_contains:
        return df

    rename_map: Dict[str, str] = {}
    for col in df.columns:
        for needle, target in rename_contains.items():
            if needle.lower() in col.lower() and target not in df.columns:
                rename_map[col] = target
                break

    if rename_map:
        df = df.rename(columns=rename_map)
    return df


def load_source(spec: SourceSpec, settings: Settings) -> Optional[pd.DataFrame]:
    """Load a single CSV source into a standardized dataframe.

    Economic intent:
        Standardizing column names and date parsing ensures that downstream
        joins reflect true economic relationships rather than file quirks.

    Args:
        spec: Source specification.
        settings: Repository settings for path resolution.

    Returns:
        DataFrame or None if the source is missing and optional.
    """
    logger = logging.getLogger(__name__)
    path = (settings.repo_root / spec.path).resolve()
    if not path.exists():
        if spec.optional:
            logger.warning("Source missing (optional): %s", path)
            return None
        raise FileNotFoundError(f"Required source missing: {path}")

    df = pd.read_csv(path)
    df = ensure_datetime(df, spec.date_col)
    df = df.rename(columns=dict(spec.rename))
    df = _apply_rename_contains(df, spec.rename_contains)

    if spec.keep_columns:
        keep = [spec.date_col] + [c for c in spec.keep_columns if c in df.columns]
        df = df[keep]

    numeric_cols = [c for c in df.columns if c != spec.date_col]
    df = coerce_numeric(df, numeric_cols)
    return df


def _spec_from_config(name: str, payload: Mapping[str, Any]) -> SourceSpec:
    """Build a source specification from config payload.

    Economic intent:
        A consistent spec ensures each data source is interpreted in the
        same way across runs, protecting reproducibility of stress signals.

    Args:
        name: Source key in the config.
        payload: Source configuration mapping.

    Returns:
        SourceSpec instance.
    """
    return SourceSpec(
        name=name,
        path=Path(payload["path"]),
        date_col=payload.get("date_col", "date"),
        rename=payload.get("rename", {}),
        rename_contains=payload.get("rename_contains", {}),
        keep_columns=payload.get("keep_columns"),
        frequency=payload.get("frequency", "daily"),
        optional=payload.get("optional", True),
    )


def load_sources(config: Mapping[str, Any], settings: Settings) -> Dict[str, pd.DataFrame]:
    """Load all sources defined in the config.

    Economic intent:
        A single loading pass ensures all series are aligned to the same
        canonical naming, enabling consistent stress metrics later.

    Args:
        config: Parsed data_sources configuration.
        settings: Repository settings for path resolution.

    Returns:
        Dictionary of source name to dataframe.
    """
    logger = logging.getLogger(__name__)
    sources: Dict[str, pd.DataFrame] = {}
    for name, payload in config.get("sources", {}).items():
        spec = _spec_from_config(name, payload)
        df = load_source(spec, settings)
        if df is not None:
            sources[name] = df
            logger.info("Loaded source: %s (%s rows)", name, len(df))
    return sources
