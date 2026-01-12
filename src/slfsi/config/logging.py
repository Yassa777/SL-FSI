"""Logging configuration for SL-FSI pipelines."""

from __future__ import annotations

import logging
import logging.config
from pathlib import Path
from typing import Any

from slfsi.config.loader import load_config

_DEFAULT_FORMAT = "%(asctime)s | %(levelname)s | %(name)s | %(message)s"


def _default_logging_config(level: str | int) -> dict[str, Any]:
    return {
        "version": 1,
        "disable_existing_loggers": False,
        "formatters": {
            "standard": {"format": _DEFAULT_FORMAT},
        },
        "handlers": {
            "console": {
                "class": "logging.StreamHandler",
                "formatter": "standard",
                "level": level,
            },
        },
        "root": {"handlers": ["console"], "level": level},
    }


def setup_logging(config_path: Path | None = None, level: str | int = "INFO") -> None:
    """Configure application logging.

    Args:
        config_path: Optional YAML/JSON logging config file.
        level: Default logging level when no config file is supplied.
    """
    if config_path:
        config = load_config(config_path)
        logging.config.dictConfig(config)
        return

    logging.config.dictConfig(_default_logging_config(level))
