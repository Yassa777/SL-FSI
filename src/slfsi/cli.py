"""Command-line interface for SL-FSI pipelines."""

from __future__ import annotations

import argparse
import logging
from typing import Sequence

from slfsi import __version__
from slfsi.config.logging import setup_logging
from slfsi.config.settings import Settings
from slfsi.pipelines import analyze as analyze_run
from slfsi.pipelines import build_panel as build_panel_run
from slfsi.pipelines import download_external as download_external_run
from slfsi.pipelines import fetch_historical as fetch_historical_run
from slfsi.pipelines import leading_indicators as leading_indicators_run
from slfsi.pipelines import mercado as mercado_run
from slfsi.pipelines import combine as combine_run
from slfsi.pipelines import theory as theory_run
from slfsi.pipelines import train_hmm as train_hmm_run
from slfsi.pipelines import validate as validate_run


def build_parser() -> argparse.ArgumentParser:
    """Build the CLI argument parser."""
    parser = argparse.ArgumentParser(prog="slfsi", description="SL-FSI pipeline CLI")
    parser.add_argument("--log-level", default="INFO", help="Logging level (e.g., INFO, DEBUG)")

    subparsers = parser.add_subparsers(dest="command", required=True)

    subparsers.add_parser("version", help="Show package version")
    subparsers.add_parser("show-config", help="Print resolved default paths")

    build_panel_parser = subparsers.add_parser("build-panel", help="Build daily/monthly panels")
    build_panel_parser.add_argument("--config", help="Path to a YAML/JSON config file")

    download_parser = subparsers.add_parser(
        "download-external", help="Download external market and policy data"
    )
    download_parser.add_argument("--config", help="Path to a YAML/JSON config file")

    fetch_parser = subparsers.add_parser(
        "fetch-historical", help="Fetch historical macro data sources"
    )
    fetch_parser.add_argument("--config", help="Path to a YAML/JSON config file")

    train_hmm_parser = subparsers.add_parser("train-hmm", help="Train HMM models")
    train_hmm_parser.add_argument("--config", help="Path to a YAML/JSON config file")

    validate_parser = subparsers.add_parser("validate", help="Run validation workflows")
    validate_parser.add_argument("--config", help="Path to a YAML/JSON config file")

    indicators_parser = subparsers.add_parser(
        "leading-indicators", help="Compute leading indicators"
    )
    indicators_parser.add_argument("--config", help="Path to a YAML/JSON config file")

    mercado_parser = subparsers.add_parser("mercado", help="Compute Mercado-Park FSI")
    mercado_parser.add_argument("--config", help="Path to a YAML/JSON config file")

    combine_parser = subparsers.add_parser("combine", help="Combine FSI and HMM outputs")
    combine_parser.add_argument("--config", help="Path to a YAML/JSON config file")

    theory_parser = subparsers.add_parser(
        "theory", help="Run theory-based regime classification"
    )
    theory_parser.add_argument("--config", help="Path to a YAML/JSON config file")

    analyze_parser = subparsers.add_parser(
        "analyze", help="Run analysis utilities (comparison, overlap, transitions)"
    )
    analyze_parser.add_argument("--config", help="Path to a YAML/JSON config file")

    return parser


def main(argv: Sequence[str] | None = None) -> int:
    """Run the SL-FSI CLI.

    Returns:
        Process exit code (0 for success).
    """
    parser = build_parser()
    args = parser.parse_args(argv)

    setup_logging(level=args.log_level)
    logger = logging.getLogger(__name__)

    if args.command == "version":
        logger.info("slfsi %s", __version__)
        return 0

    if args.command == "show-config":
        settings = Settings.default()
        logger.info("repo_root=%s", settings.repo_root)
        logger.info("data_dir=%s", settings.data_dir)
        logger.info("processed_dir=%s", settings.processed_dir)
        logger.info("external_dir=%s", settings.external_dir)
        logger.info("merged_dir=%s", settings.merged_dir)
        logger.info("outputs_dir=%s", settings.outputs_dir)
        logger.info("figures_dir=%s", settings.figures_dir)
        logger.info("configs_dir=%s", settings.configs_dir)
        return 0

    if args.command == "build-panel":
        return build_panel_run(config_path=args.config)

    if args.command == "download-external":
        return download_external_run(config_path=args.config)

    if args.command == "fetch-historical":
        return fetch_historical_run(config_path=args.config)

    if args.command == "train-hmm":
        return train_hmm_run(config_path=args.config)

    if args.command == "validate":
        return validate_run(config_path=args.config)

    if args.command == "leading-indicators":
        return leading_indicators_run(config_path=args.config)

    if args.command == "mercado":
        return mercado_run(config_path=args.config)

    if args.command == "combine":
        return combine_run(config_path=args.config)

    if args.command == "theory":
        return theory_run(config_path=args.config)

    if args.command == "analyze":
        return analyze_run(config_path=args.config)

    logger.error("Unhandled command: %s", args.command)
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
