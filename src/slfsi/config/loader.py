"""Load configuration files for SL-FSI."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import yaml


def load_config(path: Path) -> dict[str, Any]:
    """Load a JSON or YAML configuration file.

    Args:
        path: Path to a YAML or JSON config file.

    Returns:
        Parsed configuration as a dictionary.
    """
    if not path.exists():
        raise FileNotFoundError(f"Config file not found: {path}")

    if path.suffix.lower() in {".yml", ".yaml"}:
        with path.open("r", encoding="utf-8") as handle:
            data = yaml.safe_load(handle) or {}
        if not isinstance(data, dict):
            raise ValueError(f"YAML config must be a mapping: {path}")
        return data

    if path.suffix.lower() == ".json":
        with path.open("r", encoding="utf-8") as handle:
            data = json.load(handle)
        if not isinstance(data, dict):
            raise ValueError(f"JSON config must be a mapping: {path}")
        return data

    raise ValueError(f"Unsupported config format: {path}")
